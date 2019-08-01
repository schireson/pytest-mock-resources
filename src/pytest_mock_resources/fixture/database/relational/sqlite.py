import pytest
from sqlalchemy import create_engine

from pytest_mock_resources.fixture.database.relational.generic import manage_engine


def create_sqlite_fixture(*ordered_actions, **kwargs):
    scope = kwargs.pop("scope", "function")
    tables = kwargs.pop("tables", None)

    if len(kwargs):
        raise KeyError("Unsupported Arguments: {}".format(kwargs))

    @pytest.fixture(scope=scope)
    def _():
        engine = create_engine("sqlite://")
        for engine in manage_engine(engine, ordered_actions, tables=tables):
            yield engine

    return _
