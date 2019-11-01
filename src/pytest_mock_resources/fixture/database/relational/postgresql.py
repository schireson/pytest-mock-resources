import pytest
import sqlalchemy

from pytest_mock_resources.container import get_docker_host
from pytest_mock_resources.container.postgres import config, get_sqlalchemy_engine
from pytest_mock_resources.fixture.database.generic import assign_fixture_credentials
from pytest_mock_resources.fixture.database.relational.generic import EngineManager


def create_postgres_fixture(*ordered_actions, **kwargs):
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
    def _(_postgres_container):
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

        engine_manager = EngineManager(
            engine, ordered_actions, tables=tables, default_schema="public"
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
