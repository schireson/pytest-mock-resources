import pytest

from pytest_mock_resources.fixture.database.relational.postgresql import (
    _create_clean_database,
    _run_actions,
    get_sqlalchemy_engine,
)
from pytest_mock_resources.patch.redshift.create_engine import (
    substitute_execute_with_custom_execute,
)


def create_redshift_fixture(*ordered_actions, **kwargs):
    scope = kwargs.pop("scope", "function")
    tables = kwargs.pop("tables", None)

    if len(kwargs):
        raise KeyError("Unsupported Arguments: {}".format(kwargs))

    from pytest_mock_resources.fixture.database.relational.redshift.udf import REDSHIFT_UDFS

    ordered_actions = ordered_actions + (REDSHIFT_UDFS,)

    @pytest.fixture(scope=scope)
    def _(_postgres_container):
        database_name = _create_clean_database()
        engine = get_sqlalchemy_engine(database_name)

        engine.database = database_name
        _run_actions(engine, ordered_actions, tables=tables)

        return substitute_execute_with_custom_execute(engine)

    return _
