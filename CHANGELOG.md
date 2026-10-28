# Development Notes & History

## Unreleased — data provenance and credibility pass
- Amazon sample: dates, station depot, service times and package volumes are read from the file; values the file lacks (distances, durations, actual visit order, driver) stay unknown instead of being filled with constants.
- The bundled Mendeley-schema CSV is renamed `data/mendeley_synthetic_fixture.csv` and ingested with `is_synthetic=True`; dataset licenses are recorded per dataset (Amazon: CC BY-NC 4.0).
- One definition of "material deviation" and one sequence-similarity metric (Kendall tau) shared by ingestion, API and evaluation.
- Optimizer: no San Francisco default depot; savings are measured against the planned order with the same distance model, and only when the data has a plan.
- Frontend: removed hard-coded risk scores, mock KPIs and fallback numbers; data-mode labels come from `/health`; Optimization and Scenarios pages use real route IDs.
- New `GET /api/v1/risk-scores`, `backend/scripts/train_eval.py` (cross-validated evaluation with baselines), core-algorithm tests, and GitHub Actions CI.
- `DATA_DIR` defaults to the repository's `data/` folder; ingestion only reads file names inside it.

## Initial Consolidation (September 2026)
This repository was initially developed as a collection of localized prototypes and exploratory data analysis notebooks (Nov 2025 - Feb 2026). During this period, the core ML models, data validators, and Google OR-Tools VRP constraints were designed and tested offline.

In September 2026, the project was consolidated, re-architected into a clean Next.js/FastAPI monorepo, and pushed to GitHub. This explains the initial large monolithic commits that scaffold the full build, APIs, and ML models all at once.

## Forward-Looking Commit Convention
Going forward, all work will be tracked incrementally. We adhere to the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` for new features (e.g., `feat: add weather impact to delay predictor`)
- `fix:` for bug fixes
- `docs:` for documentation updates
- `test:` for adding or modifying tests
- `refactor:` for code changes that neither fix a bug nor add a feature
- `ci:` for CI/CD pipeline changes

All future commits should be small, focused, and tested before merging to `main`.
