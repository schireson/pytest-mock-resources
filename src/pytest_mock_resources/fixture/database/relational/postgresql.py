import pytest
import sqlalchemy

from pytest_mock_resources.container.postgres import get_sqlalchemy_engine, PostgresConfig
from pytest_mock_resources.fixture.database.generic import assign_fixture_credentials
from pytest_mock_resources.fixture.database.relational.generic import EngineManager


@pytest.fixture(scope="session")
def pmr_postgres_config():
    """Override this fixture with a :class:`PostgresConfig` instance to specify different defaults.

    Examples:
        >>> @pytest.fixture(scope='session')
        ... def pmr_postgres_config():
        ...     return PostgresConfig(image="postgres:9.6.10", root_database="foo")
    """
    return PostgresConfig()


def create_engine_manager(pmr_postgres_config, ordered_actions, tables):
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
    return EngineManager(engine, ordered_actions, tables=tables, default_schema="public")


def create_postgres_fixture(
    *ordered_actions, scope="function", tables=None, session=None, async_=False
):
    """Produce a Postgres fixture.

    Any number of fixture functions can be created. Under the hood they will all share the same
    database server.

    Arguments:
        ordered_actions: Any number of ordered actions to be run on test setup.
        scope: Passthrough pytest's fixture scope.
        tables: Subsets the tables created by `ordered_actions`. This is generally
            most useful when a model-base was specified in `ordered_actions`.
        session: Whether to return a session instead of an engine directly. This can
            either be a bool or a callable capable of producing a session.
        async_: Whether to return an async fixture/client.
    """

    @pytest.fixture(scope=scope)
    def _sync(_postgres_container, pmr_postgres_config):
        engine_manager = create_engine_manager(pmr_postgres_config, ordered_actions, tables)
        yield from engine_manager.manage_sync(session=session)

    @pytest.fixture(scope=scope)
    async def _async(_postgres_container, pmr_postgres_config):
        engine_manager = create_engine_manager(pmr_postgres_config, ordered_actions, tables)
        async for engine in engine_manager.manage_async(session=session):
            yield engine

    if async_:
        return _async
    else:
        return _sync


def _create_clean_database(config):
    root_engine = get_sqlalchemy_engine(config, config.root_database, isolation_level="AUTOCOMMIT")

    try:
        root_engine.execute(
            """
            CREATE TABLE IF NOT EXISTS pytest_mock_resource_db(
                id serial
            );
            """
        )
    except (sqlalchemy.exc.IntegrityError, sqlalchemy.exc.ProgrammingError):
        # A race condition may occur during table creation if:
        #  - another process has already created the table
        #  - the current process begins creating the table
        #  - the other process commits the table creation
        #  - the current process tries to commit the table creation
        pass

    result = root_engine.execute(
        "INSERT INTO pytest_mock_resource_db VALUES (DEFAULT) RETURNING id"
    )
    id_ = tuple(result)[0][0]
    database_name = "pytest_mock_resource_db_{}".format(id_)

    root_engine.execute('CREATE DATABASE "{}"'.format(database_name))
    root_engine.execute(
        'GRANT ALL PRIVILEGES ON DATABASE "{}" TO CURRENT_USER'.format(database_name)
    )

    return database_name
