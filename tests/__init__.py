import os

import pytest

from pytest_mock_resources.compat import sqlalchemy

is_at_least_sqlalchemy2 = sqlalchemy.version.startswith("2.")
is_sqlalchemy2 = sqlalchemy.version.startswith("1.4") or sqlalchemy.version.startswith("2.")
skip_if_sqlalchemy2 = pytest.mark.skipif(
    is_sqlalchemy2,
    reason="Incompatible with sqlalchemy 2 behavior",
)
skip_if_not_sqlalchemy2 = pytest.mark.skipif(
    not is_sqlalchemy2,
    reason="Incompatible before sqlalchemy 2 behavior",
)

skip_if_ci = pytest.mark.skipif(
    os.environ.get("CI") == "true",
    reason="Incompatible with CI behavior",
)
