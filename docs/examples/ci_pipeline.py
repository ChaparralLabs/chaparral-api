"""
ci_pipeline.py — example for use in CI (GitHub Actions, etc.).

Verifies that a set of expected projects exists and all recent searches
completed successfully. Exits non-zero if any check fails.

Usage:
    CHAPARRAL_API_KEY="chpr_live_..." python ci_pipeline.py
"""

import sys
from chaparral import Client
from chaparral.exceptions import ChaparralError

EXPECTED_PROJECTS = ["My Project", "Reference Run"]


def main() -> int:
    try:
        client = Client()
    except ChaparralError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    # Check expected projects exist
    projects = client.list_projects()
    project_names = {p.name for p in projects}
    missing = [name for name in EXPECTED_PROJECTS if name not in project_names]
    if missing:
        print(f"FAIL: missing projects: {missing}", file=sys.stderr)
        return 1
    print(f"OK: found {len(projects)} projects")

    # Check no recent searches failed
    results = client.list_search_results()
    failed = [r for r in results if r.status == "failed"]
    if failed:
        print(f"FAIL: {len(failed)} failed search(es): {[r.id for r in failed]}", file=sys.stderr)
        return 1
    print(f"OK: {len(results)} search result(s), none failed")

    return 0


if __name__ == "__main__":
    sys.exit(main())
