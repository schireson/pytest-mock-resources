import pytest

from pytest_mock_resources.compat import sqlalchemy

skip_if_sqlalchemy2 = pytest.mark.skipif(
    sqlalchemy.version.startswith("1.4") or sqlalchemy.version.startswith("2."),
    reason="Incompatible with sqlalchemy 2 behavior",
)
