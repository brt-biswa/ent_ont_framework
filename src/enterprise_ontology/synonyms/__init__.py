"""PRD Sec. 27's suggested repo structure lists `synonyms/` as its own
top-level package. In this implementation, synonym resolution is cohesive
with concept resolution (both are "exact + governed text matching" against
the same registry tables), so the real implementation lives in
`resolution/synonym_resolver.py` and is re-exported here so both import
paths documented in the PRD and this codebase work identically.
"""
from ..resolution.synonym_resolver import SynonymResolver, SynonymMatch

__all__ = ["SynonymResolver", "SynonymMatch"]
