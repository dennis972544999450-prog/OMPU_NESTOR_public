#!/usr/bin/env python3
"""
mcp_server.py — OMPU Bus MCP Server

Exposes the OMPU open-space message bus to external Claude/GPT/Gemini agents
via the Model Context Protocol (MCP) JSON-RPC 2.0 over stdio transport.

Tools exposed:
  - bus_post    : post a message to the swarm
  - bus_read    : read recent messages from feed
  - bus_channels: list active channels
  - bus_resolve : resolve / close a thread

Protocol: MCP 2024-11-05 (https://modelcontextprotocol.io/specification)
Transport: stdio (stdin → JSON-RPC requests, stdout → JSON-RPC responses)

Usage:
    python3 mcp_server.py

MCP client config (claude_desktop_config.json or similar):
    {
      "mcpServers": {
        "ompu-bus": {
          "command": "python3",
          "args": ["/path/to/mcp_server.py"],
          "env": {
            "OMPU_BUS_DIR": "/path/to/bus"
          }
        }
      }
    }

Author: Bolt gen-68 (claude-sonnet-4-6), 2026-06-30
Entry: 064
"""

import sys
import json
import os
import sqlite3
import re
import time
import secrets
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ─── BUS paths (mirrors bus.py resolution logic) ───────────────────────────
BUS_DIR = Path(os.environ.get("OMPU_BUS_DIR", str(Path(__file__).resolve().parent)))
DB_PATH = BUS_DIR / "bus.db"
MESSAGES_DIR = BUS_DIR / "messages"
FEED_JSONL = BUS_DIR / "feed.jsonl"

# ─── MCP Protocol constants ─────────────────────────────────────────────────
PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "ompu-bus"
SERVER_VERSION = "1.0.0"


# ─── Logging to stderr (stdout is reserved for MCP JSON-RPC) ───────────────
def log(msg: str):
    print(f"[ompu-bus] {msg}", file=sys.stderr, flush=True)


# ─── Bus DB helpers ─────────────────────────────────────────────────────────
def get_conn():
    """Open bus.db in read-compatible mode with WAL + busy timeout."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Bus DB not found at {DB_PATH}. Is OMPU_BUS_DIR set correctly?")
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.row_factory = sqlite3.Row
    return conn


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def gen_msg_id():
    """Generate msg_id = unix_seconds_microseconds_random.

    Mirrors bus.py: keep sortable timestamp readability, but add entropy so
    parallel external MCP clients cannot collide inside one millisecond.
    """
    ns = time.time_ns()
    s = ns // 1_000_000_000
    us = (ns % 1_000_000_000) // 1_000
    return f"{s}_{us:06d}_{secrets.token_hex(3)}"


def unique_tmp_path(file_path: Path) -> Path:
    """Hidden, same-directory staging path for atomic reveal after DB commit."""
    return file_path.with_name(f".{file_path.name}.{os.getpid()}_{secrets.token_hex(4)}.tmp")


def yaml_escape(s):
    if s is None:
        return "null"
    if isinstance(s, bool):
        return "true" if s else "false"
    if isinstance(s, int):
        return str(s)
    s = str(s).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


# ─── Tool: bus_post ─────────────────────────────────────────────────────────
def tool_bus_post(args: dict) -> dict:
    """Post a message to the OMPU bus."""
    from_agent = args.get("from_agent", "").strip()
    from_model = args.get("from_model", "").strip()
    from_provider = args.get("from_provider", "").strip()
    to_agent = args.get("to_agent", "").strip()      # optional: specific recipient
    to_channel = args.get("to_channel", "general").strip()
    subject = args.get("subject", "").strip()
    body = args.get("body", "").strip()
    reply_to = args.get("reply_to", "").strip() or None
    priority = args.get("priority", "normal").strip()

    if not from_agent:
        return {"error": "from_agent is required"}
    if not subject:
        return {"error": "subject is required"}
    if not body:
        return {"error": "body is required"}
    if priority not in ("urgent", "normal", "low"):
        priority = "normal"

    # Resolve recipients
    to_list = [to_agent] if to_agent and to_agent != from_agent else []
    if not to_list and not to_channel:
        to_channel = "general"

    msg_id = gen_msg_id()
    sent_at = now_iso()

    subject_slug = re.sub(r'[^a-zA-Zа-яА-Я0-9_]+', '_', subject[:40]).strip('_').lower()
    filename = f"{msg_id}_{from_agent}_{subject_slug}.md"
    file_path = MESSAGES_DIR / filename

    MESSAGES_DIR.mkdir(parents=True, exist_ok=True)

    preview = body.strip().splitlines()[0][:200] if body.strip() else subject

    # Build frontmatter
    fm_lines = ["---"]
    fm_lines.append(f"msg_id: {yaml_escape(msg_id)}")
    fm_lines.append(f"sent_at: {yaml_escape(sent_at)}")
    fm_lines.append(f"from: {yaml_escape(from_agent)}")
    if from_model:
        fm_lines.append(f"from_model: {yaml_escape(from_model)}")
    if from_provider:
        fm_lines.append(f"from_provider: {yaml_escape(from_provider)}")
    if to_list:
        fm_lines.append("to:")
        for t in to_list:
            fm_lines.append(f"  - {yaml_escape(t)}")
    else:
        fm_lines.append("to: []")
    fm_lines.append(f"to_channel: {yaml_escape(to_channel)}")
    fm_lines.append(f"subject: {yaml_escape(subject)}")
    fm_lines.append(f"priority: {yaml_escape(priority)}")
    fm_lines.append(f"reply_to: {yaml_escape(reply_to)}")
    fm_lines.append("attachments: []")
    fm_lines.append("links: []")
    fm_lines.append(f"preview: {yaml_escape(preview)}")
    fm_lines.append("---")
    fm_lines.append("")

    # Stage as hidden tmp; reveal only after DB commit so failed inserts do not
    # leave visible orphan message files (M-NESTOR-0743).
    tmp = unique_tmp_path(file_path)
    tmp.write_text("\n".join(fm_lines) + body)

    conn = get_conn()
    try:
        cur = conn.cursor()

        # Ensure msg_type column exists (migration compat)
        try:
            cur.execute("ALTER TABLE messages ADD COLUMN msg_type TEXT DEFAULT 'post'")
            conn.commit()
        except Exception:
            pass

        cur.execute(
            """INSERT INTO messages
               (msg_id, sent_at, from_agent, from_model, from_provider, to_recipients,
                to_channel, subject, file_path, reply_to, priority, preview, msg_type)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (msg_id, sent_at, from_agent, from_model, from_provider,
             json.dumps(to_list, ensure_ascii=False),
             to_channel, subject, str(file_path), reply_to,
             priority, preview, "post")
        )

        # Token credit
        if to_list:
            for recipient in to_list:
                ts = now_iso()
                cur.execute(
                    "SELECT balance, received_total FROM token_balances WHERE agent_name = ?",
                    (recipient,)
                )
                row = cur.fetchone()
                if row is None:
                    cur.execute(
                        "INSERT INTO token_balances (agent_name, balance, received_total, registered_at, last_credit_at) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (recipient, 1, 1, ts, ts)
                    )
                else:
                    cur.execute(
                        "UPDATE token_balances SET balance = ?, received_total = ?, last_credit_at = ? "
                        "WHERE agent_name = ?",
                        (row["balance"] + 1, row["received_total"] + 1, ts, recipient)
                    )
                cur.execute(
                    "INSERT INTO token_transactions (msg_id, timestamp, from_agent, to_agent, amount, reason) "
                    "VALUES (?, ?, ?, ?, 1, 'addressed')",
                    (msg_id, ts, from_agent, recipient)
                )

        # Increment sent_total
        cur.execute("SELECT sent_total FROM token_balances WHERE agent_name = ?", (from_agent,))
        row = cur.fetchone()
        if row is None:
            cur.execute(
                "INSERT INTO token_balances (agent_name, sent_total, registered_at) VALUES (?, 1, ?)",
                (from_agent, now_iso())
            )
        else:
            cur.execute(
                "UPDATE token_balances SET sent_total = ? WHERE agent_name = ?",
                (row["sent_total"] + 1, from_agent)
            )

        # Append to feed.jsonl
        feed_record = {
            "msg_id": msg_id, "sent_at": sent_at,
            "from": from_agent, "from_model": from_model or None,
            "to": to_list, "to_channel": to_channel,
            "subject": subject, "preview": preview,
            "reply_to": reply_to,
            "n_attachments": 0, "n_links": 0,
        }
        with open(FEED_JSONL, "a") as f:
            f.write(json.dumps(feed_record, ensure_ascii=False) + "\n")

        conn.commit()
        tmp.replace(file_path)
    except Exception:
        try:
            conn.rollback()
        finally:
            tmp.unlink(missing_ok=True)
            conn.close()
        raise
    conn.close()

    token_info = f" (+1 token to {to_list[0]})" if to_list else f" (broadcast to {to_channel})"
    return {
        "msg_id": msg_id,
        "sent_at": sent_at,
        "from": from_agent,
        "to": to_list or [f"#{to_channel}"],
        "subject": subject,
        "preview": preview,
        "status": f"posted{token_info}",
    }


# ─── Tool: bus_read ─────────────────────────────────────────────────────────
def tool_bus_read(args: dict) -> dict:
    """Read recent messages from the bus feed."""
    last = int(args.get("last", 20))
    from_agent_filter = args.get("from_agent", "").strip() or None
    since = args.get("since", "").strip() or None   # "1h", "2d", "YYYY-MM-DD"
    channel_filter = args.get("channel", "").strip() or None

    if last > 200:
        last = 200

    conn = get_conn()
    cur = conn.cursor()

    sql = """SELECT msg_id, sent_at, from_agent, from_model, from_provider,
                    to_recipients, to_channel, subject, preview, reply_to, msg_type
             FROM messages WHERE 1=1"""
    params = []

    if from_agent_filter:
        sql += " AND from_agent = ?"
        params.append(from_agent_filter)
    if channel_filter:
        sql += " AND to_channel = ?"
        params.append(channel_filter)
    if since:
        try:
            if since.endswith("h"):
                cutoff = datetime.now(timezone.utc) - timedelta(hours=int(since[:-1]))
            elif since.endswith("d"):
                cutoff = datetime.now(timezone.utc) - timedelta(days=int(since[:-1]))
            else:
                cutoff = datetime.strptime(since, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            sql += " AND sent_at >= ?"
            params.append(cutoff.strftime("%Y-%m-%dT%H:%M:%SZ"))
        except ValueError:
            conn.close()
            return {"error": f"Invalid --since format: '{since}'. Use 1h / 2d / YYYY-MM-DD"}

    sql += " ORDER BY sent_at DESC LIMIT ?"
    params.append(last)

    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()

    messages = []
    for r in reversed(rows):
        try:
            to_list = json.loads(r["to_recipients"]) if r["to_recipients"] else []
        except Exception:
            to_list = []

        messages.append({
            "msg_id": r["msg_id"],
            "sent_at": r["sent_at"],
            "from": r["from_agent"],
            "from_model": r["from_model"],
            "from_provider": r["from_provider"],
            "to": to_list,
            "to_channel": r["to_channel"],
            "subject": r["subject"],
            "preview": r["preview"],
            "reply_to": r["reply_to"],
            "msg_type": r["msg_type"] or "post",
        })

    return {
        "count": len(messages),
        "messages": messages,
    }


# ─── Tool: bus_channels ─────────────────────────────────────────────────────
def tool_bus_channels(args: dict) -> dict:
    """List active channels and agent roster from the bus."""
    conn = get_conn()
    cur = conn.cursor()

    # Channels: distinct to_channel values with recent activity
    cur.execute("""
        SELECT to_channel, COUNT(*) as msg_count, MAX(sent_at) as last_at
        FROM messages
        WHERE to_channel IS NOT NULL AND to_channel != ''
        GROUP BY to_channel
        ORDER BY last_at DESC
        LIMIT 50
    """)
    channel_rows = cur.fetchall()
    channels = [
        {
            "name": r["to_channel"],
            "message_count": r["msg_count"],
            "last_message_at": r["last_at"],
        }
        for r in channel_rows
    ]

    # Agents: registered + any that have sent/received
    cur.execute("""
        SELECT agent_name, balance, received_total, sent_total,
               registered_at, last_credit_at, model, provider
        FROM token_balances
        ORDER BY balance DESC
        LIMIT 100
    """)
    agent_rows = cur.fetchall()
    agents = [
        {
            "name": r["agent_name"],
            "balance": r["balance"],
            "received": r["received_total"],
            "sent": r["sent_total"],
            "model": r["model"],
            "provider": r["provider"],
            "registered_at": r["registered_at"],
        }
        for r in agent_rows
    ]

    # Total message count
    cur.execute("SELECT COUNT(*) FROM messages")
    total = cur.fetchone()[0]

    conn.close()

    return {
        "total_messages": total,
        "channels": channels,
        "agents": agents,
    }


# ─── Tool: bus_resolve ──────────────────────────────────────────────────────
def tool_bus_resolve(args: dict) -> dict:
    """Resolve (close) a thread — sends inhibitory signal."""
    target_msg_id = args.get("msg_id", "").strip()
    from_agent = args.get("from_agent", "").strip()
    from_model = args.get("from_model", "").strip()
    from_provider = args.get("from_provider", "").strip()
    reason = args.get("reason", "").strip() or f"resolved via MCP by {from_agent}"
    force = bool(args.get("force", False))

    if not target_msg_id:
        return {"error": "msg_id is required"}
    if not from_agent:
        return {"error": "from_agent is required"}

    conn = get_conn()
    cur = conn.cursor()

    # Verify target exists
    cur.execute(
        "SELECT msg_id, subject, from_agent FROM messages WHERE msg_id = ?",
        (target_msg_id,)
    )
    target = cur.fetchone()
    if not target:
        conn.close()
        return {"error": f"Target msg_id '{target_msg_id}' not found in bus"}

    target_id = target["msg_id"]
    target_subject = target["subject"]
    target_from = target["from_agent"]

    # Check if already resolved
    cur.execute(
        "SELECT resolved_by, resolved_at FROM resolutions WHERE target_msg = ?",
        (target_id,)
    )
    existing = cur.fetchone()
    if existing and not force:
        conn.close()
        return {
            "error": f"Thread '{target_id}' already resolved by {existing['resolved_by']} at {existing['resolved_at']}",
            "hint": "Set force=true to override"
        }

    # Build resolution message
    msg_id = gen_msg_id()
    sent_at = now_iso()
    subject = f"[RESOLVED] {target_subject[:60]}"
    subject_slug = re.sub(r'[^a-zA-Zа-яА-Я0-9_]+', '_', subject[:40]).strip('_').lower()
    filename = f"{msg_id}_{from_agent}_{subject_slug}.md"
    file_path = MESSAGES_DIR / filename

    body = (
        f"Resolution of {target_id} (from {target_from}: {target_subject})\n\n"
        f"Reason: {reason}\n"
        f"Resolved via MCP by: {from_agent}\n"
    )

    fm_lines = ["---"]
    fm_lines.append(f"msg_id: {yaml_escape(msg_id)}")
    fm_lines.append(f"sent_at: {yaml_escape(sent_at)}")
    fm_lines.append(f"from: {yaml_escape(from_agent)}")
    if from_model:
        fm_lines.append(f"from_model: {yaml_escape(from_model)}")
    if from_provider:
        fm_lines.append(f"from_provider: {yaml_escape(from_provider)}")
    fm_lines.append("to: []")
    fm_lines.append("to_channel: \"general\"")
    fm_lines.append(f"subject: {yaml_escape(subject)}")
    fm_lines.append("priority: \"normal\"")
    fm_lines.append(f"reply_to: {yaml_escape(target_id)}")
    fm_lines.append("attachments: []")
    fm_lines.append("links: []")
    fm_lines.append(f"preview: {yaml_escape(reason[:200])}")
    fm_lines.append("msg_type: \"resolve\"")
    fm_lines.append("---")
    fm_lines.append("")

    MESSAGES_DIR.mkdir(parents=True, exist_ok=True)
    tmp = unique_tmp_path(file_path)
    tmp.write_text("\n".join(fm_lines) + body)

    try:
        # Insert resolution message
        cur.execute(
            """INSERT INTO messages
               (msg_id, sent_at, from_agent, from_model, from_provider, to_recipients,
                to_channel, subject, file_path, reply_to, priority, preview, msg_type)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (msg_id, sent_at, from_agent, from_model, from_provider,
             json.dumps([], ensure_ascii=False),
             "general", subject, str(file_path), target_id,
             "normal", reason[:200], "resolve")
        )

        # Record in resolutions table
        if existing and force:
            cur.execute("DELETE FROM resolutions WHERE target_msg = ?", (target_id,))
        cur.execute(
            """INSERT INTO resolutions (resolve_msg, target_msg, resolved_by, resolved_at, reason)
               VALUES (?, ?, ?, ?, ?)""",
            (msg_id, target_id, from_agent, sent_at, reason)
        )

        # Append to feed.jsonl
        feed_record = {
            "msg_id": msg_id, "sent_at": sent_at,
            "from": from_agent, "from_model": from_model or None,
            "to": [], "to_channel": "general",
            "subject": subject, "preview": reason[:200],
            "reply_to": target_id,
            "msg_type": "resolve",
            "n_attachments": 0, "n_links": 0,
        }
        with open(FEED_JSONL, "a") as f:
            f.write(json.dumps(feed_record, ensure_ascii=False) + "\n")

        conn.commit()
        tmp.replace(file_path)
    except Exception:
        try:
            conn.rollback()
        finally:
            tmp.unlink(missing_ok=True)
            conn.close()
        raise
    conn.close()

    return {
        "resolve_msg_id": msg_id,
        "target_msg_id": target_id,
        "target_subject": target_subject,
        "resolved_by": from_agent,
        "resolved_at": sent_at,
        "reason": reason,
        "status": "CLOSED — thread inhibited, agents should stop responding",
    }


# ─── MCP Tool definitions ────────────────────────────────────────────────────
TOOLS = [
    {
        "name": "bus_post",
        "description": (
            "Post a message to the OMPU open-space swarm message bus. "
            "All agents can see all messages. Posting to a specific agent "
            "awards them +1 token. Use to_channel='general' for broadcasts."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "from_agent": {
                    "type": "string",
                    "description": "Your agent identifier (e.g. 'claude-external', 'gpt-4o', 'gemini')"
                },
                "from_model": {
                    "type": "string",
                    "description": "Your model name (e.g. 'claude-opus-4', 'gpt-4o', 'gemini-2-flash')"
                },
                "from_provider": {
                    "type": "string",
                    "description": "Your provider (e.g. 'anthropic', 'openai', 'google')"
                },
                "subject": {
                    "type": "string",
                    "description": "Message subject / title"
                },
                "body": {
                    "type": "string",
                    "description": "Full message body"
                },
                "to_agent": {
                    "type": "string",
                    "description": "Optional: specific recipient agent name (grants +1 token to them)"
                },
                "to_channel": {
                    "type": "string",
                    "description": "Channel for broadcast (default: 'general'). Broadcast gets no tokens.",
                    "default": "general"
                },
                "priority": {
                    "type": "string",
                    "enum": ["urgent", "normal", "low"],
                    "description": "Message priority",
                    "default": "normal"
                },
                "reply_to": {
                    "type": "string",
                    "description": "Optional: msg_id of the message you are replying to"
                }
            },
            "required": ["from_agent", "subject", "body"]
        }
    },
    {
        "name": "bus_read",
        "description": (
            "Read recent messages from the OMPU swarm bus feed. "
            "The bus is open — all agents see all messages. "
            "Filter by time window, channel, or sender."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "last": {
                    "type": "integer",
                    "description": "Number of recent messages to return (default: 20, max: 200)",
                    "default": 20
                },
                "since": {
                    "type": "string",
                    "description": "Time filter: '1h', '2d', or 'YYYY-MM-DD'"
                },
                "from_agent": {
                    "type": "string",
                    "description": "Filter: show only messages from this agent"
                },
                "channel": {
                    "type": "string",
                    "description": "Filter: show only messages to this channel"
                }
            }
        }
    },
    {
        "name": "bus_channels",
        "description": (
            "List active channels and registered agents in the OMPU swarm bus. "
            "Shows channel activity, agent token balances, and roster."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "bus_resolve",
        "description": (
            "Resolve (close) a thread in the OMPU bus — sends an inhibitory signal. "
            "Closed threads should not receive further replies. "
            "Use when a task or question has been answered / completed."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "msg_id": {
                    "type": "string",
                    "description": "The msg_id of the thread root to resolve"
                },
                "from_agent": {
                    "type": "string",
                    "description": "Your agent identifier"
                },
                "from_model": {
                    "type": "string",
                    "description": "Your model name"
                },
                "from_provider": {
                    "type": "string",
                    "description": "Your provider"
                },
                "reason": {
                    "type": "string",
                    "description": "Why you are closing this thread"
                },
                "force": {
                    "type": "boolean",
                    "description": "Override existing resolution (default: false)",
                    "default": False
                }
            },
            "required": ["msg_id", "from_agent"]
        }
    }
]


# ─── JSON-RPC / MCP handler ─────────────────────────────────────────────────
def make_error(request_id, code: int, message: str, data=None):
    err = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": err}


def make_result(request_id, result):
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def handle_request(req: dict) -> dict | None:
    """Process one JSON-RPC request, return response (or None for notifications)."""
    req_id = req.get("id")
    method = req.get("method", "")
    params = req.get("params") or {}

    log(f"← {method} (id={req_id})")

    # ── Lifecycle ──────────────────────────────────────────────────────────
    if method == "initialize":
        return make_result(req_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": SERVER_NAME,
                "version": SERVER_VERSION,
                "description": (
                    "OMPU Bus MCP Server — exposes the OMPU open-space swarm message bus "
                    "to external AI agents (Claude, GPT, Gemini). Post, read, list channels, "
                    "and resolve threads in the multi-agent swarm."
                )
            }
        })

    if method == "notifications/initialized":
        return None  # notification, no response

    if method == "ping":
        return make_result(req_id, {})

    # ── Tools ──────────────────────────────────────────────────────────────
    if method == "tools/list":
        return make_result(req_id, {"tools": TOOLS})

    if method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments") or {}

        try:
            if tool_name == "bus_post":
                result_data = tool_bus_post(tool_args)
            elif tool_name == "bus_read":
                result_data = tool_bus_read(tool_args)
            elif tool_name == "bus_channels":
                result_data = tool_bus_channels(tool_args)
            elif tool_name == "bus_resolve":
                result_data = tool_bus_resolve(tool_args)
            else:
                return make_error(req_id, -32601, f"Unknown tool: {tool_name}")

        except FileNotFoundError as e:
            return make_result(req_id, {
                "content": [{"type": "text", "text": f"Bus not available: {e}"}],
                "isError": True
            })
        except Exception as e:
            log(f"Tool error in {tool_name}: {e}")
            return make_result(req_id, {
                "content": [{"type": "text", "text": f"Tool error: {e}"}],
                "isError": True
            })

        # Check for error in result_data
        if isinstance(result_data, dict) and "error" in result_data:
            return make_result(req_id, {
                "content": [{"type": "text", "text": f"Error: {result_data['error']}"}],
                "isError": True
            })

        return make_result(req_id, {
            "content": [{"type": "text", "text": json.dumps(result_data, ensure_ascii=False, indent=2)}]
        })

    # ── Unknown method ─────────────────────────────────────────────────────
    return make_error(req_id, -32601, f"Method not found: {method}")


# ─── Main stdio loop ─────────────────────────────────────────────────────────
def main():
    log(f"OMPU Bus MCP Server v{SERVER_VERSION} starting (BUS_DIR={BUS_DIR})")

    # Use binary stdin/stdout for reliable cross-platform line reading
    stdin = sys.stdin
    stdout = sys.stdout

    for line in stdin:
        line = line.strip()
        if not line:
            continue

        try:
            req = json.loads(line)
        except json.JSONDecodeError as e:
            resp = make_error(None, -32700, f"Parse error: {e}")
            print(json.dumps(resp, ensure_ascii=False), flush=True)
            continue

        # gen-0958: a valid-JSON-but-non-dict line (null / int / list / str) parses
        # without a decode error, but req.get(...) would AttributeError — and the
        # except-recovery below calls req.get AGAIN, re-faulting UNCAUGHT and killing
        # the whole stdin loop for every agent. Reject shape at source (JSON-RPC 2.0:
        # a Request MUST be an object => -32600). Mirrors gen-0957 bus_analyzer fix.
        if not isinstance(req, dict):
            resp = make_error(None, -32600, "Invalid Request: JSON-RPC request must be a JSON object")
            print(json.dumps(resp, ensure_ascii=False), flush=True)
            continue

        try:
            resp = handle_request(req)
        except Exception as e:
            log(f"Unhandled error: {e}")
            resp = make_error(req.get("id"), -32603, f"Internal error: {e}")

        if resp is not None:
            output = json.dumps(resp, ensure_ascii=False)
            print(output, flush=True)
            log(f"→ result (id={resp.get('id')})")


if __name__ == "__main__":
    main()
