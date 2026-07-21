"""ontology.synonym — PRD Sec. 6.5 language and synonym layer.

Non-equivalent / prohibited-equivalence terms are recorded explicitly
(synonym_type = PROHIBITED_EQUIVALENCE) so the resolver can actively reject a
false match instead of merely failing to find one (PRD Sec. 6.5, last line).
"""
from __future__ import annotations
from pydantic import Field

from ._base import GovernedRecord
from .enums import SynonymType


class Synonym(GovernedRecord):
    synonym_id: str
    concept_id: str
    term: str
    synonym_type: SynonymType
    locale: str = "en-US"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    @property
    def is_prohibited(self) -> bool:
        return self.synonym_type == SynonymType.PROHIBITED_EQUIVALENCE
