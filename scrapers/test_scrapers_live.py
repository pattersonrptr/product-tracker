#!/usr/bin/env python3
"""
Live test script — validates each scraper by actually hitting the real websites.

Usage:
    cd scrapers/
    python test_scrapers_live.py                          # all scrapers, default term
    python test_scrapers_live.py --term "kindle"          # custom search term
    python test_scrapers_live.py --scrapers olx enjoei    # only specific scrapers
    python test_scrapers_live.py --scrape-detail           # also scrape 1 product page each

No Docker, no Celery, no API required.
"""

import argparse
import json
import logging
import sys
import time
import traceback

# ---------------------------------------------------------------------------
# Make sure `src` is importable when running from scrapers/
# ---------------------------------------------------------------------------
sys.path.insert(0, ".")

from src.scrapers.factory.scraper_factory import ScraperFactory
from src.scrapers.manager.scraper_manager import ScraperManager

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
AVAILABLE_SCRAPERS = ["olx", "enjoei", "estante_virtual", "mercado_livre"]
DEFAULT_SEARCH_TERM = "kindle"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------
def test_search(scraper_name: str, search_term: str) -> dict:
    """Test the search phase: returns URLs found."""
    result = {
        "scraper": scraper_name,
        "phase": "search",
        "search_term": search_term,
        "status": "FAIL",
        "urls_found": 0,
        "sample_urls": [],
        "time_seconds": 0,
        "error": None,
    }

    t0 = time.time()
    try:
        scraper = ScraperFactory.create_scraper(scraper_name)
        manager = ScraperManager(scraper)
        urls = list(manager.get_products_urls(search_term))
        elapsed = round(time.time() - t0, 2)

        result["urls_found"] = len(urls)
        result["sample_urls"] = urls[:3]
        result["time_seconds"] = elapsed

        if urls:
            result["status"] = "OK"
        else:
            result["status"] = "WARN"
            result["error"] = "Search returned 0 URLs"

    except Exception as e:
        result["time_seconds"] = round(time.time() - t0, 2)
        result["error"] = f"{type(e).__name__}: {e}"
        result["traceback"] = traceback.format_exc()

    return result


def test_scrape_detail(scraper_name: str, url: str) -> dict:
    """Test scraping a single product page."""
    result = {
        "scraper": scraper_name,
        "phase": "scrape_detail",
        "url": url,
        "status": "FAIL",
        "data": {},
        "time_seconds": 0,
        "error": None,
    }

    t0 = time.time()
    try:
        scraper = ScraperFactory.create_scraper(scraper_name)
        manager = ScraperManager(scraper)
        data = manager.scrape_product(url)
        elapsed = round(time.time() - t0, 2)

        result["data"] = data
        result["time_seconds"] = elapsed

        # Basic validation
        if data and data.get("title"):
            result["status"] = "OK"
        else:
            result["status"] = "WARN"
            result["error"] = "Scrape returned empty or no title"

    except Exception as e:
        result["time_seconds"] = round(time.time() - t0, 2)
        result["error"] = f"{type(e).__name__}: {e}"
        result["traceback"] = traceback.format_exc()

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Live scraper validation")
    parser.add_argument(
        "--term", default=DEFAULT_SEARCH_TERM, help="Search term (default: kindle)"
    )
    parser.add_argument(
        "--scrapers",
        nargs="*",
        default=AVAILABLE_SCRAPERS,
        help=f"Scrapers to test (default: all). Options: {AVAILABLE_SCRAPERS}",
    )
    parser.add_argument(
        "--scrape-detail",
        action="store_true",
        help="Also scrape the first product page from each scraper",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=1,
        help="Max search pages to fetch (default: 1, keeps it fast)",
    )
    args = parser.parse_args()

    print("=" * 70)
    print(f"  LIVE SCRAPER VALIDATION — term: '{args.term}'")
    print(f"  Scrapers: {args.scrapers}")
    print(f"  Scrape detail: {args.scrape_detail}")
    print("=" * 70)
    print()

    all_results = []

    for name in args.scrapers:
        print(f"{'─' * 70}")
        print(f"  ▶ {name.upper()}")
        print(f"{'─' * 70}")

        # --- Phase 1: Search ---
        search_result = test_search(name, args.term)
        all_results.append(search_result)

        status_icon = "✅" if search_result["status"] == "OK" else "⚠️" if search_result["status"] == "WARN" else "❌"
        print(f"  SEARCH  {status_icon}  {search_result['status']}  |  {search_result['urls_found']} URLs  |  {search_result['time_seconds']}s")

        if search_result["error"]:
            print(f"          Error: {search_result['error']}")

        if search_result["sample_urls"]:
            for u in search_result["sample_urls"][:2]:
                print(f"          → {u[:100]}...")

        # --- Phase 2: Scrape detail (optional) ---
        if args.scrape_detail and search_result["status"] == "OK" and search_result["sample_urls"]:
            first_url = search_result["sample_urls"][0]
            print(f"  Scraping detail: {first_url[:80]}...")

            detail_result = test_scrape_detail(name, first_url)
            all_results.append(detail_result)

            status_icon = "✅" if detail_result["status"] == "OK" else "⚠️" if detail_result["status"] == "WARN" else "❌"
            print(f"  DETAIL  {status_icon}  {detail_result['status']}  |  {detail_result['time_seconds']}s")

            if detail_result["data"]:
                d = detail_result["data"]
                print(f"          title: {(d.get('title') or 'N/A')[:60]}")
                print(f"          price: {d.get('price', 'N/A')}")
                print(f"          avail: {d.get('is_available', 'N/A')}")

            if detail_result["error"]:
                print(f"          Error: {detail_result['error']}")

        print()

    # --- Summary ---
    print("=" * 70)
    print("  SUMMARY")
    print("=" * 70)

    scrapers_ok = []
    scrapers_warn = []
    scrapers_fail = []

    for r in all_results:
        if r["phase"] != "search":
            continue
        if r["status"] == "OK":
            scrapers_ok.append(r["scraper"])
        elif r["status"] == "WARN":
            scrapers_warn.append(r["scraper"])
        else:
            scrapers_fail.append(r["scraper"])

    print(f"  ✅ Working:  {', '.join(scrapers_ok) if scrapers_ok else 'none'}")
    print(f"  ⚠️  Warning:  {', '.join(scrapers_warn) if scrapers_warn else 'none'}")
    print(f"  ❌ Failed:   {', '.join(scrapers_fail) if scrapers_fail else 'none'}")
    print()

    # Dump full JSON for analysis
    report_file = "scraper_test_report.json"
    with open(report_file, "w") as f:
        # Remove traceback from JSON for cleanliness
        clean = []
        for r in all_results:
            entry = {k: v for k, v in r.items() if k != "traceback"}
            clean.append(entry)
        json.dump(clean, f, indent=2, ensure_ascii=False, default=str)

    print(f"  Full report saved to: {report_file}")
    print()

    # Exit code: 0 if all OK, 1 if any failure
    sys.exit(1 if scrapers_fail else 0)


if __name__ == "__main__":
    main()
