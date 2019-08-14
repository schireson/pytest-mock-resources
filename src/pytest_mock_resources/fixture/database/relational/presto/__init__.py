import pytest

from pytest_mock_resources.fixture.database.relational.generic import _run_actions
from pytest_mock_resources.fixture.database.relational.postgresql import (
    _create_clean_database,
    get_sqlalchemy_engine,
)


def create_presto_fixture(*ordered_actions, **kwargs):
    scope = kwargs.pop("scope", "function")
    tables = kwargs.pop("tables", None)

    if len(kwargs):
        raise KeyError("Unsupported Arguments: {}".format(kwargs))

    from pytest_mock_resources.fixture.database.relational.presto.udf import PRESTO_UDFS

    ordered_actions = ordered_actions + (PRESTO_UDFS,)

    @pytest.fixture(scope=scope)
    def _(_postgres_container):
        database_name = _create_clean_database()
        engine = get_sqlalchemy_engine(database_name)

        engine.database = database_name
        _run_actions(engine, ordered_actions, tables=tables)

        return engine

    return _
