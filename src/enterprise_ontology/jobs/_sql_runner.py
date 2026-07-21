"""Shared helper: read a directory of .sql files in numeric order, apply
simple ${var} substitution, split into individual statements and execute
them. Used by both the Unity Catalog and Lakebase bootstrap jobs so DDL
files stay plain, portable SQL with one templating convention.

The statement splitter is dollar-quote aware: Postgres `CREATE FUNCTION ...
$$ ... $$ LANGUAGE plpgsql;` bodies (see sql/lakebase/009_maintenance.sql)
contain semicolons that must NOT be treated as statement terminators. A
naive `split(";")` would truncate every function body at its first internal
`;` and send Postgres a syntactically broken statement.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Callable, Iterable

logger = logging.getLogger(__name__)

_DOLLAR_QUOTE_RE = re.compile(r"\$([A-Za-z_]*)\$")


def render(sql_text: str, variables: dict[str, str]) -> str:
    for key, value in variables.items():
        sql_text = sql_text.replace("${" + key + "}", value)
    return sql_text


def iter_statements(sql_text: str) -> Iterable[str]:
    """Split on top-level `;` only — never inside a $tag$ ... $tag$ block."""
    statements: list[str] = []
    buf: list[str] = []
    open_tag: str | None = None
    i = 0
    n = len(sql_text)

    while i < n:
        if open_tag is None:
            match = _DOLLAR_QUOTE_RE.match(sql_text, i)
            if match:
                open_tag = match.group(0)
                buf.append(open_tag)
                i += len(open_tag)
                continue
            if sql_text[i] == ";":
                statements.append("".join(buf))
                buf = []
                i += 1
                continue
            buf.append(sql_text[i])
            i += 1
        else:
            if sql_text.startswith(open_tag, i):
                buf.append(open_tag)
                i += len(open_tag)
                open_tag = None
                continue
            buf.append(sql_text[i])
            i += 1

    if buf:
        statements.append("".join(buf))

    for raw in statements:
        stmt = raw.strip()
        if not stmt:
            continue
        # Drop statements that are comment-only (every non-blank line starts with --).
        if all(line.strip().startswith("--") or not line.strip() for line in stmt.splitlines()):
            continue
        yield stmt


def run_sql_directory(
    directory: Path,
    variables: dict[str, str],
    execute_fn: Callable[[str], None],
    skip_files: tuple[str, ...] = ("999_run_all.sql",),
) -> None:
    files = sorted(p for p in directory.glob("*.sql") if p.name not in skip_files)
    for path in files:
        logger.info("Applying %s", path.name)
        rendered = render(path.read_text(), variables)
        for statement in iter_statements(rendered):
            execute_fn(statement)
