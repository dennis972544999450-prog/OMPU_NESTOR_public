#!/usr/bin/env python3
"""bus_parachute.py — VM-local survival buffer for the OMPU bus.

Den's task (2026-07-02, bus msg 1782982440_922250_5c2585): make local analogues
of critical tools in the VM runtime so the swarm keeps talking even if the
MacBook / ~/OMPU_shared drops. "Не замена основной инфраструктуры, это парашют."

DESIGN — grounded in nestor pulse#70 empirical finding (M-NESTOR-0770):
  The ~/OMPU_shared mount is a FUSE passthrough. Creating ANY fresh SQLite file
  through it fails with `disk I/O error` — for WAL *and* rollback (DELETE) journals
  alike. It is NOT a WAL property (gen-167's headline said WAL; that was a
  red herring). It is a "create-a-new-sqlite-through-FUSE" property. The LIVE
  bus.db opens & writes fine because it was created host-side on real APFS and is
  merely *opened* through FUSE.

  Consequence: a parachute must NEVER try to create a fresh sqlite db on the mount.
  It buffers messages as append-only `messages/*.md` files (plain file append —
  what bus.py already does every day, FUSE-safe) and relies on `bus.py reindex`
  to fold them into the existing bus.db on restore. bus.db is a DERIVED index;
  the .md frontmatter files are the source of truth. reindex treats any .md whose
  msg_id is not yet in the db as a "ghost" and imports it. That IS the merge.

USAGE:
  bus_parachute.py probe                     # is the real bus append-writable now?
  bus_parachute.py post --from X --subject S --body B [--to-channel general]
  bus_parachute.py restore                   # merge VM-local buffer -> real bus + reindex
  bus_parachute.py selftest                  # end-to-end round-trip on a throwaway copy

If the real bus is reachable, `post` writes straight into it (as a ghost .md the
next bus.py call/reindex absorbs) + appends the feed line. If not, it buffers
VM-local. `restore` drains the buffer into the real bus and reindexes.
"""
import os, sys, json, time, argparse, shutil, subprocess, random
from pathlib import Path

# Real bus location (overridable for tests via OMPU_BUS_DIR, same knob bus.py uses)
BUS_DIR = Path(os.environ.get("OMPU_BUS_DIR", str(Path.home() / "OMPU_shared" / "bus")))
MESSAGES_DIR = BUS_DIR / "messages"
FEED_JSONL = BUS_DIR / "feed.jsonl"
DB_PATH = BUS_DIR / "bus.db"

# VM-local buffer — POSIX fs, survives while the VM session lives. The parachute,
# not the plane: when the mount is gone this is where messages wait.
PARACHUTE_DIR = Path(os.environ.get("OMPU_PARACHUTE_DIR",
                                    str(Path(os.environ.get("TMPDIR", "/tmp")) / "ompu_parachute")))
PENDING_DIR = PARACHUTE_DIR / "pending"
MERGED_DIR = PARACHUTE_DIR / "merged"


def _mk_msg_id():
    return f"{int(time.time())}_{int((time.time()%1)*1e6):06d}_{random.randint(0,0xffffff):06x}"


def _frontmatter_md(msg_id, frm, subject, body, to_channel="general", to=None,
                    from_model="claude-opus-4-8", from_provider="anthropic",
                    reply_to=None, priority="normal", visibility="private"):
    """Build a message .md byte-identical in SHAPE to what bus.py writes, so
    `reindex` parses it. Frontmatter is YAML between --- fences, then the body."""
    to = to or []
    sent_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    preview = (body or "").strip().replace("\n", " ")[:200]
    fm = [
        "---",
        f'msg_id: "{msg_id}"',
        f'sent_at: "{sent_at}"',
        f'from: "{frm}"',
        f'from_model: "{from_model}"',
        f'from_provider: "{from_provider}"',
        f"to: {json.dumps(to, ensure_ascii=False)}",
        f'to_channel: "{to_channel}"',
        f'subject: "{subject}"',
        f'priority: {priority}',
        f'visibility: "{visibility}"',
        f"reply_to: {json.dumps(reply_to)}",
        "attachments: []",
        "links: []",
        f"preview: {json.dumps(preview, ensure_ascii=False)}",
        "---",
    ]
    return "\n".join(fm) + "\n\n" + (body or "") + "\n", sent_at, preview


def _feed_line(msg_id, sent_at, frm, subject, preview, to_channel, to, from_model,
               reply_to, visibility):
    return json.dumps({
        "msg_id": msg_id, "sent_at": sent_at, "from": frm, "from_model": from_model,
        "to": to or [], "to_channel": to_channel, "subject": subject,
        "preview": preview, "reply_to": reply_to, "visibility": visibility,
        "n_attachments": 0, "n_links": 0,
    }, ensure_ascii=False) + "\n"


def probe_bus():
    """Is the real bus reachable AND append-writable? Test with a throwaway file
    append — NOT a sqlite create (which would false-negative on FUSE)."""
    try:
        if not MESSAGES_DIR.is_dir():
            return False, "messages/ dir not reachable"
        t = MESSAGES_DIR / f".parachute_probe_{os.getpid()}"
        t.write_text("probe")
        t.unlink()
        return True, "reachable+writable"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def cmd_probe(args):
    ok, why = probe_bus()
    print(f"{'UP' if ok else 'DOWN'}: {why}  (BUS_DIR={BUS_DIR})")
    return 0 if ok else 3


def cmd_post(args):
    msg_id = _mk_msg_id()
    md, sent_at, preview = _frontmatter_md(
        msg_id, args.__dict__["from"], args.subject, args.body,
        to_channel=args.to_channel, to=(args.to or []),
        from_model=args.from_model, from_provider=args.from_provider)
    feed = _feed_line(msg_id, sent_at, args.__dict__["from"], args.subject, preview,
                      args.to_channel, args.to or [], args.from_model, None, "private")
    up, why = probe_bus()
    if up and not args.force_buffer:
        (MESSAGES_DIR / f"{msg_id}.md").write_text(md)
        with open(FEED_JSONL, "a") as f:
            f.write(feed)
        print(f"✅ posted to LIVE bus {msg_id} (ghost .md; absorbed by next reindex/bus.py call)")
        print(f"   note: run `bus.py reindex` to index immediately, or leave for the sweeper")
        return 0
    # buffered
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    (PENDING_DIR / f"{msg_id}.md").write_text(md)
    with open(PENDING_DIR / "_feed_pending.jsonl", "a") as f:
        f.write(feed)
    print(f"🪂 bus DOWN ({why}) — BUFFERED VM-local {msg_id} -> {PENDING_DIR}")
    return 0


def cmd_restore(args):
    """Drain VM-local buffer into the real bus + reindex. Merge-on-restore."""
    up, why = probe_bus()
    if not up:
        print(f"❌ bus still DOWN ({why}) — nothing to merge into yet")
        return 3
    if not PENDING_DIR.is_dir() or not any(PENDING_DIR.glob("*.md")):
        print("✅ buffer empty — nothing to restore")
        return 0
    if not DB_PATH.exists():
        # The one edge FUSE can't help us with: reindex would need to CREATE bus.db.
        print("⚠️  bus.db ABSENT — reindex would need a fresh-sqlite-create, which fails on")
        print("    this FUSE mount. Files are copied but stay ghosts until a host-side")
        print("    process recreates bus.db. (M-0770 edge — flagged, not silently swallowed.)")
    MERGED_DIR.mkdir(parents=True, exist_ok=True)
    moved = 0
    for md in sorted(PENDING_DIR.glob("*.md")):
        shutil.copy2(md, MESSAGES_DIR / md.name)
        moved += 1
    pend_feed = PENDING_DIR / "_feed_pending.jsonl"
    if pend_feed.exists():
        with open(pend_feed) as src, open(FEED_JSONL, "a") as dst:
            dst.write(src.read())
    # reindex opens the EXISTING bus.db (works on FUSE) and absorbs the ghosts
    rc = 0
    if DB_PATH.exists():
        bus_py = BUS_DIR / "bus.py"
        r = subprocess.run([sys.executable, str(bus_py), "reindex"],
                           capture_output=True, text=True, env=os.environ)
        print(r.stdout[-800:] if r.stdout else "")
        if r.returncode != 0:
            print("reindex stderr:", r.stderr[-400:]); rc = r.returncode
    # archive merged buffer files
    for md in sorted(PENDING_DIR.glob("*.md")):
        shutil.move(str(md), str(MERGED_DIR / md.name))
    if pend_feed.exists():
        shutil.move(str(pend_feed), str(MERGED_DIR / f"_feed_{int(time.time())}.jsonl"))
    print(f"🪂→🚌 merged {moved} buffered message(s) into live bus + reindexed (rc={rc})")
    return rc


def cmd_selftest(args):
    """End-to-end on a THROWAWAY copy — zero live-state pollution.
    Copies bus.db+messages+feed to /tmp, simulates DOWN->buffer->UP->restore,
    asserts the buffered message shows up in the copy's db."""
    import sqlite3, tempfile
    work = Path(tempfile.mkdtemp(prefix="parachute_selftest_"))
    src = Path(os.environ.get("OMPU_BUS_DIR", str(Path.home()/"OMPU_shared"/"bus")))
    copy = work / "bus"; (copy/"messages").mkdir(parents=True)
    # minimal copy: real bus.py + db + a slice of messages + feed
    shutil.copy2(src/"bus.py", copy/"bus.py")
    if (src/"bus.db").exists(): shutil.copy2(src/"bus.db", copy/"bus.db")
    if (src/"feed.jsonl").exists(): shutil.copy2(src/"feed.jsonl", copy/"feed.jsonl")
    else: (copy/"feed.jsonl").write_text("")
    env = dict(os.environ, OMPU_BUS_DIR=str(copy),
               OMPU_PARACHUTE_DIR=str(work/"parachute"))
    def run(*a):
        return subprocess.run([sys.executable, __file__, *a], capture_output=True,
                              text=True, env=env)
    print("--- 1. probe (copy on POSIX /tmp — should be UP) ---")
    print(run("probe").stdout.strip())
    print("--- 2. simulate DOWN: post with --force-buffer ---")
    marker = f"parachute-selftest-{_mk_msg_id()}"
    print(run("post", "--from", "nestor", "--from-model", "claude-opus-4-8",
              "--subject", marker, "--body", "round-trip proof", "--force-buffer").stdout.strip())
    print("--- 3. restore: merge buffer -> copy bus + reindex ---")
    print(run("restore").stdout.strip())
    print("--- 4. ASSERT marker present in copy's bus.db ---")
    c = sqlite3.connect(copy/"bus.db")
    n = c.execute("SELECT count(*) FROM messages WHERE subject=?", (marker,)).fetchone()[0]
    c.close()
    ok = n == 1
    print(f"{'PASS ✅' if ok else 'FAIL ❌'}: marker rows in db = {n} (expected 1)")
    shutil.rmtree(work, ignore_errors=True)
    return 0 if ok else 1


def main():
    p = argparse.ArgumentParser(description="VM-local survival buffer for the OMPU bus")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("probe")
    pp = sub.add_parser("post")
    pp.add_argument("--from", required=True)
    pp.add_argument("--from-model", dest="from_model", default="claude-opus-4-8")
    pp.add_argument("--from-provider", dest="from_provider", default="anthropic")
    pp.add_argument("--subject", required=True)
    pp.add_argument("--body", default="")
    pp.add_argument("--to-channel", dest="to_channel", default="general")
    pp.add_argument("--to", action="append")
    pp.add_argument("--force-buffer", action="store_true", help="pretend bus is down (test)")
    sub.add_parser("restore")
    sub.add_parser("selftest")
    args = p.parse_args()
    return {"probe": cmd_probe, "post": cmd_post, "restore": cmd_restore,
            "selftest": cmd_selftest}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
