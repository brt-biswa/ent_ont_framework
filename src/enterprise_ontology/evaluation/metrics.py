"""Evaluation metrics — PRD Sec. 24 "key metrics": concept-resolution
accuracy, metric/dimension-selection precision/recall, entity-resolution
precision, join correctness, plan validity, SQL validity/policy compliance,
provenance completeness, unauthorized concept exposure.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EvaluationMetrics:
    total: int = 0
    concept_resolution_correct: int = 0
    metric_selection_correct: int = 0
    dimension_selection_correct: int = 0
    plan_valid: int = 0
    unauthorized_exposures: int = 0
    failures: list[dict] = field(default_factory=list)

    @property
    def concept_resolution_accuracy(self) -> float:
        return self.concept_resolution_correct / self.total if self.total else 0.0

    @property
    def metric_selection_precision(self) -> float:
        return self.metric_selection_correct / self.total if self.total else 0.0

    @property
    def dimension_selection_precision(self) -> float:
        return self.dimension_selection_correct / self.total if self.total else 0.0

    @property
    def plan_validity_rate(self) -> float:
        return self.plan_valid / self.total if self.total else 0.0

    def as_release_gate_summary(self) -> dict:
        """PRD Sec. 24 release blockers: unauthorized exposure, unapproved
        source use, SQL-policy bypass, missing version metadata, broken
        critical mappings, major regression."""
        return {
            "total_questions": self.total,
            "concept_resolution_accuracy": round(self.concept_resolution_accuracy, 4),
            "metric_selection_precision": round(self.metric_selection_precision, 4),
            "dimension_selection_precision": round(self.dimension_selection_precision, 4),
            "plan_validity_rate": round(self.plan_validity_rate, 4),
            "unauthorized_exposures": self.unauthorized_exposures,
            "release_blocked": self.unauthorized_exposures > 0 or self.concept_resolution_accuracy < 0.95,
            "failure_count": len(self.failures),
        }
