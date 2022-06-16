import os

import pytest

try:
    import sqlalchemy
except ImportError:
    sqlalchemy_version = ''
else:
    sqlalchemy_version = getattr(sqlalchemy, 'version', '')

skip_if_sqlalchemy2 = pytest.mark.skipif(
    sqlalchemy_version.startswith("1.4") or sqlalchemy_version.startswith("2."),
    reason="Incompatible with sqlalchemy 2 behavior",
)

skip_if_ci = pytest.mark.skipif(
    os.environ.get("CI") == "true",
    reason="Incompatible with CI behavior",
)
