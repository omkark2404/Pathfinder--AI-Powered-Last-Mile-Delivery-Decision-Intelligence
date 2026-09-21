# Development Notes & History

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
