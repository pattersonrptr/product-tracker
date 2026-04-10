# Copilot Instructions — product-tracker (Garimpei)

## Project Context

- **Product name:** Garimpei (development name: `product-tracker`)
- **Roadmap:** See `ROADMAP.md` for phases, features and architecture
- **Status:** See `PLAN.md` for current capabilities

## Branching Strategy

- `main` — stable, always passes CI
- Feature branches: `feat/description` (e.g. `feat/phase1-price-alert-entity`)
- Docs branches: `docs/description`
- Fix branches: `fix/description`
- Chore branches: `chore/description`

## Commit Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `ci`, `style`, `perf`

Scopes: `backend`, `frontend`, `scrapers`, `infra`

Examples:
- `feat(backend): add PriceAlert entity and CRUD endpoints`
- `fix(scrapers): handle ML rate-limit timeout gracefully`
- `docs: update ROADMAP with Phase 1 progress`

## Semantic Versioning & Releases

This project uses [Semantic Versioning](https://semver.org/) (SemVer):

```
MAJOR.MINOR.PATCH
```

- **MAJOR** — breaking API changes or incompatible data migrations
- **MINOR** — new features (backward compatible)
- **PATCH** — bug fixes, docs, refactors (backward compatible)

### Release rules
- `feat` commits → bump **MINOR**
- `fix`, `perf`, `refactor` commits → bump **PATCH**
- `BREAKING CHANGE` footer or `!` after type → bump **MAJOR**

### Release process
1. All work merged to `main` via squash-merge PRs
2. Create release with `gh release create vX.Y.Z --generate-notes`
3. Tag follows format: `v0.1.0`, `v0.2.0`, `v1.0.0`
4. Update `CHANGELOG.md` with the release notes

### Current version
- Pre-release: `v0.x.x` (not yet at v1.0.0)
- v1.0.0 will be the first public release (Phase 3 — Launch)

## Changelog

Maintain a `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/):

```markdown
## [Unreleased]
### Added
### Changed
### Fixed
### Removed
```

Every PR should update the `[Unreleased]` section. On release, move entries
to the versioned section.

## CI / Linting

- **Backend:** `poetry run ruff check` + `poetry run ruff format --check` + `poetry run pytest`
- **Scrapers:** `poetry run ruff check` + `poetry run ruff format --check` + `poetry run pytest`
- **Frontend:** `npm run lint` + `npm run test`
- Always use `poetry run ruff` (not global ruff) to match CI version (0.8.6)

## GitHub Workflow

- PRs always target `main`
- Squash merge (clean history)
- Reference issues in PR body: `Closes #34`
- Milestones: Phase 1 — Core, Phase 2 — Polish, Phase 3 — Launch
- Labels: `backend`, `frontend`, `scrapers`, `infra`, `enhancement`, `bug`
