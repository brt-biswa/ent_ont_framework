"""Canonical Pydantic data model for the Enterprise Ontology Framework.

This mirrors the Unity Catalog Delta data model defined in the PRD (Sec. 21)
exactly, table for table, so that repository code can serialize/deserialize
without translation drift. Every model is immutable at the field-value level
(new versions are new rows, never in-place mutation of an ACTIVE definition).
"""
from .enums import (
    ConceptType, LifecycleStatus, AuthorityLevel, Sensitivity, Discoverability,
    RuleType, SynonymType, AssetType, Operator, ComparisonBasis, TimeGrain,
    ValueResolutionStrategy, DriftSeverity, ChangeRequestStage,
)
from .concept import Concept
from .relationship import Relationship
from .synonym import Synonym
from .metric import MetricDefinition
from .dimension import DimensionDefinition
from .hierarchy import Hierarchy, HierarchyNode
from .business_rule import BusinessRule
from .asset_mapping import AssetMapping
from .document_mapping import DocumentMapping
from .security import SecurityScope, AuthoritySource
from .version import OntologyVersion
from .change_request import ChangeRequest, ApprovalHistory
from .drift import DriftEvent
from .agent_tool import DomainRegistry, AgentMapping, ToolMapping, TestQuestion
from .plan import SemanticPlan, PlanFilter, PlanValidationResult
from .context import UserContext, OntologyContext

__all__ = [
    "ConceptType", "LifecycleStatus", "AuthorityLevel", "Sensitivity", "Discoverability",
    "RuleType", "SynonymType", "AssetType", "Operator", "ComparisonBasis", "TimeGrain",
    "ValueResolutionStrategy", "DriftSeverity", "ChangeRequestStage",
    "Concept", "Relationship", "Synonym", "MetricDefinition", "DimensionDefinition",
    "Hierarchy", "HierarchyNode", "BusinessRule", "AssetMapping", "DocumentMapping",
    "SecurityScope", "AuthoritySource", "OntologyVersion", "ChangeRequest",
    "ApprovalHistory", "DriftEvent", "DomainRegistry", "AgentMapping", "ToolMapping",
    "TestQuestion", "SemanticPlan", "PlanFilter", "PlanValidationResult",
    "UserContext", "OntologyContext",
]
