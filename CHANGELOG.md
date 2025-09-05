# Changelog

All notable changes to this project will be documented in this file.

## [0.1.1] - 2025-09-05

### Fixed
- Workflow: added missing Workflow States `Pending` and `RevisionsRequired` to fixtures to resolve "Workflow State RevisionsRequired not found" when opening the Development Committee Review workflow.
- Workspace fixtures: removed stale shortcuts/links to removed doctypes/pages (Development Task, Project Approval Committee) to prevent Not Found errors when editing the workspace and after `import-fixtures`.

### Added
- Post‑migration safety: new `after_migrate` hook (`rb.install.after_migrate`) that ensures required Workflow States exist on any site, preventing runtime errors without relying solely on fixture import.
- Committee Review: added `summary` field (Small Text) to `Development Committee Review` DocType.

### Docs
- Updated development spec docs to align with current implementation (removed non‑existent fields like `owner_name` on Lot and `contractor_id` on Development Item).

### Notes
- To apply: run `bench --site <site> migrate` or `bench --site <site> import-fixtures` and then `bench clear-cache`.

## [0.1.0] - 2025-09-05

### Added
- Development module enhancements:
  - Development Price History child table with controller (`development_price_history/*`).
  - Price per sqm calculation based on allocatable total cost and sum of chargeable lot areas.
  - Price lock/unlock with audit history.
  - Recalculate cost allocations to Lots; reflect price and allocated cost on Lot.
  - Default Development Stages (StageA, StageB, Final) and stage totals.
  - Stage Progress Update DocType for tracking progress and expenses.
- Lot fields used for costing pipeline: `chargeable`, `related_project`, `dev_price_per_sqm`, `allocated_dev_cost`, `lot_development_status`.
- Documentation:
  - `rb/docs/development-implementation-report.md` summarizing design and changes.

### Changed
- Development Project logic (`development_project.py/json/js`) to compute totals, handle calculation source, price locking, and cost allocation.

### Fixed
- Fixtures: added `name` to Workflow fixture to prevent KeyError during migrate.

### Migration Notes
- Run: `bench --site <site> migrate` and then `bench --site <site> clear-cache`.
- If existing Lots should be included in costing, ensure `chargeable=1` where applicable.
