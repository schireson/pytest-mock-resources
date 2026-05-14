"""Strip Redshift-only clauses from CREATE TABLE statements.

DISTKEY, SORTKEY, and DISTSTYLE are accepted by Redshift but rejected by
Postgres. Since the fixture is backed by Postgres, raw SQL containing them
must have them removed before forwarding to the cursor.
"""
import re

_DISTKEY_RE = re.compile(r"\s*\bDISTKEY\b\s*\(\s*[^)]*\)", re.IGNORECASE)
_DISTSTYLE_RE = re.compile(r"\s*\bDISTSTYLE\b\s+(?:AUTO|EVEN|KEY|ALL)\b", re.IGNORECASE)
_SORTKEY_RE = re.compile(
    r"\s*(?:\b(?:COMPOUND|INTERLEAVED)\s+)?\bSORTKEY\b\s*(?:\bAUTO\b|\(\s*[^)]*\))",
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
