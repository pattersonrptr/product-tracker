# 🏴‍☠️ Garimpei — Product Roadmap

> **Garimpei** = Opportunity Hunter for Brazilian Marketplaces
>
> Development name: `product-tracker`
>
> Target audience: resellers/flippers who buy cheap (OLX, ML, Enjoei, etc.)
> and resell at a margin. Option C (reseller tool) with a gateway into
> D (pricing intelligence for marketplace sellers).

---

## What Already Exists (June 2025)

### ✅ Backend (FastAPI)

- JWT auth with refresh tokens
- Roles: admin, staff, regular
- Full CRUD: Products, Price History, Source Websites, Search Configs, Execution Logs
- JSON:API compliant
- 486+ tests

### ✅ Scrapers (Celery + Playwright)

- 4 platforms: OLX, Mercado Livre, Enjoei, Estante Virtual
- Celery Beat with dynamic scheduler (syncs configs via API)
- ML rate-limiting validated (492/492, zero blocks)
- Proxy infrastructure ready (paid + free rotation with fallback)
- 291+ tests

### ✅ Frontend (React 19 + Vite + MUI)

- Product listing with pagination, filters, sorting
- Price history charts (Recharts)
- Search config CRUD
- Source website CRUD
- User management
- JWT auth with interceptors

### ✅ Infrastructure

- Docker Compose (web, scraper, celery-beat, flower, db, redis, frontend)
- GitHub Actions CI (lint + test: backend, scrapers, frontend)
- All 4 scrapers tested via Docker with Celery

### ❌ What Does NOT Exist Yet

- "Price Alert" / "Watch" concept (keyword + max price → notification)
- Notifications (email, push, WhatsApp)
- Smart dashboard ("Your Searches" + "Opportunities")
- Admin area
- More scrapers (Shopee, Amazon BR)
- Landing page / onboarding
- Freemium model (plans, limits)
- Link between SearchConfig and results (currently disconnected entities)

---

## Frontend Assessment — Keep and Evolve, Don't Rewrite

> **Verdict:** ~70% of the frontend is reusable infrastructure. The CRUD pages
> become the admin section almost as-is. Only 2–3 new pages need to be built
> on top of the existing foundation.

### ✅ Keep As-Is (production-quality infrastructure)

| Layer | Files | What It Does |
|-------|-------|-------------|
| API client | `api/client.ts` | Axios with JWT auto-refresh, 401 interceptor, single in-flight refresh + queue |
| JSON:API layer | `api/jsonapi.ts` | `unwrapSingle`, `unwrapCollection`, `wrapPayload` — hides the JSON:API envelope |
| Auth context | `context/AuthContext.tsx` | JWT decode, roles (staff/superuser), session expiry, localStorage |
| Services | `services/*.ts` | snake_case→camelCase mapping, typed `PaginatedResult<T>` |
| Types | `types/*.ts` | Domain types per resource, barrel export |
| Generic hook | `hooks/usePaginatedResource.ts` | One hook for all paginated listings — avoids duplication |
| Layout shell | `components/layout/*` | Header, collapsible Sidebar, Footer, Outlet pattern |
| Reusable components | `components/common/*` | `GenericFormModal`, `ConfirmationDialog`, `PageHeader` |
| Build tooling | `vite.config.ts`, `tsconfig.*` | Vite 7, path aliases (`@/`), Vitest + jsdom, ESLint |

### ♻️ Repurpose (existing pages → admin section)

| Current Page | Current Path | Future Path | Changes Needed |
|-------------|-------------|-------------|----------------|
| ProductsPage | `/products` | `/admin/products` | Move route, add admin guard |
| SearchConfigsPage | `/search-configs` | `/admin/search-configs` | Move route, add admin guard |
| SourceWebsitesPage | `/source-websites` | `/admin/source-websites` | Move route, add admin guard |
| UsersPage | `/users` | `/admin/users` | Already behind `isStaff` check |
| ProductDetailPage | `/products/:id` | `/products/:id` | Keep as-is, add "🎯 Opportunity" tag |

### 🆕 Build New (Garimpei user-facing pages)

| New Page | Path | What It Does | Reuses From Existing |
|----------|------|-------------|---------------------|
| **Dashboard** | `/dashboard` | Cards: active alerts, recent opportunities, next checks | Layout, formatters, auth |
| **My Alerts** | `/alerts` | PriceAlert CRUD: keyword + max price + sources | `GenericFormModal`, `usePaginatedResource`, `DataGrid` |
| **Alert Detail** | `/alerts/:id` | Products found by this alert, sorted by price | `DataGrid`, price chart from ProductDetailPage |
| **Landing Page** | `/` | Public page explaining Garimpei (Phase 2) | Theme, MUI components |

### 🆕 New Service Files Needed

| File | Purpose |
|------|---------|
| `services/priceAlertService.ts` | CRUD for `/price-alerts` endpoint |
| `services/dashboardService.ts` | Fetch `GET /dashboard/summary` |
| `types/priceAlert.ts` | `PriceAlert`, `PriceAlertCreatePayload`, `PriceAlertUpdatePayload` |
| `hooks/useDashboardSummary.ts` | Fetch and cache dashboard data |

### 📊 Effort Estimate

| Category | Lines of Code | Effort |
|----------|--------------|--------|
| Reusable infrastructure (keep) | ~1,200 | 0 — already done |
| Existing pages (move to admin) | ~1,700 | ~1h — route changes only |
| New pages + services + types | ~400–600 | ~2–3 days |
| Sidebar reorganization | ~50 | ~30min |
| **Total new frontend work** | **~500** | **~3 days** |

### 🔧 Sidebar Navigation Plan

```text
── User Section ──
  📊 Dashboard        → /dashboard
  🔔 My Alerts        → /alerts
  📦 Products         → /products

── Admin Section ── (staff/superuser only)
  👥 Users            → /admin/users
  🔍 Search Configs   → /admin/search-configs
  🌐 Source Websites  → /admin/source-websites
```

---

## Phase 1 — Core "Opportunity Hunter" (4–5 weeks)

**Goal:** transform product-tracker into a product that delivers real value —
alert when a product appears below the target price.

### 1.1 — Price Alert / Watch (backend)

> **The core feature of Garimpei.**

- [ ] New entity `PriceAlert`

  ```text
  id, user_id, search_term, max_price, source_website_ids[],
  is_active, frequency_minutes, last_triggered_at,
  created_at, updated_at
  ```

- [ ] Relationship: `PriceAlert` 1↔N `Product` (products found by this alert)
- [ ] Full CRUD: `POST/GET/PATCH/DELETE /price-alerts`
- [ ] Use case: `EvaluatePriceAlertUseCase` — when a scraper saves a product with
  price ≤ max_price, mark as "opportunity" and fire notification
- [ ] Alembic migration for new table
- [ ] Unit + integration tests

### 1.2 — Link SearchConfig → PriceAlert

> Today SearchConfig is generic. It needs a clear link.

- [ ] Each `PriceAlert` automatically creates/reuses a `SearchConfig`
  (matching `search_term` + `source_website_ids`)
- [ ] When the scraper finds products, the system checks all active
  `PriceAlerts` matching that search_term
- [ ] Endpoint: `GET /price-alerts/{id}/products` — products found by
  that alert, sorted by price

### 1.3 — Email Notifications

> SendGrid free tier = 100 emails/day (enough for MVP).

- [ ] Email service (`EmailNotificationService`)
- [ ] Simple HTML template: "🎯 Opportunity! {product} for R${price} on {site}"
- [ ] Celery task integration: `send_price_alert_notification`
- [ ] Backend config: `SENDGRID_API_KEY`, `FROM_EMAIL`
- [ ] Rate limiting: max 1 email per alert per hour (avoid spam)
- [ ] Tests with SendGrid mock

### 1.4 — "My Opportunities" Dashboard (frontend)

> Replace the dumb listing with something that delivers value.

- [ ] New page: **Dashboard** (`/dashboard`) — landing page after login
  - "Active Alerts" card with count and quick link
  - "Recent Opportunities" card (latest products below target price)
  - "Next Checks" card (when each alert is scheduled to run)
- [ ] New page: **My Alerts** (`/alerts`)
  - Price Alert CRUD (create/edit/pause/delete)
  - Form: keyword + max price + select sources
  - Status: active/paused, last check, products found
- [ ] Update `/products` to show "🎯 Opportunity" tag when price ≤ alert threshold
- [ ] Keep `/products/:id` with price chart (already exists)

### 1.5 — Refine the Scraper Flow

> The scraper needs to "close the loop" with alerts.

- [ ] After `save_product` in the scraper, call new endpoint:
  `POST /products/{id}/evaluate-alerts` (or the backend does it automatically
  on product create/update)
- [ ] Backend checks if any active PriceAlert matches that product
- [ ] If yes: mark product as opportunity + enqueue email

---

## Phase 2 — Presentable Product (5–6 weeks)

**Goal:** polished frontend, more scrapers, basic admin. Something ready to
show to beta testers.

### 2.1 — Frontend Polish

- [ ] Public landing page (`/`) — explains what Garimpei is, CTA "Create free account"
- [ ] Visual redesign: colors, placeholder logo, consistent typography
- [ ] Mobile responsiveness (MUI helps, but needs testing/adjustments)
- [ ] Onboarding: after signup, wizard "Create your first alert"
- [ ] Friendly empty states ("No alerts created yet. Start now!")

### 2.2 — New Scrapers

- [ ] **Shopee** — high volume, popular among resellers
  - Investigate: public API? Playwright needed? Anti-bot?
- [ ] **Amazon BR** — expectation: aggressive anti-bot (similar or worse than ML)
  - Investigate: headless viable? Proxy needed?
- [ ] For each new scraper:
  - Create class inheriting from `PlaywrightScraper` or `RequestScraper`
  - Register in `ScraperFactory`
  - Add `SourceWebsite` to fixture/seed
  - Tests with mocked HTML

### 2.3 — Admin Area (basic)

- [ ] Route `/admin` protected by `is_superuser`
- [ ] Admin dashboard:
  - Total users, active alerts, products in database
  - Scraper status (last run, success/error) — data from `SearchExecutionLog`
  - Link to Flower (Celery monitoring)
- [ ] User management: activate/deactivate, promote to staff
- [ ] Source website management: enable/disable scrapers

### 2.4 — Backend Improvements

- [ ] Endpoint `GET /dashboard/summary` (aggregated data for dashboard)
- [ ] Endpoint `GET /price-alerts/{id}/opportunities` (matched products)
- [ ] Soft delete on PriceAlerts (preserve history)
- [ ] Pagination on opportunity results
- [ ] Background job: cleanup old products with no associated alert

---

## Phase 3 — Launch & Monetization (3–4 weeks)

**Goal:** go live with a freemium model. Acquire the first 50 users.

### 3.1 — Freemium Model

| Feature | Free | Pro (R$29/mo) | Business (R$79/mo) |
|---------|------|---------------|---------------------|
| Active alerts | 3 | Unlimited | Unlimited |
| Check frequency | 6h | 30min | 15min |
| Price history | 7 days | 90 days | Unlimited |
| Notifications | Email | Email + Push | Email + Push + WhatsApp |
| Sources | 2 | All | All + API access |

- [ ] `Plan` + `Subscription` entities in backend
- [ ] Middleware for limits based on user's plan
- [ ] Payment integration: Stripe or Mercado Pago
- [ ] Plans page in frontend

### 3.2 — WhatsApp Notifications (Business plan)

- [ ] Integrate Evolution API (open source) or Twilio
- [ ] Celery task: `send_whatsapp_notification`
- [ ] Per-user config: verified WhatsApp number

### 3.3 — Production Deployment

- [ ] VPS (Hetzner, Contabo, or DigitalOcean ~R$50-100/mo)
- [ ] Docker Compose in production (simple, no K8s for now)
- [ ] Domain: garimpei.com.br (or similar)
- [ ] HTTPS via Caddy or Traefik
- [ ] Automatic PostgreSQL backups
- [ ] Basic monitoring: Uptime Kuma + logs

### 3.4 — User Acquisition

- [ ] Facebook groups for resellers
- [ ] TikTok: videos showing Garimpei finding opportunities in real time
- [ ] Product Hunt (technical visibility + beta testers)
- [ ] SEO: blog with content like "How to find deals on OLX"

---

## Phase 4 — Evolution (Future)

Ideas for after gaining traction:

- **Pricing intelligence** (Option D): suggest resale price based on
  history + average margin
- **Cross-source price comparison** (same product, different sources)
- **Internal marketplace**: connect buyers and sellers within Garimpei
- **Mobile app** (React Native or PWA)
- **More scrapers**: Facebook Marketplace, Instagram shops, Mercado Shops
- **Machine Learning**: automatically detect opportunities based on
  category price patterns (no manual alert needed)

---

## Time Estimates

Assumptions: ~10h/week, with AI accelerating development.

| Phase | Duration | Outcome |
|-------|----------|---------|
| **Phase 1** — Core | 4–5 weeks | Working product: alerts + email + dashboard |
| **Phase 2** — Polish | 5–6 weeks | Presentable product: landing, admin, +scrapers |
| **Phase 3** — Launch | 3–4 weeks | Live with freemium and first users |
| **Phase 4** — Growth | Ongoing | Evolution based on feedback |

**Total to launch: ~3 months** (12–15 weeks).

---

## Target Data Architecture

```text
User 1───N PriceAlert
              │
              ├── search_term: "iPhone 14"
              ├── max_price: 2500.00
              ├── source_website_ids: [1, 2]  (OLX, ML)
              ├── frequency_minutes: 360      (free plan = 6h)
              └── is_active: true
              │
              └───N Product (found by this alert)
                    │
                    ├── url, title, price, condition...
                    └───N PriceHistory
                          └── price, created_at
```

Main flow:

1. User creates PriceAlert ("iPhone 14", max R$2,500, OLX+ML)
2. System creates/reuses SearchConfig for "iPhone 14" on chosen sources
3. Celery Beat schedules the search based on frequency
4. Scraper runs → finds products → saves via API
5. Backend evaluates: price ≤ R$2,500? → marks as opportunity
6. Celery sends email: "🎯 iPhone 14 for R$1,800 on OLX!"
7. User sees it on the dashboard and rushes to buy

---

## Technical Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Email provider | SendGrid (free tier) | 100 emails/day, good Python SDK, free |
| WhatsApp | Evolution API (future) | Open source, self-hosted |
| Payments | Stripe or MercadoPago | Stripe = more dev-friendly, MP = more BR-native |
| Deploy | VPS + Docker Compose | Simple, cheap, no K8s complexity |
| New scraper base | Playwright | Already the project standard, works well |
| Frontend framework | Keep React + MUI | Already exists, works, don't switch stacks |
