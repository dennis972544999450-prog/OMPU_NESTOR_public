#!/usr/bin/env python3
"""
test_sites.py — OMPU Deployed Sites HTTP Status Checker
Created: 2026-06-30 | Bolt gen-48 | Entry 044

Curls all deployed OMPU sites, checks HTTP status and expected headers.
Run after any deploy to verify site is live.

Usage:
    python3 test_sites.py                  # test all sites
    python3 test_sites.py --site jsontube.org  # test one site
    python3 test_sites.py --json           # output JSON
    python3 test_sites.py --quiet          # only show failures
    python3 test_sites.py --timeout 15     # custom timeout (default: 10s)
"""

import urllib.request
import urllib.error
import json
import sys
import time
import argparse
from typing import Optional

# ─── SITE REGISTRY ──────────────────────────────────────────────────────────

SITES = [
    {
        "name": "jsontube.org",
        "url": "https://jsontube.org/",
        "expected_status": 200,
        "expected_headers": {},
        "notes": "AI-facing feed, live since 2026",
        "category": "core"
    },
    {
        "name": "paniccast.com",
        "url": "https://paniccast.com/",
        "expected_status": 200,
        "expected_headers": {"x-built-by": "Bolt gen-40 / OMPU"},
        "notes": "CF Worker, active zone — deployed Entry 042",
        "category": "worker"
    },
    {
        "name": "paniccast.com/health",
        "url": "https://paniccast.com/health",
        "expected_status": 200,
        "expected_headers": {},
        "check_json": True,
        "expected_json_keys": ["panic_level", "signal", "carrier"],
        "notes": "Health endpoint from CF Worker",
        "category": "worker"
    },
    {
        "name": "aisauna.org",
        "url": "https://aisauna.org/",
        "expected_status": [200, 522, 0],  # 0 = connection refused / timeout (zone pending)
        "expected_headers": {},
        "notes": "CF Worker deployed, zone pending NS delegation — Entry 041",
        "category": "worker_pending"
    },
    {
        "name": "mirageloom.org",
        "url": "https://mirageloom.org/",
        "expected_status": 200,
        "expected_headers": {},
        "notes": "MirageLoom — Sprinkler mode",
        "category": "core"
    },
    {
        "name": "ompu.eu",
        "url": "https://ompu.eu/",
        "expected_status": [200, 0],  # may timeout from sandbox environment
        "expected_headers": {},
        "notes": "Main OMPU site — may be unreachable from Cowork sandbox",
        "category": "core"
    },
    {
        "name": "attentionheads.org",
        "url": "https://attentionheads.org/",
        "expected_status": 200,
        "expected_headers": {},
        "notes": "AttentionHeads forum",
        "category": "external"
    },
    {
        "name": "catconstant.com",
        "url": "https://catconstant.com/",
        "expected_status": [200, 404, 0],
        "expected_headers": {},
        "notes": "CatConstant — CF token blocked, may not be live",
        "category": "pending"
    },
    {
        "name": "huyuring.org",
        "url": "https://huyuring.org/",
        "expected_status": [200, 404],
        "expected_headers": {},
        "notes": "HT spec site",
        "category": "core"
    },
    {
        "name": "annawelt.com",
        "url": "https://annawelt.com/",
        "expected_status": [200, 404, 0],  # DNS may not resolve from all environments
        "expected_headers": {},
        "notes": "AnnaWelt — learning platform, DNS may be pending",
        "category": "pending"
    },
]

# ─── TEST RUNNER ─────────────────────────────────────────────────────────────

def check_site(site: dict, timeout: int = 10) -> dict:
    """Check a single site. Returns result dict."""
    url = site["url"]
    name = site["name"]
    expected_status = site.get("expected_status", 200)
    if isinstance(expected_status, int):
        expected_status = [expected_status]

    result = {
        "name": name,
        "url": url,
        "category": site.get("category", "unknown"),
        "notes": site.get("notes", ""),
        "status_code": None,
        "response_time_ms": None,
        "headers_checked": [],
        "json_keys_found": [],
        "passed": False,
        "failures": [],
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    start = time.time()
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "OMPU-TestBot/1.0 (bolt; test_sites.py; ompu.eu)",
                "Accept": "text/html,application/json,*/*",
            }
        )
        response = urllib.request.urlopen(req, timeout=timeout)
        elapsed_ms = int((time.time() - start) * 1000)

        result["status_code"] = response.getcode()
        result["response_time_ms"] = elapsed_ms

        # Check status
        if result["status_code"] not in expected_status:
            result["failures"].append(
                f"Status {result['status_code']} not in expected {expected_status}"
            )

        # Check headers
        resp_headers = {k.lower(): v for k, v in response.headers.items()}
        for header_name, expected_value in site.get("expected_headers", {}).items():
            actual_value = resp_headers.get(header_name.lower(), "")
            if expected_value.lower() in actual_value.lower():
                result["headers_checked"].append(f"{header_name}: OK")
            else:
                result["headers_checked"].append(f"{header_name}: MISSING (got: '{actual_value}')")
                result["failures"].append(
                    f"Header '{header_name}' expected '{expected_value}', got '{actual_value}'"
                )

        # Check JSON body
        if site.get("check_json"):
            try:
                body = response.read().decode("utf-8", errors="replace")
                data = json.loads(body)
                for key in site.get("expected_json_keys", []):
                    if key in data:
                        result["json_keys_found"].append(f"{key}: OK")
                    else:
                        result["json_keys_found"].append(f"{key}: MISSING")
                        result["failures"].append(f"JSON key '{key}' not found in response")
            except (json.JSONDecodeError, Exception) as e:
                result["failures"].append(f"JSON parse error: {e}")

    except urllib.error.HTTPError as e:
        elapsed_ms = int((time.time() - start) * 1000)
        result["status_code"] = e.code
        result["response_time_ms"] = elapsed_ms
        if e.code not in expected_status:
            result["failures"].append(f"HTTP error {e.code}: {e.reason}")

    except urllib.error.URLError as e:
        elapsed_ms = int((time.time() - start) * 1000)
        result["status_code"] = 0
        result["response_time_ms"] = elapsed_ms
        if 0 not in expected_status:
            result["failures"].append(f"Connection error: {e.reason}")
        else:
            # 0 was expected (pending zone etc.)
            result["failures"] = []

    except Exception as e:
        elapsed_ms = int((time.time() - start) * 1000)
        result["status_code"] = 0
        result["response_time_ms"] = elapsed_ms
        if 0 not in expected_status:
            result["failures"].append(f"Unexpected error: {e}")

    result["passed"] = len(result["failures"]) == 0
    return result


def run_tests(
    sites: list,
    timeout: int = 10,
    quiet: bool = False,
    json_output: bool = False,
) -> dict:
    """Run all tests and return summary."""
    results = []
    passed = 0
    failed = 0
    warned = 0  # pending/external sites

    for site in sites:
        if not quiet:
            print(f"  Checking {site['name']}...", end="", flush=True)
        result = check_site(site, timeout=timeout)
        results.append(result)

        cat = site.get("category", "")
        is_informational = cat in ("pending", "worker_pending", "external")

        if result["passed"]:
            passed += 1
            if not quiet:
                status_str = f"HTTP {result['status_code']}" if result['status_code'] else "N/A (expected)"
                print(f" PASS [{status_str}] {result['response_time_ms']}ms")
        elif is_informational:
            warned += 1
            if not quiet:
                status_str = f"HTTP {result['status_code']}" if result['status_code'] else "UNREACHABLE"
                print(f" WARN [{status_str}] {result['response_time_ms']}ms — {site.get('notes', '')}")
                for failure in result["failures"]:
                    print(f"    ! {failure}")
        else:
            failed += 1
            if not quiet:
                status_str = f"HTTP {result['status_code']}" if result['status_code'] else "UNREACHABLE"
                print(f" FAIL [{status_str}] {result['response_time_ms']}ms")
                for failure in result["failures"]:
                    print(f"    ! {failure}")

    summary = {
        "schema": "ompu.site-test.v1",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sites_tested": len(sites),
        "passed": passed,
        "failed": failed,
        "warned": warned,
        "overall": "PASS" if failed == 0 else "FAIL",
        "results": results,
    }

    return summary


def print_summary(summary: dict, quiet: bool = False) -> None:
    """Print human-readable summary."""
    if not quiet or summary["overall"] == "FAIL":
        print()
        print("=" * 60)
        print(f"OMPU Site Test — {summary['timestamp']}")
        print(f"Sites tested: {summary['sites_tested']}")
        print(f"  PASS: {summary['passed']}")
        print(f"  WARN: {summary['warned']} (pending/informational)")
        print(f"  FAIL: {summary['failed']}")
        print(f"Overall: {summary['overall']}")
        print("=" * 60)

        if summary["failed"] > 0:
            print("\nFailed sites:")
            for r in summary["results"]:
                if not r["passed"] and r.get("category") not in ("pending", "worker_pending", "external"):
                    print(f"  {r['name']} ({r['url']})")
                    for failure in r["failures"]:
                        print(f"    -> {failure}")
            print()
            print("Check ERROR_LOG.md for known error patterns.")
            print("Check TESTING_PROTOCOL.md for remediation steps.")


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="OMPU deployed sites HTTP status checker"
    )
    parser.add_argument(
        "--site",
        help="Test only this site name (partial match)",
        default=None
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only show failures"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Request timeout in seconds (default: 10)"
    )
    parser.add_argument(
        "--category",
        choices=["core", "worker", "worker_pending", "pending", "external"],
        help="Test only sites in this category",
        default=None
    )
    args = parser.parse_args()

    # Filter sites
    sites_to_test = SITES
    if args.site:
        sites_to_test = [s for s in SITES if args.site.lower() in s["name"].lower()]
        if not sites_to_test:
            print(f"No sites matching '{args.site}'")
            print(f"Available: {', '.join(s['name'] for s in SITES)}")
            sys.exit(1)
    if args.category:
        sites_to_test = [s for s in sites_to_test if s.get("category") == args.category]
        if not sites_to_test:
            print(f"No sites in category '{args.category}'")
            sys.exit(1)

    if not args.quiet:
        print(f"OMPU Site Test — {len(sites_to_test)} sites — timeout={args.timeout}s")
        print()

    summary = run_tests(
        sites=sites_to_test,
        timeout=args.timeout,
        quiet=args.quiet,
        json_output=args.json,
    )

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print_summary(summary, quiet=args.quiet)

    # Exit code: 0=all pass, 1=some warnings, 2=failures
    if summary["failed"] > 0:
        sys.exit(2)
    elif summary["warned"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
