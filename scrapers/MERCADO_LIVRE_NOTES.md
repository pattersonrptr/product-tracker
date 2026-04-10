# Mercado Livre Scraper — Technical Notes# Mercado Livre Scraper — Investigation Notes



> **Status:** ✅ Working — rate-limited scraping validated at scale (492/492 products, zero blocks)> **Last updated:** 2026-04-09

> **Status:** ✅ WORKING — Rate-limited scraping validated (492/492 products, zero blocks)

---> **Decision:** Gentle scraping with 15s search delay + 10s product delay + shuffle + context rotation works at scale



## How It Works---



ML blocks scrapers via **server-side IP reputation** (`x-is-search-bot: true`## Table of Contents

header). The block is **temporary** (expires in hours) and is triggered by

request frequency, not request count. Our solution: slow down enough to stay1. [Problem Summary](#problem-summary)

under the detection threshold.2. [What We Tested](#what-we-tested)

3. [Confirmed Dead Ends](#confirmed-dead-ends-do-not-retry)

### Production Configuration4. [How ML's Anti-Bot Works](#how-mls-anti-bot-works)

5. [Viable Solution: Residential Proxy](#viable-solution-residential-proxy)

```python6. [Implementation Plan](#implementation-plan)

# MercadoLivreScraper class attributes7. [Key Discovery: The Block is Temporary](#key-discovery-the-block-is-temporary)

_MAX_SEARCH_PAGES = 20           # Up to 20 pages (~1000 URLs)8. [Execution Plan: Gentle Rate-Limited Scraping](#execution-plan-gentle-rate-limited-scraping)

_SEARCH_PAGE_DELAY = 15.0        # Seconds between search result pages9. [Current Implementation Status](#current-implementation-status)

_PRODUCT_SCRAPE_DELAY = 10.0     # Seconds between product page scrapes

_JITTER_FACTOR = 0.2             # ±20% randomness on all delays---

_CONTEXT_ROTATION_INTERVAL = 5   # Fresh browser context every 5 requests

_SHUFFLE_URLS = True             # Randomize URL scraping order## Problem Summary

```

The `MercadoLivreScraper` code is **fully functional** — selectors, pagination,

### Validation Resultsproduct extraction all work correctly. The problem is **100% network-level**:

Mercado Livre blocks our requests **before any page content is served**.

| Test | Products | Result | Time |

|------|----------|--------|------|- **Search pages** (`lista.mercadolivre.com.br/{term}`) → HTTP 302 redirect to

| "kindle" (48 URLs) | 48/48 | ✅ Zero blocks | 11 min |  `account-verification` (login required)

| "iphone 15" (492 URLs) | 492/492 | ✅ Zero blocks | 94 min |- **Product pages** (`mercadolivre.com.br/.../p/MLB...`) → same 302 redirect

- **Homepage** (`www.mercadolivre.com.br/`) → HTTP 200 ✅ (only page that works)

### Scaling Estimate- **ML Public API** (`api.mercadolibre.com/sites/MLB/search`) → HTTP 403



- ~10s per product + 15s per search pageML's server returns the header `x-is-search-bot: true` — our IP is flagged as a

- 1 search config with 500 products ≈ 90 minbot at the **server level** before any JavaScript or browser fingerprinting runs.

- Multiple search configs run sequentially (same IP)

---

---

## What We Tested

## Dead Ends (Do Not Retry)

### Test 1: Direct Playwright (current scraper)

| Approach | Result |```

|----------|--------|URL:    https://lista.mercadolivre.com.br/kindle

| Playwright stealth scripts | Block is server-side (HTTP 302 before JS runs) |Result: 302 → account-verification (login page)

| Client Hints headers | Still flagged as bot |Items:  0

| Homepage cookie warming | Cookies don't carry search permission |```

| Tor network | Hard 403 — exit nodes are blocklisted |

| ML Public API (authenticated) | 403 on search; prices not in response |### Test 2: Playwright with enhanced stealth scripts

| Free SOCKS5 proxies | 0/50 worked against ML (datacenter IPs) |Injected: `navigator.webdriver`, `navigator.plugins`, `navigator.languages`,

`window.chrome`, `permissions.query`, canvas fingerprint, WebGL vendor/renderer.

### What Would Make It Faster```

Result: Same 302 → account-verification

Paid residential proxies (~$20/month) would allow parallel scraping by```

splitting URLs across multiple IPs. The proxy infrastructure is already**Conclusion:** Stealth scripts don't help — the block is server-side, not

implemented (`_USE_PROXY`, `ProxyConfig`, `FreeProxyRotator`,client-side fingerprinting.

`PaidProxyRotator`) — just needs `PROXY_ENABLED=true` + credentials.

### Test 3: Homepage first → search via search box

---Visited homepage (works), typed search term, pressed Enter.

```

## Key FilesResult: Still redirected to account-verification

```

| File | Purpose |**Conclusion:** Even human-like navigation flow doesn't help.

|------|---------|

| `src/scrapers/mercado_livre.py` | Scraper with rate-limiting |### Test 4: curl with full Client Hints headers

| `src/scrapers/base/playwright_scraper.py` | Base class with proxy support |Sent all `Sec-CH-UA-*`, `Device-Memory`, `DPR`, `Viewport-Width`, `RTT`,

| `src/config/proxy.py` | Paid proxy config |`Downlink`, `ECT` headers matching a real Chrome browser.

| `src/config/proxy_rotator.py` | Proxy rotation (paid + free) |```

| `src/config/free_proxy.py` | Free SOCKS5 proxy pool |Result: HTTP 302, x-is-search-bot: true

| `src/tests/scrapers/test_mercado_livre.py` | ML scraper tests |```

**Conclusion:** Missing Client Hints is not the trigger.

### Test 5: Homepage cookies + Referer
Visited homepage to collect session cookies (`_d2id`, `_csrf`,
`_mldataSessionId`), then used those cookies + `Referer: mercadolivre.com.br/`
for the search request.
```
Result: HTTP 302 → account-verification
```
**Conclusion:** Session cookies from homepage don't grant search access.

### Test 6: Tor network
```
Search:  HTTP 403 (hard block — worse than direct IP)
Product: HTTP 403
Homepage: HTTP 200 (but extremely slow, timed out downloading)
```
**Conclusion:** ML has a blocklist of Tor exit node IPs. Tor is even more
blocked than our regular IP. **Do not attempt Tor again.**

### Test 7: ML Public API (authenticated)
Registered as ML developer, obtained API credentials.
```
Search endpoint: HTTP 403
```
Additionally, the ML API's search endpoint does **not expose product prices**
in the response — making it useless for a price tracker even if it worked.
**Do not attempt ML API again.**

### Test 8: account-verification page analysis
When Playwright follows the redirect, the page shows:
```
"Olá! Para continuar, acesse sua conta"
(Hello! To continue, sign in to your account)
- "Sou novo" (I'm new)
- "Já tenho conta" (I already have an account)
```
This is a **mandatory login page**, not a solvable JS challenge (unlike
Estante Virtual's Radware Bot Manager which Playwright could solve).

---

## Confirmed Dead Ends (DO NOT RETRY)

| Approach | Why it fails | Risk |
|---|---|---|
| **Playwright stealth scripts** | Block is server-side (HTTP 302 before JS) | None, just doesn't work |
| **Client Hints headers** | `x-is-search-bot` still returned | None |
| **Homepage cookie warming** | Cookies don't carry search permission | None |
| **Search box interaction** | Same redirect after search submit | None |
| **Tor network** | Hard 403 block on exit nodes | None |
| **ML Public API (authed)** | 403 on search; no prices in response | None |
| **Logged-in Playwright** | Account would get banned | **Account ban risk** |
| **Google Cache/indirect** | Stale price data; Google blocks scraping too | Unreliable |

---

## How ML's Anti-Bot Works

### Detection Layer: Server-Side IP Reputation

ML uses **CloudFront** (AWS) as CDN with a server called **Tengine** behind it.
The decision to block happens at the **HTTP level**:

1. Request arrives at ML's edge (CloudFront)
2. Server checks IP reputation database
3. If flagged → HTTP 302 to `account-verification` (or HTTP 403 for known
   proxy/VPN/Tor IPs)
4. Response includes `x-is-search-bot: true` header

### What triggers the flag

- **Datacenter/cloud IPs** — IPs from AWS, GCP, Azure, DigitalOcean, Hetzner,
  OVH, etc. are automatically flagged
- **VPN exit nodes** — commercial VPN IPs are known and blocked
- **Tor exit nodes** — publicly listed, hard-blocked (403 instead of 302)
- **Residential IPs with suspicious patterns** — too many requests, odd timing

### What gets through

- **Clean residential IPs** — ISP-assigned home/mobile connections
- **Logged-in sessions** — authenticated users from any IP (but scraping would
  get the account banned)

### Key observation

The **homepage works** from any IP because ML wants bots to see it (SEO).
But **search and product pages** require either authentication or a clean
residential IP.

---

## Viable Solution: Residential Proxy

### Why this works

Residential proxy services route traffic through real ISP-assigned IPs from
actual homes/devices. ML cannot distinguish these from regular users without
behavioral analysis (which Playwright stealth handles).

### Requirements

1. **Proxy service** with **Brazilian residential IPs** (ML is `.com.br`)
2. **Rotating IPs** — different IP per request/session to avoid rate limits
3. **HTTPS support** — ML is HTTPS-only
4. **SOCKS5 or HTTP CONNECT** — Playwright supports both

### Recommended services (by reputation)

| Service | BR IPs | Pricing | Notes |
|---|---|---|---|
| **Bright Data** | Yes | ~$8.40/GB | Largest pool, ML-tested |
| **Oxylabs** | Yes | ~$8/GB | Good API, reliable |
| **SmartProxy** | Yes | ~$7/GB | Budget-friendly |
| **ScraperAPI** | Yes | Pay per request | Handles rotation automatically |
| **IPRoyal** | Yes | ~$3.50/GB | Cheapest, smaller pool |

### Estimated cost

For our use case (search + product pages for a few terms):
- Search: ~5 pages × 200KB = ~1MB per search term
- Products: ~50 products × 300KB = ~15MB per search term
- **~16MB per search term, ~$0.13 per run** (at $8/GB)
- Monthly with 5 terms, daily runs: **~$20/month**

---

## Implementation Plan

### Step 1: Add proxy support to `PlaywrightScraper`

Playwright natively supports proxies in `browser.launch()`:

```python
browser = await pw.chromium.launch(
    headless=True,
    proxy={
        "server": "http://proxy.example.com:8080",
        "username": "user",
        "password": "pass",
    }
)
```

Or per-context (allows rotation):
```python
context = await browser.new_context(
    proxy={
        "server": "http://proxy.example.com:8080",
        "username": "user",
        "password": "pass",
    }
)
```

### Step 2: Environment configuration

```env
# .env or docker-compose environment
PROXY_SERVER=http://gate.smartproxy.com:7000
PROXY_USERNAME=user
PROXY_PASSWORD=pass
PROXY_ENABLED=true
```

### Step 3: Selective proxy usage

Only ML needs the proxy — OLX, Enjoei, and Estante Virtual work fine without it.
The proxy should be opt-in per scraper:

```python
class MercadoLivreScraper(PlaywrightScraper):
    _USE_PROXY = True  # Only this scraper needs it
```

### Step 4: Test and validate

1. Sign up for a proxy service (start with trial/minimum plan)
2. Test with `curl --proxy` first
3. Test with Playwright proxy config
4. Validate search returns results
5. Validate product pages load
6. Run full live test

---

## Implementation Status (2025-07-25)

Proxy support is **fully implemented and tested** on branch `feature/proxy-support`.

### What was done

| Component | File | Change |
|---|---|---|
| Proxy config module | `src/config/proxy.py` | `ProxyConfig` dataclass + `load_proxy_config()` from env vars |
| Base scraper | `src/scrapers/base/playwright_scraper.py` | `_USE_PROXY` flag, proxy injection in `_build_context()` |
| ML scraper | `src/scrapers/mercado_livre.py` | `_USE_PROXY = True` (only scraper that needs it) |
| Docker config | `docker-compose.yml` | `PROXY_*` env vars on `scraper` and `celery-beat` services |
| Env example | `.env.example` | Proxy configuration section added |
| Tests | 3 test files | 20 new tests (11 config + 7 playwright + 2 ML) |

### Test results

- `src/tests/config/test_proxy.py` — **11/11 passed** ✅
- `src/tests/scrapers/test_playwright_scraper.py` — **24/24 passed** ✅
- `src/tests/scrapers/test_mercado_livre.py` — **45/45 passed** ✅
- **Full suite: 280/280 passed** ✅

### How to activate

```bash
# In .env or docker-compose environment:
PROXY_ENABLED=true
PROXY_SERVER=http://gate.smartproxy.com:7000  # or your provider
PROXY_USERNAME=your_username
PROXY_PASSWORD=your_password
```

### Recommended proxy providers (Brazilian residential IPs)

- **Smartproxy** — BR geo-targeting, ~$7/GB
- **Bright Data** — largest pool, ~$8/GB
- **IPRoyal** — budget option, ~$5/GB
- **Oxylabs** — enterprise-grade, ~$10/GB

Start with a trial/minimum plan, test with `test_scrapers_live.py`.

---

## File References

- **Scraper code:** `scrapers/src/scrapers/mercado_livre.py`
- **Base class:** `scrapers/src/scrapers/base/playwright_scraper.py`
- **Proxy config (paid):** `scrapers/src/config/proxy.py`
- **Free proxy pool:** `scrapers/src/config/free_proxy.py`
- **Proxy rotator:** `scrapers/src/config/proxy_rotator.py`
- **Tests (ML):** `scrapers/src/tests/scrapers/test_mercado_livre.py`
- **Tests (proxy config):** `scrapers/src/tests/config/test_proxy.py`
- **Tests (free proxy):** `scrapers/src/tests/config/test_free_proxy.py`
- **Tests (rotator):** `scrapers/src/tests/config/test_proxy_rotator.py`
- **Tests (base scraper):** `scrapers/src/tests/scrapers/test_playwright_scraper.py`
- **Live test:** `scrapers/test_scrapers_live.py`
- **Celery tasks:** `scrapers/src/celery/tasks.py`
- **Docker config:** `docker-compose.yml` (PROXY_* env vars)
- **Env example:** `.env.example`

---

## Timeline

| Date | What happened |
|---|---|
| Early sessions | ML scraper created with Playwright, returned 0 results |
| PR #28 | Batch processing fixes — ML still 0 results |
| 2026-04-08 | Full investigation: server-side IP block confirmed |
| 2026-04-08 | Tor tested — hard 403, confirmed blocked |
| 2026-04-08 | All alternatives evaluated, residential proxy chosen |
| 2026-04-08 | Proxy support implemented and merged (PR #30) |
| 2026-04-08 | Re-tested: single request still blocked — confirmed IP-level, not rate-based |
| 2026-04-08 | Free SOCKS5 proxy rotation implemented (feature/free-proxy-rotation) |
| 2026-04-08 | SOCKS5 validated via `requests` (~5–11% work against httpbin) |
| 2026-04-08 | **SOCKS5 vs ML via Playwright: 0/50** — ML blocks datacenter IPs regardless of protocol |
| 2026-04-08 | **KEY DISCOVERY:** IP block is **temporary** (hours, not days). Direct access works again |
| 2026-04-08 | Direct Playwright (no proxy): **50 items found**, product scrape OK |
| 2026-04-08 | **New strategy:** gentle rate-limited scraping instead of proxy rotation |
| 2026-04-09 | **Threshold experiment:** ML blocks on **2nd search page visit** (page 2 at 3s delay) |
| 2026-04-09 | **Insight:** Block expires in ~15 min, but 2nd visit immediately re-triggers |
| 2026-04-09 | **Bug fix:** `_scrape_with_current_proxy` no longer calls `start()`/`stop()` per URL |
| 2026-04-09 | **Bug fix:** `scrape_batch` now has configurable delay (env `SCRAPE_BATCH_DELAY`, default 3s) |
| 2026-04-09 | **321/321 tests passing** after all fixes |
| 2026-04-09 | **🎉 EXPERIMENT SUCCESS:** 48/48 product pages scraped, ZERO blocks (10s delay + shuffle + rotate/5) |
| 2026-04-09 | Implemented rate-limiting in MercadoLivreScraper (`_PRODUCT_SCRAPE_DELAY=10`, `_MAX_SEARCH_PAGES=1`, `_SHUFFLE_URLS=True`, `_CONTEXT_ROTATION_INTERVAL=5`) |
| 2026-04-09 | Moved rate-limiting from `scrape_batch` (generic) into scraper (per-site), URL shuffle via `_SHUFFLE_URLS` flag |
| 2026-04-09 | Rewrote `ml_ip_monitor.py` to use `curl` (doesn't burn Playwright visits) |
| 2026-04-09 | **331/331 tests passing** (10 new rate-limiting tests) |
| 2026-04-09 | **Search experiment:** 15s delay → 5 pages / 274 URLs, zero blocks |
| 2026-04-09 | **🎉 FULL VALIDATION:** "iphone 15" — 11 search pages → 492 URLs → **492/492 products scraped, ZERO blocks** (94 min) |
| 2026-04-09 | Updated `_MAX_SEARCH_PAGES` from 1 → 20, added `_SEARCH_PAGE_DELAY=15.0` |
| 2026-04-09 | **291 tests passing** after final updates |

---

## Key Discovery: The Block is Temporary

After hours of being blocked, the IP was automatically unblocked:

```
# Before (blocked):
URL: https://www.mercadolivre.com.br/gz/account-verification?go=...
Blocked: True, Items: 0

# After waiting ~4-6 hours:
URL: https://lista.mercadolivre.com.br/kindle
Blocked: False, Items: 50
```

**This changes everything.** The block is not permanent — it's ML's response
to aggressive scraping (many requests in rapid succession). If we scrape
gently with proper delays, we may never trigger the block at all.

### What triggers the block

Evidence from our sessions:

| Scenario | Result |
|---|---|
| Single search page load (1st visit after unblock) | ✅ Works — 50 items |
| 2nd search page visit (3s delay from 1st) | 🔴 Blocked immediately |
| Same IP after ~15 min wait | ✅ Unblocked automatically |
| 2nd visit after the 15 min unblock | 🔴 Blocked again (pattern repeats) |
| 50+ product scrapes in fast sequence | 🔴 Eventually blocked |
| Same IP after 4-6h wait | ✅ Unblocked automatically |
| Free SOCKS5 proxy (datacenter IP) | 🔴 Always blocked (IP reputation) |

**Critical finding:** ML's threshold is **extremely aggressive** — it blocks
on the **2nd request** with short delays (3s). However, with a **15s delay**
between requests, 11+ consecutive search pages pass without any block.
The key is the **timing pattern**, not the request count.

**Implication for our strategy:** With 15s delay between search pages and 10s
delay between product pages (plus shuffle + context rotation), we can scrape
hundreds of products in a single session. Validated: **492/492 products, zero blocks.**

### What doesn't work

| Approach | Result | Why |
|---|---|---|
| Free HTTP proxies | 0/240 passed | Datacenter IPs, blocked on sight |
| Free SOCKS5 proxies | 0/50 vs ML | Same datacenter IPs, protocol doesn't help |
| Paid residential proxies | Would work, ~$20/mo | Rejected (cost) |

**SOCKS5 was NOT the silver bullet.** The earlier success (~5% via `requests`)
was only against `httpbin.org` for validation. Against ML itself via Playwright,
all 50 validated SOCKS5 proxies were either blocked (32%) or errored (68%).

---

## Execution Plan: Gentle Rate-Limited Scraping

### The Idea

Instead of trying to disguise our IP with proxies, **be a polite scraper**:
make fewer requests, space them out, and stay under ML's detection threshold.

### Volume Estimation

Typical ML scraping workflow per search config:

```
PHASE 1 — Search (collecting product URLs)
├── Page 1: 50 product URLs    → 1 request
├── Page 2: 50 product URLs    → 1 request
├── Page 3: 50 product URLs    → 1 request
├── Page 4: 50 product URLs    → 1 request
├── Page 5: 50 product URLs    → 1 request (max_pages default)
└── Total: ~250 URLs, 5 requests

PHASE 2 — Scrape (visiting each product page)
├── New URLs only (skip existing in DB)
├── First run: ~250 product page requests
├── Subsequent runs: ~10-30 new products
└── Each product: 1 request

TOTAL PER SEARCH CONFIG (first run): ~255 requests
TOTAL PER SEARCH CONFIG (daily):     ~15-35 requests
```

The Celery task flow:
1. `run_scraper_search` → dispatches `run_search` per active source website
2. `run_search` → calls `scraper.search()` (5 pages) → dispatches `process_urls_list`
3. `process_urls_list` → splits into batches of 20 → dispatches `scrape_batch` per chunk
4. `scrape_batch` → calls `scraper.scrape_product(url)` for each URL in batch

**The danger zone is Phase 2** — scraping 250 product pages in rapid sequence.
With batches of 20 and no delay between requests, that's 250 requests in ~5 min.

### Phase 1: Measure the Threshold (Experiment)

**Goal:** Find exactly how many requests at what speed trigger the block.

#### Experiment design

```
Test A: Search pages only (no product scrapes)
  - Load 1 search page every 3s → count until blocked
  - Repeat with 5s, 10s delays

Test B: Product pages only
  - Scrape 1 product page every 2s → count until blocked
  - Repeat with 5s, 10s, 15s delays

Test C: Mixed (realistic workflow)
  - 5 search pages (3s delay between each)
  - Then N product pages (Xs delay between each)
  - Find max N and min X
```

#### Expected output

A table like:

| Delay (seconds) | Max requests before block | Total time |
|---|---|---|
| 0s | ~20-30? | ~1 min |
| 2s | ~50? | ~2 min |
| 5s | ~100? | ~8 min |
| 10s | ~250? | ~42 min |
| 15s | unlimited? | ~63 min |

### Phase 2: Implement Rate-Limiting

Based on Phase 1 data, add configurable delays:

```python
class MercadoLivreScraper:
    # Delay between search result pages
    _SEARCH_PAGE_DELAY: float = 3.0      # seconds

    # Delay between individual product page scrapes
    _PRODUCT_SCRAPE_DELAY: float = 10.0   # seconds (TBD from experiment)

    # New browser context every N product scrapes
    _CONTEXT_ROTATION_INTERVAL: int = 20  # requests
```

#### Where delays get added

1. **Search pagination** (`_search_with_current_proxy`):
   - Already has `await asyncio.sleep(1.0)` between pages
   - Increase to `_SEARCH_PAGE_DELAY` (3-5s)

2. **Product scraping** (`_scrape_with_current_proxy`):
   - Currently no delay between product scrapes
   - Add `_PRODUCT_SCRAPE_DELAY` before each scrape
   - This is the main change — the `scrape_batch` Celery task calls
     `scraper.scrape_product(url)` in a loop with no pause

3. **Context rotation** (new):
   - Close and reopen browser context every N requests
   - Fresh cookies/session = looks like a new visitor
   - Prevents ML from building a behavior profile on a single session

4. **Backoff on warning signs**:
   - If a request takes unusually long (>10s) → possible throttling
   - If we see a captcha/challenge page → backoff 60s
   - If blocked → stop completely, report to Celery as "rate_limited"

### Phase 3: Proxy as Fallback Safety Net

The proxy rotation code we built is **kept as-is** (321 tests passing).
It serves as a fallback layer:

```
Request flow:
  1. Try with direct IP (no proxy, with delays)
  2. If blocked → try proxy rotation (if available)
  3. If all proxies blocked → stop and report "rate_limited"
```

- **Paid proxy** (PROXY_ENABLED=true): Always works, use if budget allows
- **Free SOCKS5 pool**: Unlikely to help with ML but costs nothing to try
- **No proxy available**: Respect the block, retry next Celery schedule

The `_ProxyBlockedError` → retry loop already handles this gracefully.

### Success Criteria

| Metric | Target | Result |
|---|---|---|
| Search (1 page) | Returns ~50 URLs without block | ✅ **48 URLs** |
| Product scrape (48 URLs) | Completes without block | ✅ **48/48 scraped** |
| Total time per search config | < 60 minutes | ✅ **~11 min** |
| No IP block after full run | IP still clean for next run | ⚠️ Unknown (needs Celery test) |
| Celery integration | Works with existing task flow | ✅ No architecture changes |

---

## Experiment Results (2026-04-09)

### Search Page Threshold

| Delay | Pages loaded | URLs | Result |
|---|---|---|---|
| 3s | 1 (50 links) | 50 | 🔴 **Blocked on page 2** |
| 15s | 5 pages | 274 | ✅ **Zero blocks** |
| 15s | 11 pages | 492 | ✅ **Zero blocks** (part of full run) |

**Conclusion:** 15s between search pages is safe for 11+ pages. The old 3s
delay triggered a block on page 2. With 15s, all pages load successfully.

### Product Page Threshold

| Term | Strategy | Delay | Products | Result | Time |
|---|---|---|---|---|---|
| kindle | shuffle + rotate/5 | 10s | **48/48** | ✅ ZERO blocks | 11 min |
| iphone | shuffle + rotate/5 | 10s | **48/48** | ✅ ZERO blocks | 9 min |
| **iphone 15** | **shuffle + rotate/5** | **10s** | **492/492** | ✅ **ZERO blocks** | **94 min** |

**Conclusion:** Product pages are very tolerant. 10s delay with shuffle and
context rotation every 5 requests works perfectly — even at 492 products.

### Full Pipeline Validation ("iphone 15")

The definitive test: search all pages + scrape all products in one run.

```
Search phase:   11 pages → 492 URLs collected (204s, 15s delay between pages)
Product phase:  492/492 scraped (5459s, 10s delay + shuffle + rotate/5)
Total time:     5673s (~94 min)
Blocks:         ZERO
```

### All Experiment Runs (ml_experiment_results.json)

| # | Test | Term | Delay | Strategy | Result | Time |
|---|------|------|-------|----------|--------|------|
| 1 | search | kindle | 3s | — | 🔴 Blocked page 2 | 11s |
| 2 | product | kindle | 10s | shuffle+rot/5 | 🔴 Blocked (IP burned) | 6s |
| 3 | product | kindle | 10s | shuffle+rot/5 | 🔴 Blocked (IP burned) | 6s |
| 4 | product | kindle | 10s | shuffle+rot/5 | ✅ **48/48** | 656s |
| 5 | product | iphone | 10s | shuffle+rot/5 | ✅ **48/48** | 542s |
| 6 | search | iphone | 15s | — | ✅ **5pp / 274 URLs** | 74s |
| 7 | **product** | **iphone 15** | **10s** | **shuffle+rot/5** | ✅ **492/492** | **5673s** |

---

## Current Implementation Status

### Production configuration (MercadoLivreScraper)

```python
_MAX_SEARCH_PAGES = 20           # Validated: 11 pages OK with 15s delay
_SEARCH_PAGE_DELAY = 15.0        # Seconds between search pages
_PRODUCT_SCRAPE_DELAY = 10.0     # Seconds between product scrapes
_JITTER_FACTOR = 0.2             # ±20% randomness on all delays
_CONTEXT_ROTATION_INTERVAL = 5   # Fresh browser context every 5 requests
_SHUFFLE_URLS = True             # Randomize URL order (anti-sequential)
```

### Already done (feature/free-proxy-rotation branch)

| Component | File | Status |
|---|---|---|
| Free proxy pool | `src/config/free_proxy.py` | ✅ Created (16 tests) |
| Proxy rotator | `src/config/proxy_rotator.py` | ✅ Created (18 tests) |
| Base scraper integration | `src/scrapers/base/playwright_scraper.py` | ✅ Updated |
| ML block detection | `src/scrapers/mercado_livre.py` | ✅ `_is_blocked()` + retry loop |
| ML proxy rotation | `src/scrapers/mercado_livre.py` | ✅ `_ProxyBlockedError` + retry |
| **Search rate-limiting** | `src/scrapers/mercado_livre.py` | ✅ 15s delay between pages |
| **Product rate-limiting** | `src/scrapers/mercado_livre.py` | ✅ 10s delay + jitter |
| **URL shuffle** | `src/celery/tasks.py` | ✅ Via `_SHUFFLE_URLS` flag |
| **Context rotation** | `src/scrapers/mercado_livre.py` | ✅ New context per scrape |
| **IP monitor** | `ml_ip_monitor.py` | ✅ curl-based (doesn't burn visits) |
| **Threshold experiment** | `ml_threshold_experiment.py` | ✅ Full validation (492/492) |
| Test suite | All test files | ✅ **291 passed** |

### Still to do

| Task | Priority | Notes |
|---|---|---|
| Live validation with Celery | Medium | Full end-to-end run via Celery task pipeline |
| Multiple search terms | Low | Test running consecutive search configs |

### Recently fixed

| Bug | Fix | File |
|---|---|---|
| `_scrape_with_current_proxy` called `start()`/`stop()` per URL | Removed `stop()` — browser now reused across batch | `mercado_livre.py` |
| `scrape_batch` had no delay between requests | Added `time.sleep(SCRAPE_BATCH_DELAY)` (default 3s, env-configurable) | `tasks.py` |
| Threshold experiment's `--check` consumed the "free" 1st visit | Removed pre-flight check from test runs | `ml_threshold_experiment.py` |

---