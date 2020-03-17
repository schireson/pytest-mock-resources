import pytest

from pytest_mock_resources.container import get_docker_host
from pytest_mock_resources.container.postgres import config
from pytest_mock_resources.fixture.database.generic import assign_fixture_credentials
from pytest_mock_resources.fixture.database.relational.generic import EngineManager
from pytest_mock_resources.fixture.database.relational.postgresql import (
    _create_clean_database,
    get_sqlalchemy_engine,
)
from pytest_mock_resources.patch.redshift.create_engine import (
    substitute_execute_with_custom_execute,
)


def create_redshift_fixture(*ordered_actions, **kwargs):
    """Create a Redshift fixture.

    Any number of fixture functions can be created. Under the hood they will all share the same
    database server.
    """
    scope = kwargs.pop("scope", "function")
    tables = kwargs.pop("tables", None)

    session = kwargs.pop("session", None)

    if len(kwargs):
        raise KeyError("Unsupported Arguments: {}".format(kwargs))

    from pytest_mock_resources.fixture.database.relational.redshift.udf import REDSHIFT_UDFS

    ordered_actions = ordered_actions + (REDSHIFT_UDFS,)

    @pytest.fixture(scope=scope)
    def _(_redshift_container):
        database_name = _create_clean_database()
        engine = get_sqlalchemy_engine(database_name)

        assign_fixture_credentials(
            engine,
            drivername="postgresql+psycopg2",
            host=get_docker_host(),
            port=config["port"],
            database=database_name,
            username="user",
            password="password",
        )

        engine = substitute_execute_with_custom_execute(engine)
        engine_manager = EngineManager(
            engine, ordered_actions, tables=tables, default_schema="public"
        )
        for engine in engine_manager.manage(session=session):
            yield engine

    return _
