"""Strip Redshift-only clauses from CREATE TABLE statements.

DISTKEY, SORTKEY, and DISTSTYLE are accepted by Redshift but rejected by
Postgres. Since the fixture is backed by Postgres, raw SQL containing them
must have them removed before forwarding to the cursor.
"""
import re

_DISTKEY_RE = re.compile(r"\s*DISTKEY\s*\(\s*[^)]*\)", re.IGNORECASE)
_DISTSTYLE_RE = re.compile(r"\s*DISTSTYLE\s+(?:AUTO|EVEN|KEY|ALL)", re.IGNORECASE)
_SORTKEY_RE = re.compile(
    r"\s*(?:COMPOUND\s+|INTERLEAVED\s+)?SORTKEY\s*(?:AUTO|\(\s*[^)]*\))",
    re.IGNORECASE,
)
_CREATE_TABLE_RE = re.compile(r"^\s*create\s+(?:temp(?:orary)?\s+)?table\b", re.IGNORECASE)


def is_create_table(sql):
    """Return True if the SQL starts with a CREATE TABLE statement."""
    return bool(_CREATE_TABLE_RE.match(sql))


def strip_redshift_table_options(sql):
    """Remove Redshift-only DISTKEY/SORTKEY/DISTSTYLE clauses from the SQL."""
    for pattern in (_DISTKEY_RE, _DISTSTYLE_RE, _SORTKEY_RE):
        sql = pattern.sub("", sql)
    return sql
