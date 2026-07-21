"""ontology.domain_registry / agent_mapping / tool_mapping / test_question."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class DomainRegistry(BaseModel):
    domain: str
    description: str
    steward: str
    council_reviewed: bool = False
    shared_concepts_referenced: list[str] = Field(default_factory=list)


class AgentMapping(BaseModel):
    agent_mapping_id: str
    agent_name: str
    domain: str
    genie_agent_ref: Optional[str] = None
    allowed_concept_ids: list[str] = Field(default_factory=list)
    allowed_metric_ids: list[str] = Field(default_factory=list)
    max_sql_policy_level: int = Field(default=2, ge=1, le=2)


class ToolMapping(BaseModel):
    tool_mapping_id: str
    tool_name: str
    mcp_service_ref: str
    concept_ids: list[str] = Field(default_factory=list)
    input_schema_ref: Optional[str] = None
    output_schema_ref: Optional[str] = None


class TestQuestion(BaseModel):
    test_question_id: str
    domain: str
    question_text: str
    expected_concept_ids: list[str] = Field(default_factory=list)
    expected_metric_ids: list[str] = Field(default_factory=list)
    expected_dimension_ids: list[str] = Field(default_factory=list)
    expected_plan: Optional[dict] = None
    category: str = Field(
        default="GENERAL",
        description="CONCEPT_RESOLUTION|SYNONYM|NON_EQUIVALENCE|AMBIGUITY|METRIC_SELECTION|"
                    "DIMENSION_SELECTION|ENTITY_RESOLUTION|JOIN_PATH|FISCAL_PERIOD|"
                    "AUTHORIZATION|SEMANTIC_PLANNING|SQL_COMPILATION|CONSISTENCY|"
                    "HISTORICAL_VERSION|DEPRECATED_SOURCE",
    )
