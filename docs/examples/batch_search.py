"""
batch_search.py — poll a list of known search result IDs until all complete.

Usage:
    CHAPARRAL_API_KEY="chpr_live_..." python batch_search.py
"""

import time
from chaparral import Client
from chaparral.exceptions import NotFoundError

SEARCH_IDS = [
    "srch_AAA",
    "srch_BBB",
    "srch_CCC",
]
POLL_INTERVAL = 15  # seconds


def main() -> None:
    client = Client()
    pending = set(SEARCH_IDS)

    while pending:
        done = set()
        for sid in pending:
            try:
                result = client.get_search_result(sid)
            except NotFoundError:
                print(f"{sid}: not found — skipping")
                done.add(sid)
                continue

            print(f"{sid}: {result.status}")
            if result.status in ("completed", "failed"):
                done.add(sid)

        pending -= done
        if pending:
            time.sleep(POLL_INTERVAL)

    print("All searches finished.")


if __name__ == "__main__":
    main()
