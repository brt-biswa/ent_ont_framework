"""Concept resolution — PRD Sec. 10 "ontology retrieval": exact lookup,
synonym resolution, and (optionally) semantic/embedding lookup layered on
top. This is the entry point request classification calls before any
planning happens (PRD Sec. 12 runtime sequence, steps 2-3).

Design principle 8 (Sec. 5): categorical VALUES are resolved by governed
services (dimensions/dimension_resolver.py); this module only resolves which
CONCEPTS (metrics, dimensions, entities...) a question is about.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..models import Concept
from ..repositories.unity_catalog_repository import UnityCatalogOntologyRepository
from .synonym_resolver import SynonymResolver, SynonymMatch


@dataclass
class ConceptResolutionResult:
    concepts: list[Concept] = field(default_factory=list)
    unresolved_terms: list[str] = field(default_factory=list)
    ambiguous_terms: dict[str, list[Concept]] = field(default_factory=dict)
    requires_clarification: bool = False


class ConceptResolver:
    """Deterministic-first concept resolution. Semantic (embedding-based)
    fallback is intentionally a separate, injectable step (`semantic_lookup_fn`)
    so a domain team can plug in AI Search / a vector index without this class
    caring about the implementation (PRD Sec. 32 anti-pattern: "don't treat
    vector search as the sole ontology store" — it is one input among several,
    used only as a fallback after exact + synonym lookup miss).
    """

    AMBIGUITY_CONFIDENCE_SPREAD = 0.15

    def __init__(
        self,
        repository: UnityCatalogOntologyRepository,
        synonym_resolver: SynonymResolver | None = None,
        semantic_lookup_fn=None,
    ):
        self._repo = repository
        self._synonyms = synonym_resolver or SynonymResolver(repository)
        self._semantic_lookup_fn = semantic_lookup_fn  # async Callable[[str, str|None], list[SynonymMatch]]

    async def resolve(self, terms: list[str], domain: str | None = None) -> ConceptResolutionResult:
        result = ConceptResolutionResult()
        exact = await self._repo.resolve_terms(terms, domain=domain)
        exact_by_term = {c.canonical_name.lower(): c for c in exact}

        for term in terms:
            lowered = term.lower()
            if lowered in exact_by_term:
                result.concepts.append(exact_by_term[lowered])
                continue

            matches = await self._synonyms.resolve(term, domain=domain)
            usable = [m for m in matches if not m.is_prohibited]

            if not usable and self._semantic_lookup_fn is not None:
                usable = await self._semantic_lookup_fn(term, domain)

            if not usable:
                result.unresolved_terms.append(term)
                continue

            candidate_concepts = await self._repo.resolve_terms(
                [m.concept_id for m in usable], domain=domain
            )
            if len(candidate_concepts) == 1:
                result.concepts.append(candidate_concepts[0])
            elif len(candidate_concepts) > 1:
                confidences = sorted((m.confidence for m in usable), reverse=True)
                is_ambiguous = (
                    len(confidences) > 1
                    and (confidences[0] - confidences[1]) < self.AMBIGUITY_CONFIDENCE_SPREAD
                )
                if is_ambiguous:
                    result.ambiguous_terms[term] = candidate_concepts
                    result.requires_clarification = True
                else:
                    result.concepts.append(candidate_concepts[0])

        return result
