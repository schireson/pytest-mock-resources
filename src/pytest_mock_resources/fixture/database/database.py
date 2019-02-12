import abc

import pytest
import six
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
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
    scope = kwargs.pop("scope", "function")

    if len(kwargs):
        raise KeyError("Unsupported Arguments: {}".format(kwargs))

    @pytest.fixture(scope=scope)
    def _(_postgres_container):
        database_name = _create_clean_database()
        engine = get_sqlalchemy_engine(database_name)

        engine.database = database_name

        _run_actions(engine, ordered_actions)

        return engine

    return _


def create_redshift_fixture(*ordered_actions, **kwargs):
    scope = kwargs.pop("scope", "function")

    if len(kwargs):
        raise KeyError("Unsupported Arguments: {}".format(kwargs))

    from pytest_mock_resources.fixture.database.udf import REDSHIFT_UDFS

    return create_postgres_fixture(REDSHIFT_UDFS, *ordered_actions, scope=scope)


def _create_clean_database():
    # Database names that include upper case letters must be enclosed in double-quotes.
    root_engine = get_sqlalchemy_engine(config["root_database"])
    root_connection = root_engine.connect()
    root_connection.connection.connection.set_isolation_level(0)

    # Create a unique database name
    root_connection.execute(
        """
        CREATE TABLE IF NOT EXISTS database_name(
            id SERIAL
        );
        """
    )
    root_connection.execute("INSERT INTO database_name VALUES (DEFAULT)")
    database_id_row = root_connection.execute("SELECT MAX(id) FROM database_name").fetchone()

    database_name = "database_{}".format(database_id_row[0])
    quoted_database_name = '"{}"'.format(database_name)

    root_connection.execute(
        """
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '{}' AND pid <> pg_backend_pid()
        """.format(
            quoted_database_name
        )
    )
    root_connection.execute("DROP DATABASE IF EXISTS {}".format(quoted_database_name))
    root_connection.execute("CREATE DATABASE {}".format(quoted_database_name))
    root_connection.execute(
        "GRANT ALL PRIVILEGES ON DATABASE {} TO CURRENT_USER".format(quoted_database_name)
    )

    return database_name


def _run_actions(engine, ordered_actions):
    BaseType = type(declarative_base())

    for action in ordered_actions:
        if isinstance(action, MetaData):
            _create_ddl(engine, [action])
        elif isinstance(action, BaseType):
            _create_ddl(engine, [action.metadata])
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
        schemas = {table.schema for table in metadata.tables.values() if table.schema}

        for schema in schemas:
            statement = "CREATE SCHEMA IF NOT EXISTS {}".format(schema)
            engine.execute(statement)


def _create_tables(engine, metadatas):
    for metadata in metadatas:
        metadata.create_all(engine)
