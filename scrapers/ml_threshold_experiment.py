#!/usr/bin/env python3
"""
ML Rate-Limit Threshold Experiment  (v2)
=========================================

Measures how many requests we can make to Mercado Livre before
getting blocked, testing multiple anti-detection strategies.

Strategies tested:
  A. Baseline        — sequential URLs, same context, delay only
  B. Shuffle         — randomise URL order (anti-behavioral)
  C. Context rotate  — new browser context every N requests
  D. Combined        — shuffle + context rotate + longer delay

Usage:
    cd scrapers/
    python ml_threshold_experiment.py --check           # just check if IP is clean
    python ml_threshold_experiment.py --test search      # search pagination only
    python ml_threshold_experiment.py --test product --delay 5
    python ml_threshold_experiment.py --test product --delay 10 --shuffle --rotate 5
    python ml_threshold_experiment.py --test product --delay 10 --shuffle --rotate 5 --max-products 50
"""

import argparse
import asyncio
import json
import logging
import random
import sys
import time

sys.path.insert(0, ".")

from playwright.async_api import async_playwright

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("ml_experiment_latest.log", mode="w"),
    ],
)
logger = logging.getLogger(__name__)

CHROME_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

STEALTH_SCRIPT = (
    'Object.defineProperty(navigator, "webdriver", { get: () => undefined });'
)


def is_blocked(url: str) -> bool:
    return "account-verification" in url or "login" in url


async def create_context(browser):
    ctx = await browser.new_context(
        user_agent=CHROME_UA,
        locale="pt-BR",
        timezone_id="America/Sao_Paulo",
        viewport={"width": 1366, "height": 768},
    )
    await ctx.add_init_script(STEALTH_SCRIPT)
    return ctx


async def check_ip_status():
    """Quick check: is our IP currently blocked?"""
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await create_context(browser)
        page = await ctx.new_page()
        blocked = True
        try:
            resp = await page.goto(
                "https://lista.mercadolivre.com.br/kindle",
                wait_until="domcontentloaded",
                timeout=15_000,
            )
            blocked = is_blocked(page.url)
            if blocked:
                print("🔴 IP is BLOCKED — wait before running experiments")
            else:
                try:
                    await page.wait_for_selector(".ui-search-layout__item", timeout=8_000)
                    items = await page.query_selector_all(".poly-component__title")
                    print(f"✅ IP is CLEAN — {len(items)} items loaded. Safe to experiment.")
                except Exception:
                    print("🟡 IP seems clean but page didn't fully render")
        except Exception as e:
            print(f"❌ Error checking IP: {e}")
        finally:
            try:
                await ctx.close()
            except Exception:
                pass
            try:
                await browser.close()
            except Exception:
                pass
        return not blocked


# ------------------------------------------------------------------
# Test A: Search pages (pagination)
# ------------------------------------------------------------------

async def test_search_pages(delay: float, max_pages: int = 20, term: str = "kindle"):
    """Load successive search result pages with a delay between each."""
    results = {
        "test": "search_pages",
        "term": term,
        "delay_seconds": delay,
        "pages_loaded": 0,
        "total_links": 0,
        "blocked_at": None,
        "elapsed_seconds": 0,
    }

    t0 = time.time()
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await create_context(browser)
        page = await ctx.new_page()
        page.set_default_timeout(20_000)

        all_links = 0

        for page_num in range(1, max_pages + 1):
            offset = all_links
            if offset == 0:
                url = f"https://lista.mercadolivre.com.br/{term}"
            else:
                url = f"https://lista.mercadolivre.com.br/{term}_Desde_{offset + 1}_NoIndex_True"

            logger.info(
                "Search page %d (delay=%.1fs, total_links=%d) → %s",
                page_num, delay, all_links, url[:80],
            )

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=20_000)
            except Exception as e:
                logger.warning("Page load failed: %s", e)
                results["blocked_at"] = page_num
                results["error"] = str(e)
                break

            if is_blocked(page.url):
                logger.warning("🔴 BLOCKED at search page %d! URL: %s", page_num, page.url[:100])
                results["blocked_at"] = page_num
                break

            # Count items
            try:
                await page.wait_for_selector(".ui-search-layout__item", timeout=8_000)
                items = await page.query_selector_all(".poly-component__title")
                count = len(items)
            except Exception:
                count = 0

            all_links += count
            results["pages_loaded"] = page_num
            results["total_links"] = all_links
            logger.info("  ✅ Page %d: %d items (total: %d)", page_num, count, all_links)

            if count == 0:
                logger.info("  No more items — stopping pagination")
                break

            # Check for next page button
            next_btn = await page.query_selector("a.andes-pagination__link[title='Seguinte']")
            if not next_btn:
                logger.info("  No next button — stopping pagination")
                break

            if page_num < max_pages:
                await asyncio.sleep(delay)

        await ctx.close()
        await browser.close()

    results["elapsed_seconds"] = round(time.time() - t0, 1)
    return results


# ------------------------------------------------------------------
# Test B: Product pages (with anti-detection strategies)
# ------------------------------------------------------------------

async def test_product_pages(
    delay: float,
    max_products: int = 50,
    shuffle: bool = False,
    rotate_every: int = 0,
    term: str = "kindle",
):
    """Scrape product pages one by one with configurable strategies.

    Uses a SINGLE browser session for both search and scraping to avoid
    wasting the first (free) search page load on a separate step.

    Parameters
    ----------
    delay:          Seconds to wait between each product scrape.
    max_products:   Max products to attempt.
    shuffle:        If True, randomise the URL order (anti-behavioral).
    rotate_every:   Create a new browser context every N requests.
                    0 = never rotate (single context for all).
    """
    strategy_parts = []
    if shuffle:
        strategy_parts.append("shuffle")
    if rotate_every > 0:
        strategy_parts.append(f"rotate/{rotate_every}")
    strategy_parts.append(f"delay={delay}s")
    strategy_label = " + ".join(strategy_parts) if strategy_parts else "baseline"

    results = {
        "test": "product_pages",
        "term": term,
        "strategy": strategy_label,
        "delay_seconds": delay,
        "shuffle": shuffle,
        "rotate_every": rotate_every,
        "urls_collected": 0,
        "products_scraped": 0,
        "blocked_at": None,
        "elapsed_seconds": 0,
        "search_time": 0,
        "scrape_time": 0,
    }

    t0 = time.time()
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)

        # ----------------------------------------------------------
        # Step 1: Collect product URLs from search (ALL pages)
        # Uses 15s delay between search pages (proven safe).
        # ----------------------------------------------------------
        SEARCH_PAGE_DELAY = 15.0
        ctx = await create_context(browser)
        page = await ctx.new_page()
        page.set_default_timeout(20_000)

        urls: list[str] = []
        search_page = 0

        while True:
            search_page += 1
            offset = len(urls)
            if offset == 0:
                search_url = f"https://lista.mercadolivre.com.br/{term}"
            else:
                search_url = f"https://lista.mercadolivre.com.br/{term}_Desde_{offset + 1}_NoIndex_True"

            logger.info(
                "Search page %d (collected %d URLs so far) → %s",
                search_page, len(urls), search_url[:80],
            )

            try:
                await page.goto(search_url, wait_until="domcontentloaded")
            except Exception as e:
                logger.warning("Search page %d failed to load: %s", search_page, e)
                if not urls:
                    results["blocked_at"] = 0
                    results["error"] = str(e)
                    await ctx.close()
                    await browser.close()
                    results["elapsed_seconds"] = round(time.time() - t0, 1)
                    return results
                break

            if is_blocked(page.url):
                if not urls:
                    logger.warning("🔴 BLOCKED on search page 1 — IP is still flagged.")
                    results["blocked_at"] = 0
                    results["error"] = "Blocked on search page"
                    await ctx.close()
                    await browser.close()
                    results["elapsed_seconds"] = round(time.time() - t0, 1)
                    return results
                logger.warning("🔴 BLOCKED on search page %d — stopping search, will scrape %d URLs collected so far", search_page, len(urls))
                break

            try:
                await page.wait_for_selector(".ui-search-layout__item", timeout=10_000)
            except Exception:
                logger.info("No items rendered on search page %d — end of results", search_page)
                break

            link_elements = await page.query_selector_all(".poly-component__title")
            page_urls = []
            for el in link_elements:
                href = await el.get_attribute("href")
                if href and "click1.mercadolivre" not in href:
                    page_urls.append(href)

            if not page_urls:
                logger.info("No links on search page %d — end of results", search_page)
                break

            urls.extend(page_urls)
            logger.info("  ✅ Search page %d: %d URLs (total: %d)", search_page, len(page_urls), len(urls))

            # Check if we already have enough
            if max_products > 0 and len(urls) >= max_products:
                logger.info("Reached max_products (%d) — stopping search", max_products)
                break

            # Check for next page
            next_btn = await page.query_selector("a.andes-pagination__link[title='Seguinte']")
            if not next_btn:
                logger.info("No next page button — end of results")
                break

            # Delay between search pages
            await asyncio.sleep(SEARCH_PAGE_DELAY)

        await ctx.close()
        results["search_time"] = round(time.time() - t0, 1)
        results["urls_collected"] = len(urls)
        results["search_pages"] = search_page
        logger.info("Collected %d product URLs from %d search pages in %.1fs", len(urls), search_page, results["search_time"])

        if not urls:
            logger.warning("No URLs collected — cannot test product pages")
            await browser.close()
            results["elapsed_seconds"] = round(time.time() - t0, 1)
            return results

        # Trim to max
        if max_products > 0:
            urls = urls[:max_products]

        # ----------------------------------------------------------
        # Step 2: Apply strategies
        # ----------------------------------------------------------
        if shuffle:
            random.shuffle(urls)
            logger.info("🔀 URLs shuffled (anti-sequential)")

        # ----------------------------------------------------------
        # Step 3: Wait before starting scraping
        # Give ML time to "forget" the search request.
        # ----------------------------------------------------------
        pre_scrape_delay = max(delay, 5.0)
        logger.info("⏳ Pre-scrape cooldown: %.0fs...", pre_scrape_delay)
        await asyncio.sleep(pre_scrape_delay)

        # ----------------------------------------------------------
        # Step 4: Scrape product pages
        # ----------------------------------------------------------
        t_scrape = time.time()
        logger.info(
            "Scraping %d products | strategy: %s",
            len(urls), strategy_label,
        )

        # Initial context for scraping (fresh — not the search context)
        ctx = await create_context(browser)
        page = await ctx.new_page()
        page.set_default_timeout(20_000)

        for i, url in enumerate(urls, 1):
            # Context rotation
            if rotate_every > 0 and i > 1 and (i - 1) % rotate_every == 0:
                await ctx.close()
                ctx = await create_context(browser)
                page = await ctx.new_page()
                page.set_default_timeout(20_000)
                logger.info("  🔄 [Context rotated at request %d]", i)

            short_url = url.split("/")[-1][:50] if "/" in url else url[:50]

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=20_000)
            except Exception as e:
                logger.warning("  ❌ Load failed at #%d: %s", i, str(e)[:80])
                results["blocked_at"] = i
                results["error"] = str(e)
                break

            if is_blocked(page.url):
                logger.warning("🔴 BLOCKED at product #%d! URL: %s", i, page.url[:100])
                results["blocked_at"] = i
                break

            # Quick extraction to confirm we got real content
            title_el = await page.query_selector("h1.ui-pdp-title")
            title = (await title_el.inner_text())[:50] if title_el else "?"
            results["products_scraped"] = i
            logger.info("  ✅ #%d/%d: %s", i, len(urls), title)

            # Delay before next request
            if i < len(urls):
                # Add small random jitter (±20%) to look more human
                jitter = delay * 0.2 * (random.random() * 2 - 1)
                actual_delay = max(0.5, delay + jitter)
                await asyncio.sleep(actual_delay)

        await ctx.close()
        await browser.close()

    results["scrape_time"] = round(time.time() - t_scrape, 1)
    results["elapsed_seconds"] = round(time.time() - t0, 1)
    return results


# ------------------------------------------------------------------
# Output
# ------------------------------------------------------------------

def print_result(result: dict):
    print()
    print("=" * 60)
    test_name = result["test"]
    if result.get("strategy"):
        test_name += f" [{result['strategy']}]"
    print(f"  TEST: {test_name}")
    print("=" * 60)

    if result["test"] == "search_pages":
        print(f"  Delay:          {result['delay_seconds']}s")
        print(f"  Pages loaded:   {result['pages_loaded']}")
        print(f"  Total links:    {result['total_links']}")
    else:
        print(f"  Strategy:         {result.get('strategy', 'baseline')}")
        print(f"  Delay:            {result['delay_seconds']}s")
        print(f"  Shuffle:          {result.get('shuffle', False)}")
        print(f"  Context rotate:   every {result.get('rotate_every', 0)} reqs")
        print(f"  Products scraped: {result['products_scraped']}")

    if result.get("blocked_at"):
        print(f"  🔴 BLOCKED at request #{result['blocked_at']}")
        if result.get("error"):
            print(f"     Error: {result['error'][:80]}")
    else:
        print(f"  ✅ NO BLOCK — all requests succeeded!")

    print(f"  Total time: {result['elapsed_seconds']}s")
    print("=" * 60)
    print()


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

async def main():
    parser = argparse.ArgumentParser(
        description="ML Rate-Limit Threshold Experiment (v2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --check                                    # check IP status
  %(prog)s --test search --delay 5                    # search pages, 5s delay
  %(prog)s --test product --delay 5                   # product pages, 5s, no tricks
  %(prog)s --test product --delay 10 --shuffle        # shuffle URLs
  %(prog)s --test product --delay 10 --shuffle --rotate 5   # shuffle + rotate
  %(prog)s --test product --delay 10 --shuffle --rotate 5 --max-products 50
""",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Just check if IP is clean (no scraping)",
    )
    parser.add_argument(
        "--test", choices=["search", "product", "both"], default="both",
        help="Which test to run (default: both)",
    )
    parser.add_argument(
        "--delay", type=float, default=5.0,
        help="Delay in seconds between requests (default: 5)",
    )
    parser.add_argument(
        "--shuffle", action="store_true",
        help="Randomise product URL order (anti-behavioral detection)",
    )
    parser.add_argument(
        "--rotate", type=int, default=0, metavar="N",
        help="Create new browser context every N product requests (0=never)",
    )
    parser.add_argument(
        "--max-products", type=int, default=0,
        help="Max product pages to scrape (default: 0 = no limit)",
    )
    parser.add_argument(
        "--max-search-pages", type=int, default=20,
        help="Max search pages to load (default: 20)",
    )
    parser.add_argument(
        "--term", type=str, default="kindle",
        help="Search term to use (default: kindle)",
    )
    args = parser.parse_args()

    # --check mode: just test IP and exit
    if args.check:
        await check_ip_status()
        return

    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║    ML RATE-LIMIT THRESHOLD EXPERIMENT v2                ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print(f"║  Test:     {args.test:<46s}║")
    print(f"║  Term:     {args.term:<46s}║")
    print(f"║  Delay:    {args.delay}s{' ' * (44 - len(str(args.delay)))}║")
    print(f"║  Shuffle:  {str(args.shuffle):<46s}║")
    print(f"║  Rotate:   every {args.rotate} reqs{' ' * (37 - len(str(args.rotate)))}║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    all_results = []

    if args.test in ("search", "both"):
        result = await test_search_pages(
            delay=args.delay, max_pages=args.max_search_pages, term=args.term,
        )
        print_result(result)
        all_results.append(result)

        if result.get("blocked_at"):
            print("⚠️  Search test blocked — stopping to preserve IP")
            with open("ml_experiment_results.json", "w") as f:
                json.dump(all_results, f, indent=2)
            return

        if args.test == "both":
            cool = 30
            print(f"⏳ Cooling down {cool}s before product test...")
            await asyncio.sleep(cool)

    if args.test in ("product", "both"):
        result = await test_product_pages(
            delay=args.delay,
            max_products=args.max_products,
            shuffle=args.shuffle,
            rotate_every=args.rotate,
            term=args.term,
        )
        print_result(result)
        all_results.append(result)

    # Save results
    # Append to existing results file if it exists
    existing = []
    try:
        with open("ml_experiment_results.json") as f:
            existing = json.load(f)
            if not isinstance(existing, list):
                existing = [existing]
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    existing.extend(all_results)
    with open("ml_experiment_results.json", "w") as f:
        json.dump(existing, f, indent=2)

    print(f"Results appended to ml_experiment_results.json ({len(existing)} total runs)")


if __name__ == "__main__":
    asyncio.run(main())
