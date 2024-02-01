import pytest
import sqlalchemy
from sqlalchemy import text

from pytest_mock_resources.container.base import get_container
from pytest_mock_resources.container.mysql import get_sqlalchemy_engine, MysqlConfig
from pytest_mock_resources.sqlalchemy import EngineManager


@pytest.fixture(scope="session")
def pmr_mysql_config():
    """Override this fixture with a :class:`MysqlConfig` instance to specify different defaults.

    Examples:
        >>> @pytest.fixture(scope='session')
        ... def pmr_mysql_config():
        ...     return MysqlConfig(image="mysql:5.2", root_database="foo")
    """
    return MysqlConfig()


@pytest.fixture(scope="session")
def pmr_mysql_container(pytestconfig, pmr_mysql_config):
    yield from get_container(pytestconfig, pmr_mysql_config, interval=1, retries=60)


def create_mysql_fixture(
    *ordered_actions,
    scope="function",
    tables=None,
    session=None,
    engine_kwargs=None,
):
    """Produce a MySQL fixture.

    Any number of fixture functions can be created. Under the hood they will all share the same
    database server.

    Arguments:
        ordered_actions: Any number of ordered actions to be run on test setup.
        scope: Passthrough pytest's fixture scope.
        tables: Subsets the tables created by `ordered_actions`. This is generally
            most useful when a model-base was specified in `ordered_actions`.
        session: Whether to return a session instead of an engine directly. This can
            either be a bool or a callable capable of producing a session.
        engine_kwargs: Optional set of kwargs to send into the engine on creation.
    """

    @pytest.fixture(scope=scope)
    def _(pmr_mysql_container, pmr_mysql_config):
        database_name = _create_clean_database(pmr_mysql_config)
        engine = get_sqlalchemy_engine(
            pmr_mysql_config,
            database_name,
            **(engine_kwargs or {}),
        )

        engine_manager = EngineManager.create(
            fixture="mysql",
            dynamic_actions=ordered_actions,
            tables=tables,
            session=session,
        )
        for _, conn in engine_manager.manage_sync(engine):
            yield conn

    return _


def _create_clean_database(config):
    root_engine = get_sqlalchemy_engine(config, config.root_database, isolation_level="AUTOCOMMIT")

    with root_engine.begin() as conn:
        try:
            conn.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS pytest_mock_resource_db(
                    id serial
                );
                """
                )
            )
        except (sqlalchemy.exc.IntegrityError, sqlalchemy.exc.ProgrammingError):
            # A race condition may occur during table creation if:
            #  - another process has already created the table
            #  - the current process begins creating the table
            #  - the other process commits the table creation
            #  - the current process tries to commit the table creation
            pass

        conn.execute(text("INSERT INTO pytest_mock_resource_db VALUES (DEFAULT)"))
        result = conn.execute(text("SELECT LAST_INSERT_ID()"))
        id_ = next(iter(result))[0]
        database_name = f"pytest_mock_resource_db_{id_}"

        conn.execute(text(f"CREATE DATABASE {database_name}"))

    return database_name
