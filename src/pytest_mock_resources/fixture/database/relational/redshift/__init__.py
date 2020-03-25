import pytest

from pytest_mock_resources.fixture.database.generic import assign_fixture_credentials
from pytest_mock_resources.fixture.database.relational.generic import EngineManager
from pytest_mock_resources.fixture.database.relational.postgresql import (
    _create_clean_database,
    get_sqlalchemy_engine,
)
from pytest_mock_resources.patch.redshift import psycopg2, sqlalchemy


def create_redshift_fixture(*ordered_actions, scope="function", tables=None, session=None):
    """Produce a Redshift fixture.

    Any number of fixture functions can be created. Under the hood they will all share the same
    database server.

    Arguments:
        ordered_actions: Any number of ordered actions to be run on test setup.
        scope: Passthrough pytest's fixture scope.
        tables: Subsets the tables created by `ordered_actions`. This is generally
            most useful when a model-base was specified in `ordered_actions`.
        session: Whether to return a session instead of an engine directly. This can
            either be a bool or a callable capable of producing a session.
    """

    from pytest_mock_resources.fixture.database.relational.redshift.udf import REDSHIFT_UDFS

    ordered_actions = ordered_actions + (REDSHIFT_UDFS,)

    @pytest.fixture(scope=scope)
    def _(_redshift_container, pmr_postgres_config):
        database_name = _create_clean_database(pmr_postgres_config)
        engine = get_sqlalchemy_engine(pmr_postgres_config, database_name)

        assign_fixture_credentials(
            engine,
            drivername="postgresql+psycopg2",
            host=pmr_postgres_config.host,
            port=pmr_postgres_config.port,
            database=database_name,
            username=pmr_postgres_config.username,
            password=pmr_postgres_config.password,
        )

        sqlalchemy.register_redshift_behavior(engine)
        with psycopg2.patch_connect(pmr_postgres_config, database_name):
            engine_manager = EngineManager(
                engine, ordered_actions, tables=tables, default_schema="public"
            )
            yield from engine_manager.manage(session=session)

    return _
