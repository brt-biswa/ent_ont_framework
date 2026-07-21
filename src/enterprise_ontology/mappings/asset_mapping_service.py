"""Physical asset / document mapping service — PRD Sec. 10 "asset mapping":
concepts map to approved physical assets, fields, functions, indexes,
documents and tools; broken mappings must be detected automatically (that
detection lives in drift/detector.py, which reads this same table).
"""
from __future__ import annotations

from ..models import AssetMapping
from ..repositories.unity_catalog_repository import UnityCatalogOntologyRepository


class AssetMappingService:
    def __init__(self, repository: UnityCatalogOntologyRepository):
        self._repo = repository

    async def get_certified_source(self, concept_id: str) -> AssetMapping | None:
        mappings = await self._repo.get_asset_mappings(concept_id)
        certified = [m for m in mappings if m.is_certified]
        return certified[0] if certified else (mappings[0] if mappings else None)

    async def get_all(self, concept_id: str) -> list[AssetMapping]:
        return await self._repo.get_asset_mappings(concept_id)
