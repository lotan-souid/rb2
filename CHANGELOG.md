# Changelog

All notable changes to this project will be documented in this file.

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

