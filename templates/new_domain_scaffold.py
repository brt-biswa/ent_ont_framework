#!/usr/bin/env python3
"""New-domain onboarding scaffolder — turns a filled-in
templates/domain_ontology_template.yaml into DRAFT rows in the ontology
registry, plus one governance change request per concept, so nothing a
domain team submits ever becomes ACTIVE without going through Domain Review
-> Data Review -> Security Review -> Approved (PRD Sec. 22).

Usage:
    python templates/new_domain_scaffold.py --domain finance --owner finance-data-eng@yourco.com
        (creates an empty templates/domains/finance.yaml for you to fill in)

    python templates/new_domain_scaffold.py --from-file templates/domains/finance.yaml
        (loads a filled-in file and submits it)

This script talks to the framework the same way any other consumer does —
through UnityCatalogOntologyRepository — it has no special/elevated access
path. A human still has to approve every DRAFT before it is usable.
"""
from __future__ import annotations

import argparse
import shutil
import sys
import uuid
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = REPO_ROOT / "templates" / "domain_ontology_template.yaml"
DOMAINS_DIR = REPO_ROOT / "templates" / "domains"


def scaffold_new_domain_file(domain: str, owner: str) -> Path:
    DOMAINS_DIR.mkdir(parents=True, exist_ok=True)
    target = DOMAINS_DIR / f"{domain}.yaml"
    if target.exists():
        print(f"{target} already exists — not overwriting.")
        return target

    shutil.copy(TEMPLATE_PATH, target)
    text = target.read_text()
    text = text.replace("domain: finance", f"domain: {domain}", 1)
    text = text.replace('steward: "finance-data-eng@yourco.com"', f'steward: "{owner}"', 1)
    target.write_text(text)
    print(f"Created {target} — fill in your concepts/metrics/dimensions, then re-run with --from-file")
    return target


def submit_domain(yaml_path: Path) -> None:
    from enterprise_ontology.repositories.unity_catalog_repository import UnityCatalogOntologyRepository
    from enterprise_ontology.config import get_settings

    spec = yaml.safe_load(yaml_path.read_text())
    repo = UnityCatalogOntologyRepository(get_settings())

    domain = spec["domain"]
    print(f"Submitting domain '{domain}' from {yaml_path} ...")

    repo._query(  # noqa: SLF001
        """INSERT INTO domain_registry (domain, description, steward, council_reviewed, shared_concepts_referenced)
           VALUES (?, ?, ?, false, ?)""",
        (domain, spec["description"], spec["steward"], spec.get("shared_concepts_referenced", [])),
    )

    counts = {"concepts": 0, "synonyms": 0, "metrics": 0, "dimensions": 0, "business_rules": 0,
              "asset_mappings": 0, "test_questions": 0, "change_requests": 0}

    for c in spec.get("concepts", []):
        repo._query(  # noqa: SLF001
            """INSERT INTO concept
                (concept_id, canonical_name, concept_type, definition, domain, subdomain, owner, steward,
                 authority_level, sensitivity, discoverability, status, effective_from, version)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'DRAFT', current_date(), 1)""",
            (c["concept_id"], c["canonical_name"], c["concept_type"], c["definition"], c["domain"],
             c.get("subdomain"), c["owner"], c.get("steward"), c["authority_level"],
             c.get("sensitivity", "INTERNAL"), c.get("discoverability", "REQUEST_ACCESS")),
        )
        counts["concepts"] += 1

        change_request_id = str(uuid.uuid4())
        repo._query(  # noqa: SLF001
            """INSERT INTO change_request
                (change_request_id, concept_id, business_reason, new_definition, effective_date,
                 stage, submitted_by)
               VALUES (?, ?, ?, ?, current_date(), 'SUBMITTED', ?)""",
            (change_request_id, c["concept_id"],
             f"New domain onboarding: {domain}", c["definition"], spec["steward"]),
        )
        counts["change_requests"] += 1

    for s in spec.get("synonyms", []):
        repo._query(  # noqa: SLF001
            """INSERT INTO synonym (synonym_id, concept_id, term, synonym_type, confidence, owner, status, effective_from, version)
               VALUES (?, ?, ?, ?, ?, ?, 'DRAFT', current_date(), 1)""",
            (str(uuid.uuid4()), s["concept_id"], s["term"], s["synonym_type"], s.get("confidence", 1.0), spec["steward"]),
        )
        counts["synonyms"] += 1

    for m in spec.get("metrics", []):
        repo._query(  # noqa: SLF001
            """INSERT INTO metric_definition
                (metric_id, concept_id, business_definition, formula, aggregation_behavior,
                 allowed_dimension_ids, time_grain, currency, comparison_rules,
                 certified_source_asset, is_certified, owner, status, effective_from, version)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'DRAFT', current_date(), 1)""",
            (m["metric_id"], m["concept_id"], m["business_definition"], m["formula"],
             m["aggregation_behavior"], m.get("allowed_dimension_ids", []), m.get("time_grain", "MONTH"),
             m.get("currency"), m.get("comparison_rules", []), m["certified_source_asset"],
             m.get("is_certified", False), spec["steward"]),
        )
        counts["metrics"] += 1

    for d in spec.get("dimensions", []):
        repo._query(  # noqa: SLF001
            """INSERT INTO dimension_definition
                (dimension_id, concept_id, key_column, label_column, allowed_operators,
                 value_resolution_strategy, high_cardinality, requires_obo, owner, status, effective_from, version)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'DRAFT', current_date(), 1)""",
            (d["dimension_id"], d["concept_id"], d["key_column"], d.get("label_column"),
             d.get("allowed_operators", ["EQUALS"]), d.get("value_resolution_strategy", "EXACT_MATCH"),
             d.get("high_cardinality", False), d.get("requires_obo", False), spec["steward"]),
        )
        counts["dimensions"] += 1

    for r in spec.get("business_rules", []):
        repo._query(  # noqa: SLF001
            """INSERT INTO business_rule (rule_id, concept_id, rule_type, description, executable_reference,
                                            owner, status, effective_from, version)
               VALUES (?, ?, ?, ?, ?, ?, 'DRAFT', current_date(), 1)""",
            (r["rule_id"], r["concept_id"], r["rule_type"], r["description"], r.get("executable_reference"), spec["steward"]),
        )
        counts["business_rules"] += 1

    for a in spec.get("asset_mappings", []):
        repo._query(  # noqa: SLF001
            """INSERT INTO asset_mapping (mapping_id, concept_id, asset_type, fully_qualified_asset_name,
                                            is_certified, data_quality_state, source_system, freshness_sla_minutes,
                                            owner, status, effective_from, version)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'DRAFT', current_date(), 1)""",
            (a["mapping_id"], a["concept_id"], a["asset_type"], a["fully_qualified_asset_name"],
             a.get("is_certified", False), a.get("data_quality_state", "UNKNOWN"),
             a.get("source_system"), a.get("freshness_sla_minutes"), spec["steward"]),
        )
        counts["asset_mappings"] += 1

    for t in spec.get("test_questions", []):
        repo._query(  # noqa: SLF001
            """INSERT INTO test_question (test_question_id, domain, question_text, expected_concept_ids,
                                            expected_metric_ids, expected_dimension_ids, category)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (t["test_question_id"], t["domain"], t["question_text"], t.get("expected_concept_ids", []),
             t.get("expected_metric_ids", []), t.get("expected_dimension_ids", []), t.get("category", "GENERAL")),
        )
        counts["test_questions"] += 1

    print(f"Submitted domain '{domain}':")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    print(
        f"\nEverything above was inserted with status=DRAFT and {counts['change_requests']} change "
        f"request(s) were opened at stage=SUBMITTED. Nothing is usable by agents until it passes "
        f"Domain Review -> Data Review -> Security Review -> Approved -> Active (PRD Sec. 22)."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain", help="New domain name (creates a blank template to fill in)")
    parser.add_argument("--owner", help="Steward email/group for the new domain")
    parser.add_argument("--from-file", type=Path, help="Path to a filled-in domain YAML to submit")
    args = parser.parse_args()

    if args.from_file:
        submit_domain(args.from_file)
    elif args.domain and args.owner:
        scaffold_new_domain_file(args.domain, args.owner)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
