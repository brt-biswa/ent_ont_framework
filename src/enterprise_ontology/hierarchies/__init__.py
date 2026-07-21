"""PRD Sec. 27's suggested repo structure lists `hierarchies/` as its own
top-level package. In this implementation, hierarchy resolution/expansion is
cohesive with dimension-value resolution (a hierarchy is how many dimensions
resolve their values — see PRD Sec. 13), so the real implementation lives in
`dimensions/hierarchy_resolver.py` and is re-exported here.
"""
from ..dimensions.hierarchy_resolver import HierarchyResolver

__all__ = ["HierarchyResolver"]
