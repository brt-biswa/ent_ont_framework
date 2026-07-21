# jobs/

PRD Sec. 27's suggested repository structure lists `jobs/` as a top-level
directory. In this implementation, job entry points live alongside the rest
of the framework code at `src/enterprise_ontology/jobs/` (bootstrap_uc.py,
bootstrap_lakebase.py) and as `main()` functions in the modules they belong
to (`drift/detector.py`, `cache/l2_lakebase_cache.py`, `evaluation/gold_runner.py`) —
so job logic ships in the same installable wheel as everything else and is
unit-testable the same way.

`databricks.yml` wires each of these up as a scheduled Databricks Job via
`python_wheel_task` entry points (see the `resources.jobs` block):

| Job | Schedule | Entry point |
|---|---|---|
| `ontology_ddl_bootstrap` | on deploy | `enterprise_ontology.jobs.bootstrap_uc` / `bootstrap_lakebase` |
| `ontology_drift_detection` | hourly | `enterprise_ontology.drift.detector:main` |
| `ontology_cache_warm` | every 15 min | `enterprise_ontology.cache.l2_lakebase_cache:warm_main` |
| `ontology_evaluation` | daily 06:00 UTC | `enterprise_ontology.evaluation.gold_runner:main` |

This directory is kept as a placeholder matching the PRD's suggested layout
for anyone who prefers to add environment-specific Databricks notebook
wrappers around those entry points (e.g. for a workspace that mandates
notebook-based job tasks instead of Python wheel tasks).
