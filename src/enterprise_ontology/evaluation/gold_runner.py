"""Gold-dataset evaluation runner — PRD Sec. 24, 26 (100 gold questions is
the Phase 1 exit bar; release blockers listed in Sec. 24). Reads
ontology.test_question, runs each question through concept resolution ->
context projection -> semantic planning -> validation, scores the result
against the expected concept/metric/dimension IDs, and logs an MLflow run so
results are comparable across ontology versions over time (PRD Sec. 24 "MLflow
tracing", Sec. 26 reliability).

Scheduled daily by the `ontology_evaluation` job (databricks.yml).
"""
from __future__ import annotations

import asyncio
import logging

import mlflow

from ..config import get_settings
from ..models import UserContext
from ..repositories.unity_catalog_repository import UnityCatalogOntologyRepository
from ..repositories.lakebase_repository import LakebaseStateRepository
from ..resolution.concept_resolver import ConceptResolver
from ..resolution.context_projector import ContextProjector
from ..planner.semantic_planner import SemanticPlanner
from ..planner.semantic_validator import SemanticValidator
from ..metrics.metric_service import MetricService
from .metrics import EvaluationMetrics

logger = logging.getLogger(__name__)

_SERVICE_PRINCIPAL_CONTEXT = UserContext(
    principal_id="ontology-evaluation-job",
    is_service_principal=True,
    entitlement_group_ids=["ontology-platform-team"],
)


class GoldEvaluationRunner:
    def __init__(
        self,
        repository: UnityCatalogOntologyRepository,
        lakebase: LakebaseStateRepository,
    ):
        self._repo = repository
        self._concept_resolver = ConceptResolver(repository)
        self._context_projector = ContextProjector(repository, lakebase)
        self._planner = SemanticPlanner()
        self._validator = SemanticValidator(MetricService(repository))

    async def run(self, domain: str | None = None) -> EvaluationMetrics:
        questions = self._load_gold_questions(domain)
        metrics = EvaluationMetrics(total=len(questions))

        for q in questions:
            try:
                await self._evaluate_one(q, metrics)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Evaluation failed for test_question_id=%s", q["test_question_id"])
                metrics.failures.append({"test_question_id": q["test_question_id"], "error": str(exc)})

        return metrics

    async def _evaluate_one(self, q: dict, metrics: EvaluationMetrics) -> None:
        expected_concepts = set(q.get("expected_concept_ids") or [])
        expected_metrics = set(q.get("expected_metric_ids") or [])
        expected_dimensions = set(q.get("expected_dimension_ids") or [])

        resolution = await self._concept_resolver.resolve(
            terms=[q["question_text"]], domain=q.get("domain")
        )
        resolved_ids = {c.concept_id for c in resolution.concepts}
        if expected_concepts and expected_concepts.issubset(resolved_ids):
            metrics.concept_resolution_correct += 1

        context = await self._context_projector.project(list(resolved_ids), _SERVICE_PRINCIPAL_CONTEXT)
        context_metric_ids = {m.metric_id for m in context.approved_metrics}
        context_dimension_ids = {d.dimension_id for d in context.approved_dimensions}

        if expected_metrics and expected_metrics.issubset(context_metric_ids):
            metrics.metric_selection_correct += 1
        if expected_dimensions and expected_dimensions.issubset(context_dimension_ids):
            metrics.dimension_selection_correct += 1

        plan = await self._planner.plan(q["question_text"], context)
        validation = await self._validator.validate(plan, context, _SERVICE_PRINCIPAL_CONTEXT)
        if validation.is_valid:
            metrics.plan_valid += 1

    def _load_gold_questions(self, domain: str | None) -> list[dict]:
        if domain:
            return self._repo._query(  # noqa: SLF001
                "SELECT * FROM test_question WHERE domain = ?", (domain,)
            )
        return self._repo._query("SELECT * FROM test_question")  # noqa: SLF001


async def _run() -> None:
    settings = get_settings()
    repo = UnityCatalogOntologyRepository(settings)
    lakebase = LakebaseStateRepository(settings)
    await lakebase.connect()
    try:
        runner = GoldEvaluationRunner(repo, lakebase)
        metrics = await runner.run()
        summary = metrics.as_release_gate_summary()

        with mlflow.start_run(run_name="ontology-gold-evaluation"):
            mlflow.log_metrics({k: v for k, v in summary.items() if isinstance(v, (int, float))})
            mlflow.log_dict(summary, "evaluation_summary.json")

        logger.info("Gold evaluation complete: %s", summary)
        if summary["release_blocked"]:
            logger.error("RELEASE BLOCKED by evaluation gate: %s", summary)
    finally:
        await lakebase.close()


def main() -> None:
    """Entry point registered in pyproject.toml as `run_evaluation`."""
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_run())


if __name__ == "__main__":
    main()
