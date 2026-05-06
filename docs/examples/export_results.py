"""
export_results.py — fetch all complete search results and write a summary CSV.

Usage:
    CHAPARRAL_API_KEY="chpr_live_..." python export_results.py
"""

import csv
import sys
from chaparral import Client


def main() -> None:
    client = Client()

    results = client.list_search_results()
    complete = [r for r in results if r.status == "complete"]

    if not complete:
        print("No complete search results found.")
        sys.exit(0)

    writer = csv.DictWriter(
        sys.stdout,
        fieldnames=["id", "status", "created_at"],
        extrasaction="ignore",
    )
    writer.writeheader()
    for r in complete:
        writer.writerow({
            "id": r.id,
            "status": r.status,
            "created_at": str(r.created_at),
        })


if __name__ == "__main__":
    main()
