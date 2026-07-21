# Enterprise Ontology Framework for Agentic AI

A Databricks-native, reusable **governed meaning layer** that any team's agentic AI
application can call so that agents interpret enterprise data consistently, safely
and explainably — instead of every team re-inventing semantic resolution, dimension
resolution, SQL safety and audit logic on their own.

This repository is the **reference implementation and reusable framework**. Domain
teams (Finance, Supply Chain, Commercial, HR, ...) do **not** fork this repo. They:

1. Deploy this framework once per environment (platform team), via `databricks.yml`.
2. Register their own **domain ontology** (concepts, metrics, dimensions, rules,
   asset mappings) using the template in [`templates/domain_ontology_template.yaml`](templates/domain_ontology_template.yaml).
3. Call the **Ontology MCP server** or **Ontology API** from their own agents —
   they never talk to Unity Catalog or Lakebase directly.

```
Canonical enterprise meaning
        ↓
Governed ontology registry (Unity Catalog Delta tables)
        ↓
Executable semantic assets (metric views, UC functions, certified views)
        ↓
Permission-aware ontology projection
        ↓
Structured LLM planning (this framework)
        ↓
Deterministic value & hierarchy resolution (this framework)
        ↓
Plan validation (this framework)
        ↓
Governed query / tool compilation (this framework)
        ↓
OBO execution
        ↓
Unity Catalog RBAC + ABAC
        ↓
Validated result, evidence and audit
```

## Why this exists

The same business term (customer, active, segment, revenue, priority...) means
different things across systems and teams. Connecting LLMs directly to raw schemas
scales that ambiguity. This framework inserts a governed layer so that:

- The LLM **never invents** enterprise meaning, physical joins, metric formulas,
  categorical values, or SQL — it only *interprets intent* into a structured plan.
- Every physical value, join and metric comes from a governed registry, not a guess.
- Every request is versioned, permission-aware, explainable and auditable.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full runtime sequence and
[`docs/ONBOARDING.md`](docs/ONBOARDING.md) for how a new domain team adopts the
framework in an afternoon.

## Repository layout

```text
enterprise-ontology-framework/
├── databricks.yml                 # Databricks Asset Bundle (deploy everything)
├── src/enterprise_ontology/       # the framework — a pip-installable package
│   ├── models/                    # canonical Pydantic data model (Sec. 21 data model)
│   ├── repositories/              # Unity Catalog + Lakebase data access
│   ├── resolution/                # concept & synonym resolution, context projection
│   ├── dimensions/, hierarchies/  # governed dimension & hierarchy value resolution
│   ├── relationships/             # approved join-path resolution
│   ├── metrics/, rules/           # certified metric & business-rule services
│   ├── mappings/                  # physical asset / document mapping service
│   ├── security/                  # OBO context + RBAC/ABAC enforcement helpers
│   ├── planner/                   # LLM semantic planner (produces structured plans)
│   ├── compiler/                  # deterministic compiler + constrained SQL fallback
│   ├── sql_policy/                # SQL AST allow/deny-list validator (sqlglot)
│   ├── mcp/                       # reusable Ontology MCP server (11 typed tools)
│   ├── cache/                     # L1 in-memory + L2 Lakebase caching
│   ├── audit/                     # audit-trail writer
│   ├── evaluation/                # gold-question evaluation harness
│   └── drift/                     # ontology / mapping / schema drift detection
├── apps/
│   ├── ontology_api/              # Databricks App: REST API (Sec. 20)
│   ├── ontology_mcp_server/       # Databricks App: MCP server (Sec. 11)
│   └── ontology_admin_ui/         # Databricks App: governance / admin UI
├── sql/
│   ├── unity_catalog/             # Delta DDL — the ontology registry + audit tables
│   └── lakebase/                  # Postgres DDL — Lakebase operational-state tables
├── templates/                     # domain-onboarding template + scaffolder script
├── jobs/                          # scheduled jobs: drift detection, cache warm, eval
├── tests/                         # unit tests for compiler / validator / resolvers
└── docs/                          # architecture, onboarding, anti-patterns
```

## Quick start (platform team — one-time deploy)

```bash
databricks bundle validate -t dev
databricks bundle deploy -t dev
```

This creates the `ontology` and `audit` Unity Catalog schemas and tables, the
Lakebase `ontology_state` database, and deploys the three Databricks Apps.

## Quick start (domain team — reuse the framework)

```bash
pip install -e ../enterprise-ontology-framework  # or from an internal index
python templates/new_domain_scaffold.py --domain finance --owner "finance-data-eng"
```

Then call the framework from your own agent:

```python
from enterprise_ontology.mcp.tools import resolve_concept, validate_semantic_plan
from enterprise_ontology.security.obo import UserContext

ctx = UserContext.from_databricks_request(headers)
concepts = await resolve_concept(terms=["net revenue", "EMEA enterprise"], domain="finance", user_context=ctx)
```

No agent should query Unity Catalog tables, generate raw SQL, or resolve dimension
values on its own. That is exactly the duplicated effort this framework removes.
