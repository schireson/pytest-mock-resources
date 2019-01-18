import abc
import os
import time

import pytest
import six
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker

from pytest_mock_resources.container.postgres import config, get_sqlalchemy_engine


@pytest.fixture(scope="session")
def PG_HOST():
    return config["host"]


@pytest.fixture(scope="session")
def PG_PORT():
    return config["port"]


@six.add_metaclass(abc.ABCMeta)
class AbstractAction(object):
    @abc.abstractmethod
    def run(self, engine):
        """Run an action on a database via the passed-in engine.

        Args:
            engine (sqlalchemy.engine.Engine)
        """


class Rows(AbstractAction):
    def __init__(self, *rows):
        self.rows = rows

    def run(self, engine):
        rows = self._get_stateless_rows(self.rows)

        metadatas = self._get_metadatas(rows)

        _create_ddl(engine, metadatas)

        self._create_rows(engine, rows)

    @staticmethod
    def _get_stateless_rows(rows):
        """Create rows that aren't associated with any other SQLAlchemy session.
        """
        stateless_rows = []
        for row in rows:
            row_args = row.__dict__
            row_args.pop("_sa_instance_state", None)

            stateless_row = type(row)(**row_args)

            stateless_rows.append(stateless_row)
        return stateless_rows

    @staticmethod
    def _get_metadatas(rows):
        return {row.metadata for row in rows}

    @staticmethod
    def _create_rows(engine, rows):
        Session = sessionmaker(bind=engine)
        session = Session()

        session.add_all(rows)

        session.commit()
        session.close()


class Statements(AbstractAction):
    def __init__(self, *statements):
        self.statements = statements

    def run(self, engine):
        for statement in self.statements:
            engine.execute(statement)


def create_sqlite_fixture(*ordered_actions, **kwargs):
    scope = kwargs.pop("scope", "function")

    if len(kwargs):
        raise KeyError("Unsupported Arguments: {}".format(kwargs))

    @pytest.fixture(scope=scope)
    def _():
        engine = create_engine("sqlite://")

        _run_actions(engine, ordered_actions)

        return engine

    return _


def create_postgres_fixture(*ordered_actions, **kwargs):
    database_name = kwargs.pop("database_name", None)
    scope = kwargs.pop("scope", "function")
    default_suffix = kwargs.pop("default_suffix", "pg")

    if len(kwargs):
        raise KeyError("Unsupported Arguments: {}".format(kwargs))

    @pytest.fixture(scope=scope)
    def _(_postgres_container):
        if database_name:
            database_name_ = database_name
        else:
            test_name = _create_test_based_database_name()
            database_name_ = _clean_database_name(test_name)
            database_name_ = "{}_{}".format(database_name_, default_suffix)

        _create_clean_database(database_name_)
        engine = get_sqlalchemy_engine(database_name_)

        _run_actions(engine, ordered_actions)

        return engine

    return _


def create_redshift_fixture(*ordered_actions, **kwargs):
    database_name = kwargs.pop("database_name", None)
    scope = kwargs.pop("scope", "function")
    default_suffix = kwargs.pop("default_suffix", "redshift")

    if len(kwargs):
        raise KeyError("Unsupported Arguments: {}".format(kwargs))

    return create_postgres_fixture(
        *ordered_actions, database_name=database_name, scope=scope, default_suffix=default_suffix
    )


def _create_test_based_database_name():
    """Create a unique test-based database name.
    """
    # Grab the test name
    qualified_test_name = os.environ.get("PYTEST_CURRENT_TEST").split(" ")[0]
    test_name = qualified_test_name.split(":")[-1]

    # Remove `test_` prefix
    test_name = test_name[5:]

    # Keep only a max of the last 50 letters
    length = len(test_name)
    max_length = min(length, 45)
    test_name = test_name[-max_length:]

    # Add the current unix time for more uniqueness
    unix_time = int(time.time())

    return "{}{}".format(test_name, unix_time)


def _clean_database_name(name):
    name = name.lower()
    name = name.replace("[", "_")
    name = name.replace("]", "_")

    return name


def _create_clean_database(database_name):
    # Database names that include upper case letters must be enclosed in double-quotes.
    database_name = '"{}"'.format(database_name)

    root_engine = get_sqlalchemy_engine(config["root_database"])
    root_connection = root_engine.connect()
    root_connection.connection.connection.set_isolation_level(0)
    root_connection.execute(
        """
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '{database_name}' AND pid <> pg_backend_pid()
        """.format(
            database_name=database_name
        )
    )
    root_connection.execute(
        "DROP DATABASE IF EXISTS {database_name}".format(database_name=database_name)
    )
    root_connection.execute("CREATE DATABASE {database_name}".format(database_name=database_name))
    root_connection.execute(
        "GRANT ALL PRIVILEGES ON DATABASE {database_name} TO CURRENT_USER".format(
            database_name=database_name
        )
    )


def _run_actions(engine, ordered_actions):
    for action in ordered_actions:
        if isinstance(action, MetaData):
            _create_ddl(engine, [action])
        elif isinstance(action, AbstractAction):
            action.run(engine)
        else:
            raise ValueError(
                "create_fixture function takes in sqlalchemy.MetaData or actions as inputs only."
            )


def _create_ddl(engine, metadatas):
    _create_schemas(engine, metadatas)
    _create_tables(engine, metadatas)


def _create_schemas(engine, metadatas):
    for metadata in metadatas:
        schemas = [table.schema for table in metadata.tables.values()]

        for schema in schemas:
            statement = "CREATE SCHEMA IF NOT EXISTS {}".format(schema)
            engine.execute(statement)


def _create_tables(engine, metadatas):
    for metadata in metadatas:
        metadata.create_all(engine)
