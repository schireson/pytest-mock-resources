import pytest
from sqlalchemy import create_engine

from pytest_mock_resources.fixture.database.relational.postgresql import _run_actions


def create_sqlite_fixture(*ordered_actions, **kwargs):
    scope = kwargs.pop("scope", "function")
    tables = kwargs.pop("tables", None)

    if len(kwargs):
        raise KeyError("Unsupported Arguments: {}".format(kwargs))

    @pytest.fixture(scope=scope)
    def _():
        engine = create_engine("sqlite://")

        _run_actions(engine, ordered_actions, tables=tables)

        return engine

    return _
