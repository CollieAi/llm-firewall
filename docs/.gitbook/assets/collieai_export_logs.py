#!/usr/bin/env python3
"""Export CollieAI logs with filters via the dashboard API.

Usage:
    python3 collieai_export_logs.py \
        --base-url https://app.collieai.io \
        --email you@example.com \
        --project-id <PROJECT_ID> \
        --out logs.ndjson \
        [filters...]

The password is read from the COLLIEAI_PASSWORD environment variable
(or prompted interactively). Output is NDJSON (one log row per line)
or CSV with --format csv.

Filters (all optional, combine freely):
    --date-from / --date-to   ISO timestamp (2026-08-12T00:00:00Z)
                              or calendar date (2026-08-12)
    --status <v> [...]        repeatable; e.g. --status success --status blocked
    --event-type <v> [...]    repeatable
    --direction <v> [...]     repeatable: inbound / outbound
    --model <v> [...]         repeatable
    --source <v> [...]        repeatable
    --context-status <v> [...] repeatable
    --exclude <dim> [...]     flip a dimension to exclude-mode,
                              e.g. --source playground --exclude source
    --search <text>           substring search (min 2 chars; matches
                              bodies AND metadata/IDs/rule containers)
    --has-rules true|false    only rows with / without triggered rules
                              (sent on the wire as yes|no)
    --collapse-streams true|false
                              default false: export EVERY chunk row.
                              true collapses finished chunk streams to
                              their terminal row (the dashboard view)
    --duration-min / --duration-max   milliseconds
    --tokens-min / --tokens-max
    --conversation-id <id>

Pagination freezes a snapshot: the first page's `snapshot` timestamp
is passed back as `before`, so rows arriving with NEWER timestamps
never shift pages. Late async inserts at-or-before the snapshot can
still shift offset pages. Without --max-rows the script runs a COUNT
DRIFT diagnostic and exits non-zero when the exported count differs
from the matched total. This detects drift, it does NOT prove
completeness — a shift can duplicate one row and drop another while
keeping the count. Exporting a CLOSED time window fully in the past
(--date-from/--date-to, after ingestion for that period settles)
REDUCES the risk but is still not a guarantee: date_to bounds the
event timestamp, not the insert time, so a backdated insert can land
inside a past window. A true guarantee needs a server-side
snapshot/watermark; re-running the window later and comparing counts
is the practical cross-check.
`--conversation-id` exports are ordered oldest-first by the API and
are NOT snapshot-frozen (no `before` is sent).

Output is ATOMIC when --out is a FILE: rows stream to a 0600 temp
file in the target directory and are moved over --out only after the
export finishes clean — a failed run never truncates or replaces an
existing archive, and a pre-existing file's loose permissions are
replaced along with its bytes. With `--out -` rows go straight to
stdout: a failed run may have emitted a partial export (and a shell
redirect truncates its target before the script even starts).

CSV cells that begin with =, +, -, or @ are prefixed with a
single-quote so spreadsheets don't execute them as formulas
(disable with --raw-csv).

Requires: Python 3.8+ (stdlib only).
"""
import argparse
import csv
import getpass
import json
import os
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request

REPEATABLE = {
    "status": "status",
    "event_type": "event_type",
    "direction": "direction",
    "model": "model",
    "source": "source",
    "context_status": "context_status",
}


def _http_error(prefix: str, e: "urllib.error.HTTPError") -> SystemExit:
    try:
        detail = json.loads(e.read().decode())
    except Exception:
        detail = e.reason
    return SystemExit(f"{prefix}: HTTP {e.code} — {detail}")


def login(base_url: str, email: str, password: str) -> str:
    """POST /auth/email/login; return the auth_token cookie value."""
    req = urllib.request.Request(
        f"{base_url}/auth/email/login",
        data=json.dumps({"email": email, "password": password}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            for header, value in resp.headers.items():
                if header.lower() == "set-cookie" and "auth_token=" in value:
                    return value.split("auth_token=", 1)[1].split(";", 1)[0]
    except urllib.error.HTTPError as e:
        raise _http_error("login failed", e) from None
    raise SystemExit("login succeeded but no auth_token cookie was set")


def fetch_page(base_url, token, params):
    query = urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(
        f"{base_url}/logs/api?{query}",
        headers={"Cookie": f"auth_token={token}"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        raise _http_error("export request failed", e) from None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base-url", default="https://app.collieai.io")
    ap.add_argument("--email", required=True)
    ap.add_argument("--project-id", required=True)
    ap.add_argument("--out", default="-", help="output file, - for stdout")
    ap.add_argument("--format", choices=["ndjson", "csv"], default="ndjson")
    ap.add_argument("--page-size", type=int, default=200)
    ap.add_argument("--max-rows", type=int, default=None)
    ap.add_argument("--date-from")
    ap.add_argument("--date-to")
    for opt in REPEATABLE:
        ap.add_argument(f"--{opt.replace('_', '-')}", action="append")
    ap.add_argument("--exclude", action="append", default=[],
                    choices=sorted(REPEATABLE),
                    help="flip this dimension's values to exclude-mode")
    ap.add_argument("--search")
    ap.add_argument("--has-rules", choices=["true", "false"])
    ap.add_argument("--collapse-streams", choices=["true", "false"],
                    default="false")
    ap.add_argument("--raw-csv", action="store_true",
                    help="disable CSV formula-injection neutralization")
    ap.add_argument("--duration-min", type=int)
    ap.add_argument("--duration-max", type=int)
    ap.add_argument("--tokens-min", type=int)
    ap.add_argument("--tokens-max", type=int)
    ap.add_argument("--conversation-id")
    args = ap.parse_args()

    if not 1 <= args.page_size <= 1000:
        raise SystemExit("--page-size must be between 1 and 1000")
    if args.max_rows is not None and args.max_rows < 1:
        # 0/negative silently disabled the row cap AND the drift
        # diagnostic via truthiness — refuse instead.
        raise SystemExit("--max-rows must be a positive integer")

    base_params: dict = {
        "project_id": args.project_id,
        "page_size": args.page_size,
    }
    if args.date_from:
        base_params["date_from"] = args.date_from
    if args.date_to:
        base_params["date_to"] = args.date_to
    for opt, wire in REPEATABLE.items():
        values = getattr(args, opt)
        if values:
            base_params[wire] = values
        if opt in args.exclude:
            if not values:
                raise SystemExit(
                    f"--exclude {opt} needs at least one --{opt} value")
            base_params[f"{wire}_mode"] = "exclude"
    if args.search is not None:
        if len(args.search) < 2:
            # the API silently ignores 1-char terms — that would turn
            # "filtered export" into "everything"; refuse instead.
            raise SystemExit("--search needs at least 2 characters")
        base_params["search"] = args.search
    if args.conversation_id:
        base_params["conversation_id"] = args.conversation_id
    if args.has_rules:
        # CLI speaks true/false; the wire contract is yes|no (any
        # other value is silently ignored by the API).
        base_params["has_rules"] = (
            "yes" if args.has_rules == "true" else "no")
    base_params["collapse_streams"] = args.collapse_streams
    for name in ("duration_min", "duration_max", "tokens_min", "tokens_max"):
        value = getattr(args, name)
        if value is not None:
            base_params[name] = value

    # Prompt for the password only after every argument validated —
    # a rejected flag must not first block on an interactive prompt.
    password = os.environ.get("COLLIEAI_PASSWORD") or getpass.getpass(
        f"CollieAi password for {args.email}: ")
    token = login(args.base_url, args.email, password)

    tmp_path = None
    if args.out == "-":
        out = sys.stdout
    else:
        # Stream into a 0600 temp file next to the target; only a
        # CLEAN finish moves it over --out (os.replace) — a failed
        # run never truncates an existing archive, and the atomic
        # move also replaces a pre-existing file's loose permissions.
        target = os.path.abspath(args.out)
        fd, tmp_path = tempfile.mkstemp(
            dir=os.path.dirname(target) or ".",
            prefix=".collieai-export-", suffix=".tmp")
        os.fchmod(fd, 0o600)
        out = os.fdopen(fd, "w", newline="", encoding="utf-8")

    def _csv_safe(value):
        if (not args.raw_csv and isinstance(value, str)
                and value[:1] in ("=", "+", "-", "@")):
            return "'" + value
        return value
    writer = None
    exported = 0
    page = 1
    snapshot = None
    clean = False
    try:
        total = None
        while True:
            params = dict(base_params, page=page)
            if snapshot and not args.conversation_id:
                params["before"] = snapshot
            data = fetch_page(args.base_url, token, params)
            if "error" in data and not data.get("logs"):
                raise SystemExit(f"API error: {data['error']}")
            rows = data.get("logs", [])
            if page == 1:
                snapshot = data.get("snapshot")
                total = data.get("total", 0)
                print(f"matched {total} rows (snapshot={snapshot})",
                      file=sys.stderr)
            if not rows:
                break
            for row in rows:
                if args.format == "ndjson":
                    out.write(json.dumps(row, ensure_ascii=False) + "\n")
                else:
                    if writer is None:
                        writer = csv.DictWriter(out, fieldnames=list(row))
                        writer.writeheader()
                    writer.writerow({
                        k: _csv_safe(
                            json.dumps(v, ensure_ascii=False)
                            if isinstance(v, (dict, list)) else v)
                        for k, v in row.items()
                    })
                exported += 1
                if args.max_rows is not None and exported >= args.max_rows:
                    break
            if args.max_rows is not None and exported >= args.max_rows:
                break
            if len(rows) < args.page_size:
                break
            page += 1
        clean = True
    finally:
        if out is not sys.stdout:
            out.close()
            if not clean and tmp_path is not None:
                os.unlink(tmp_path)
    print(f"exported {exported} rows", file=sys.stderr)
    if args.max_rows is None and total is not None and exported != total:
        if tmp_path is not None:
            os.unlink(tmp_path)
        raise SystemExit(
            f"COUNT DRIFT: exported {exported} != matched {total} — "
            f"offset pages shifted during the export (late inserts at "
            f"or before the snapshot). NOTE this diagnostic cannot "
            f"prove completeness — a shift can duplicate one row and "
            f"drop another while keeping the count; a closed past "
            f"time window reduces (not eliminates) the risk."
            + (" The existing --out file was left untouched."
               if tmp_path is not None
               else " Rows already streamed to stdout may be a "
                    "partial export."))
    if tmp_path is not None:
        os.replace(tmp_path, target)


if __name__ == "__main__":
    main()
