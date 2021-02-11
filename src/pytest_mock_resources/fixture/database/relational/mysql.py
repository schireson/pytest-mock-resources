import pytest
import sqlalchemy

from pytest_mock_resources.container.mysql import get_sqlalchemy_engine, MysqlConfig
from pytest_mock_resources.fixture.database.generic import assign_fixture_credentials
from pytest_mock_resources.fixture.database.relational.generic import EngineManager


@pytest.fixture(scope="session")
def pmr_mysql_config():
    """Override this fixture with a :class:`MysqlConfig` instance to specify different defaults.

    Examples:
        >>> @pytest.fixture(scope='session')
        ... def pmr_mysql_config():
        ...     return MysqlConfig(image="mysql:5.2", root_database="foo")
    """
    return MysqlConfig()


def create_mysql_fixture(*ordered_actions, **kwargs):
    """Create a Postgres fixture.

    Any number of fixture functions can be created. Under the hood they will all share the same
    database server.
    """
    scope = kwargs.pop("scope", "function")
    tables = kwargs.pop("tables", None)

    session = kwargs.pop("session", None)

    if len(kwargs):
        raise KeyError("Unsupported Arguments: {}".format(kwargs))

    @pytest.fixture(scope=scope)
    def _(_mysql_container, pmr_mysql_config):
        database_name = _create_clean_database(pmr_mysql_config)
        engine = get_sqlalchemy_engine(pmr_mysql_config, database_name)

        assign_fixture_credentials(
            engine,
            drivername="mysql+pymysql",
            host=pmr_mysql_config.host,
            port=pmr_mysql_config.port,
            database=database_name,
            username=pmr_mysql_config.username,
            password=pmr_mysql_config.password,
        )

        engine_manager = EngineManager(engine, ordered_actions, tables=tables)
        for engine in engine_manager.manage(session=session):
            yield engine

    return _


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

    root_engine.execute("INSERT INTO pytest_mock_resource_db VALUES (DEFAULT)")
    result = root_engine.execute("SELECT LAST_INSERT_ID()")
    id_ = tuple(result)[0][0]
    database_name = "pytest_mock_resource_db_{}".format(id_)

    root_engine.execute("CREATE DATABASE {}".format(database_name))

    return database_name
