# Onboarding a new domain team

This is the guide to hand a domain team (Finance, Supply Chain, Commercial,
HR, ...) that wants to build an agentic AI application against enterprise
data using this framework. It assumes the platform team has already run
`databricks bundle deploy` once per environment (see the root README).

## 1. Confirm the framework is deployed

Check with the platform team that these exist in your target environment:

- Unity Catalog: `<catalog>.ontology.*` and `<catalog>.audit.*` schemas
- Lakebase: `ontology_state.*` and `audit.*` schemas
- Databricks Apps: `ontology-api`, `ontology-mcp-server`, `ontology-admin-ui`

## 2. Scaffold your domain

```bash
python templates/new_domain_scaffold.py --domain finance --owner finance-data-eng@yourco.com
```

This creates `templates/domains/finance.yaml` from the template. Fill in:

- **Concepts** — the business terms your agent needs to understand. Start
  small: PRD Sec. 30 Phase 1 targets 50-75 concepts, not your whole domain.
- **Synonyms** — including `PROHIBITED_EQUIVALENCE` entries for terms people
  confuse (e.g. "gross bookings" is NOT "net revenue").
- **Metrics** — one row per certified metric, pointing at a real metric
  view / UC function / trusted SQL asset that must already exist.
- **Dimensions** — key/label columns, allowed operators, whether OBO is required.
- **Business rules** — anything with an `executable_reference`; if a rule
  has no executable reference, it's advisory only and the planner won't
  enforce it.
- **Asset mappings** — the physical tables/views/functions each concept maps to.
- **Test questions** — aim for the 100-gold-question bar from PRD Sec. 30
  Phase 1 before going to production.

Reference the shared enterprise concepts (`ORG.LEGAL_ENTITY`,
`TIME.FISCAL_CALENDAR`, `GEO.COUNTRY`, ...) instead of redefining them —
see PRD Sec. 7.

## 3. Submit for review

```bash
python templates/new_domain_scaffold.py --from-file templates/domains/finance.yaml
```

This inserts everything as `DRAFT` and opens one `SUBMITTED` change request
per concept. Nothing is usable by an agent yet.

## 4. Work the governance workflow

Reviewers (Domain Ontology Steward -> Data Product Owner -> Security Owner,
per PRD Sec. 31) approve each change request in `apps/ontology-admin-ui`.
Once `APPROVED`, the platform team's activation job flips the ontology
version and the concepts become `ACTIVE`.

## 5. Point your agent at the framework

Pick ONE of:

**MCP** (if your agent runtime is MCP-native):
```python
from enterprise_ontology.mcp.tools import OntologyToolkit, resolve_concept, validate_semantic_plan

toolkit = OntologyToolkit.build()
result = await resolve_concept(toolkit, terms=["net revenue"], domain="finance", user_context=ctx)
```
Or connect any MCP client to the deployed `ontology-mcp-server` app URL.

**REST**:
```bash
curl -X POST https://<ontology-api-app-url>/api/v1/ontology/resolve \
  -H "Content-Type: application/json" \
  -d '{"terms": ["net revenue"], "domain": "finance"}'
```

Either way, your agent NEVER:
- queries `ontology.*` or `ontology_state.*` tables directly,
- generates its own SQL without going through `sql_policy.SQLPolicyGateway`,
- resolves a categorical value by string-matching against a raw column.

## 6. Wire up your agent's semantic planner

Use `enterprise_ontology.planner.SemanticPlanner` directly, or replicate its
prompt contract (`planner/prompts.py`) in your own agent framework if you
need a different LLM orchestration layer — the important invariant is that
your agent's LLM step produces a `SemanticPlan` (see `models/plan.py`), not
raw SQL or prose, and that plan is always run through
`planner.SemanticValidator` before compilation.

## 7. Before going to production

Run through the Definition of Done (PRD Sec. 33):

- [ ] Concepts, relationships, synonyms, prohibited equivalences approved
- [ ] Metrics, dimensions, hierarchies defined
- [ ] Rules map to executable assets
- [ ] Physical mappings approved
- [ ] Security scope defined
- [ ] OBO tested
- [ ] Drift detection active (it runs hourly automatically once your
      `asset_mapping` rows exist — no extra setup needed)
- [ ] Gold evaluation passes (`python -m enterprise_ontology.evaluation.gold_runner`)
- [ ] Trace and audit verified in `audit.*`
- [ ] Owners and runbooks assigned
