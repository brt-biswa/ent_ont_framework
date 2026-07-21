"""Enumerations shared across the ontology data model (PRD Sec. 6, 21, 22, 23)."""
from __future__ import annotations
from enum import Enum


class ConceptType(str, Enum):
    ENTITY = "ENTITY"
    MEASURE = "MEASURE"
    DIMENSION = "DIMENSION"
    HIERARCHY = "HIERARCHY"
    EVENT = "EVENT"
    STATE = "STATE"
    POLICY = "POLICY"
    RULE = "RULE"
    ACTION = "ACTION"
    CAPABILITY = "CAPABILITY"
    TIME_CONCEPT = "TIME_CONCEPT"
    LOCATION = "LOCATION"
    ROLE = "ROLE"
    DATA_PRODUCT = "DATA_PRODUCT"
    AGENT = "AGENT"
    TOOL = "TOOL"


class LifecycleStatus(str, Enum):
    """PRD Sec. 22 versioning and lifecycle state machine."""
    DRAFT = "DRAFT"
    DOMAIN_REVIEW = "DOMAIN_REVIEW"
    DATA_REVIEW = "DATA_REVIEW"
    SECURITY_REVIEW = "SECURITY_REVIEW"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    RETIRED = "RETIRED"

    @classmethod
    def next_allowed(cls, current: "LifecycleStatus") -> tuple["LifecycleStatus", ...]:
        order = list(cls)
        idx = order.index(current)
        # Forward transition, or DEPRECATED can be reached from ACTIVE only.
        if current == cls.ACTIVE:
            return (cls.DEPRECATED,)
        if current == cls.DEPRECATED:
            return (cls.RETIRED,)
        if idx + 1 < len(order) - 2:  # cannot skip into DEPRECATED/RETIRED directly
            return (order[idx + 1],)
        return ()


class AuthorityLevel(str, Enum):
    """PRD Sec. 6.7 authority order, 1 = highest authority."""
    CERTIFIED_METRIC_VIEW_OR_FUNCTION = "1_CERTIFIED_METRIC_VIEW_OR_FUNCTION"
    APPROVED_ENTERPRISE_POLICY = "2_APPROVED_ENTERPRISE_POLICY"
    CERTIFIED_DASHBOARD_OR_TRUSTED_SQL = "3_CERTIFIED_DASHBOARD_OR_TRUSTED_SQL"
    APPROVED_GLOSSARY = "4_APPROVED_GLOSSARY"
    FREQUENTLY_USED_QUERY = "5_FREQUENTLY_USED_QUERY"
    GENERAL_DOCUMENT = "6_GENERAL_DOCUMENT"
    USER_CREATED_OR_INFERRED = "7_USER_CREATED_OR_INFERRED"


class Sensitivity(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"
    REGULATED = "REGULATED"


class Discoverability(str, Enum):
    OPEN = "OPEN"
    REQUEST_ACCESS = "REQUEST_ACCESS"
    HIDDEN = "HIDDEN"


class RuleType(str, Enum):
    DEFINITION = "DEFINITION"
    CALCULATION = "CALCULATION"
    VALIDATION = "VALIDATION"
    ELIGIBILITY = "ELIGIBILITY"
    SECURITY = "SECURITY"
    TEMPORAL = "TEMPORAL"
    AGGREGATION = "AGGREGATION"
    APPROVAL = "APPROVAL"
    EXCEPTION = "EXCEPTION"
    COMPARISON = "COMPARISON"
    MATERIALITY = "MATERIALITY"


class SynonymType(str, Enum):
    EXACT = "EXACT"
    CONTEXTUAL = "CONTEXTUAL"
    ABBREVIATION = "ABBREVIATION"
    LEGACY = "LEGACY"
    REGIONAL = "REGIONAL"
    MISSPELLING = "MISSPELLING"
    PROHIBITED_EQUIVALENCE = "PROHIBITED_EQUIVALENCE"


class AssetType(str, Enum):
    TABLE = "TABLE"
    VIEW = "VIEW"
    MATERIALIZED_VIEW = "MATERIALIZED_VIEW"
    METRIC_VIEW = "METRIC_VIEW"
    COLUMN = "COLUMN"
    MEASURE = "MEASURE"
    DIMENSION_FIELD = "DIMENSION_FIELD"
    UC_FUNCTION = "UC_FUNCTION"
    MODEL = "MODEL"
    MODEL_SERVICE = "MODEL_SERVICE"
    AI_SEARCH_INDEX = "AI_SEARCH_INDEX"
    VOLUME = "VOLUME"
    DOCUMENT = "DOCUMENT"
    GENIE_AGENT = "GENIE_AGENT"
    MCP_SERVICE = "MCP_SERVICE"
    MCP_TOOL = "MCP_TOOL"
    API = "API"
    EXTERNAL_APPLICATION = "EXTERNAL_APPLICATION"


class Operator(str, Enum):
    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    IN = "IN"
    NOT_IN = "NOT_IN"
    GREATER_THAN = "GREATER_THAN"
    GREATER_OR_EQUAL = "GREATER_OR_EQUAL"
    LESS_THAN = "LESS_THAN"
    LESS_OR_EQUAL = "LESS_OR_EQUAL"
    BETWEEN = "BETWEEN"
    CONTAINS_HIERARCHY_PATH = "CONTAINS_HIERARCHY_PATH"


class ComparisonBasis(str, Enum):
    NONE = "NONE"
    PRIOR_PERIOD = "PRIOR_PERIOD"
    PRIOR_YEAR = "PRIOR_YEAR"
    BUDGET = "BUDGET"
    FORECAST = "FORECAST"


class TimeGrain(str, Enum):
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"
    FISCAL_PERIOD = "FISCAL_PERIOD"
    QUARTER = "QUARTER"
    FISCAL_YEAR = "FISCAL_YEAR"
    YEAR = "YEAR"


class ValueResolutionStrategy(str, Enum):
    EXACT_MATCH = "EXACT_MATCH"
    FUZZY_MATCH = "FUZZY_MATCH"
    SYNONYM_LOOKUP = "SYNONYM_LOOKUP"
    HIERARCHY_PATH = "HIERARCHY_PATH"
    OBO_GOVERNED_SERVICE = "OBO_GOVERNED_SERVICE"


class DriftSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class ChangeRequestStage(str, Enum):
    SUBMITTED = "SUBMITTED"
    DOMAIN_REVIEW = "DOMAIN_REVIEW"
    DATA_REVIEW = "DATA_REVIEW"
    SECURITY_REVIEW = "SECURITY_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    IMPLEMENTED = "IMPLEMENTED"
