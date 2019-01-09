import os
import time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pytest_mock_resources.container.postgres import config, get_sqlalchemy_engine


class CreateAll(object):
    def __init__(self, base_cls):
        self.base_cls = base_cls

    def run(self, engine):
        self._create_schemas(engine)
        self.base_cls.metadata.create_all(engine)

    def _create_schemas(self, engine):
        schemas = [table.schema for table in self.base_cls.metadata.tables.values()]

        for schema in schemas:
            statement = "CREATE SCHEMA IF NOT EXISTS {}".format(schema)
            engine.execute(statement)


class Rows(object):
    def __init__(self, *rows):
        self.rows = rows

    def run(self, engine):
        Session = sessionmaker(bind=engine)
        session = Session()

        rows = self._create_stateless_rows(self.rows)
        session.add_all(rows)

        session.commit()
        session.close()

    @staticmethod
    def _create_stateless_rows(rows):
        """Create rows that aren't associated with any other SQLAlchemy session.
        """
        stateless_rows = []
        for row in rows:
            row_args = row.__dict__
            row_args.pop("_sa_instance_state", None)

            stateless_row = type(row)(**row_args)

            stateless_rows.append(stateless_row)
        return stateless_rows


class Statements(object):
    def __init__(self, *statements):
        self.statements = statements

    def run(self, engine):
        for statement in self.statements:
            engine.execute(statement)


def create_sqlite_fixture(ordered_actions=None, scope="function"):
    @pytest.fixture(scope=scope)
    def _():
        engine = create_engine("sqlite://")

        if ordered_actions:
            for action in ordered_actions:
                action.run(engine)

        return engine

    return _


def create_postgres_fixture(
    database_name=None, ordered_actions=None, scope="function", default_suffix="pg"
):
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

        if ordered_actions:
            for action in ordered_actions:
                action.run(engine)

        return engine

    return _


def create_redshift_fixture(
    database_name=None, ordered_actions=None, scope="function", default_suffix="redshift"
):
    return create_postgres_fixture(database_name, ordered_actions, scope, default_suffix)


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


sqlite = create_sqlite_fixture()
postgres = create_postgres_fixture()
redshift = create_redshift_fixture()
