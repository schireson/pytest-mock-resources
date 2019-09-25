import pytest
import sqlalchemy

from pytest_mock_resources.container.postgres import config, get_sqlalchemy_engine
from pytest_mock_resources.fixture.database.relational.generic import manage_engine


@pytest.fixture(scope="session")
def PG_HOST():
    return config["host"]


@pytest.fixture(scope="session")
def PG_PORT():
    return config["port"]


def create_postgres_fixture(*ordered_actions, **kwargs):
    scope = kwargs.pop("scope", "function")
    tables = kwargs.pop("tables", None)

    if len(kwargs):
        raise KeyError("Unsupported Arguments: {}".format(kwargs))

    @pytest.fixture(scope=scope)
    def _(_postgres_container):
        database_name = _create_clean_database()
        engine = get_sqlalchemy_engine(database_name)

        engine.database = database_name

        for engine in manage_engine(
            engine, ordered_actions, tables=tables, default_schema="public"
        ):
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
