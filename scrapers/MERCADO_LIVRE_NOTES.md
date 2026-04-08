# Mercado Livre Scraper — Investigation Notes

> **Last updated:** 2025-07-25
> **Status:** ⏳ PROXY SUPPORT IMPLEMENTED — awaiting proxy credentials
> **Branch:** `feature/proxy-support` (code ready, needs PROXY_* env vars)

---

## Table of Contents

1. [Problem Summary](#problem-summary)
2. [What We Tested](#what-we-tested)
3. [Confirmed Dead Ends](#confirmed-dead-ends-do-not-retry)
4. [How ML's Anti-Bot Works](#how-mls-anti-bot-works)
5. [Viable Solution: Residential Proxy](#viable-solution-residential-proxy)
6. [Implementation Plan](#implementation-plan)

---

## Problem Summary

The `MercadoLivreScraper` code is **fully functional** — selectors, pagination,
product extraction all work correctly. The problem is **100% network-level**:
Mercado Livre blocks our requests **before any page content is served**.

- **Search pages** (`lista.mercadolivre.com.br/{term}`) → HTTP 302 redirect to
  `account-verification` (login required)
- **Product pages** (`mercadolivre.com.br/.../p/MLB...`) → same 302 redirect
- **Homepage** (`www.mercadolivre.com.br/`) → HTTP 200 ✅ (only page that works)
- **ML Public API** (`api.mercadolibre.com/sites/MLB/search`) → HTTP 403

ML's server returns the header `x-is-search-bot: true` — our IP is flagged as a
bot at the **server level** before any JavaScript or browser fingerprinting runs.

---

## What We Tested

### Test 1: Direct Playwright (current scraper)
```
URL:    https://lista.mercadolivre.com.br/kindle
Result: 302 → account-verification (login page)
Items:  0
```

### Test 2: Playwright with enhanced stealth scripts
Injected: `navigator.webdriver`, `navigator.plugins`, `navigator.languages`,
`window.chrome`, `permissions.query`, canvas fingerprint, WebGL vendor/renderer.
```
Result: Same 302 → account-verification
```
**Conclusion:** Stealth scripts don't help — the block is server-side, not
client-side fingerprinting.

### Test 3: Homepage first → search via search box
Visited homepage (works), typed search term, pressed Enter.
```
Result: Still redirected to account-verification
```
**Conclusion:** Even human-like navigation flow doesn't help.

### Test 4: curl with full Client Hints headers
Sent all `Sec-CH-UA-*`, `Device-Memory`, `DPR`, `Viewport-Width`, `RTT`,
`Downlink`, `ECT` headers matching a real Chrome browser.
```
Result: HTTP 302, x-is-search-bot: true
```
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
- **Proxy config:** `scrapers/src/config/proxy.py`
- **Tests:** `scrapers/src/tests/scrapers/test_mercado_livre.py`
- **Proxy tests:** `scrapers/src/tests/config/test_proxy.py`
- **Live test:** `scrapers/test_scrapers_live.py`
- **Docker config:** `docker-compose.yml` (PROXY_* env vars)
- **Env example:** `.env.example`

---

## Timeline

| Date | What happened |
|---|---|
| Early sessions | ML scraper created with Playwright, returned 0 results |
| PR #28 | Batch processing fixes — ML still 0 results |
| 2025-07-25 | Full investigation: server-side IP block confirmed |
| 2025-07-25 | Tor tested — hard 403, confirmed blocked |
| 2025-07-25 | All alternatives evaluated, residential proxy chosen |
| 2025-07-25 | Proxy support implemented in `feature/proxy-support` branch |
| Next | Sign up for proxy service → configure env vars → test live |
