import pytest
import sqlalchemy

from pytest_mock_resources.container import get_docker_host
from pytest_mock_resources.container.mysql import config, get_sqlalchemy_engine
from pytest_mock_resources.fixture.database.generic import assign_fixture_credentials
from pytest_mock_resources.fixture.database.relational.generic import EngineManager


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
    def _(_mysql_container):
        database_name = _create_clean_database()
        engine = get_sqlalchemy_engine(database_name)

        assign_fixture_credentials(
            engine,
            drivername="mysql+pymysql",
            host=get_docker_host(),
            port=config["port"],
            database=database_name,
            username="root",
            password="password",
        )

        engine_manager = EngineManager(
            engine, ordered_actions, tables=tables
        )
        for engine in engine_manager.manage(session=session):
            yield engine

    return _


def _create_clean_database():
    root_engine = get_sqlalchemy_engine(config["root_database"], isolation_level="AUTOCOMMIT")

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

    root_engine.execute(
        "INSERT INTO pytest_mock_resource_db VALUES (DEFAULT)"
    )
    result = root_engine.execute(
        "SELECT LAST_INSERT_ID()"
    )
    id_ = tuple(result)[0][0]
    database_name = "pytest_mock_resource_db_{}".format(id_)

    root_engine.execute('CREATE DATABASE {}'.format(database_name))

    return database_name
