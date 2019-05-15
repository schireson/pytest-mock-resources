import abc

import pytest
import six
from sqlalchemy import MetaData
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
    def run(self, engine, tables):
        """Run an action on a database via the passed-in engine.

        Args:
            engine (sqlalchemy.engine.Engine)
        """


class Rows(AbstractAction):
    def __init__(self, *rows):
        self.rows = rows

    def run(self, engine, tables):
        rows = self._get_stateless_rows(self.rows)

        metadatas = self._get_metadatas(rows)

        for metadata in metadatas:
            _create_ddl(engine, metadata, tables)

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

    def run(self, engine, tables):
        for statement in self.statements:
            engine.execute(statement)


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

        _run_actions(engine, ordered_actions, tables=tables)

        return engine

    return _


def _create_clean_database():
    root_engine = get_sqlalchemy_engine(config["root_database"], isolation_level="AUTOCOMMIT")

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


def _run_actions(engine, ordered_actions, tables=None):
    BaseType = type(declarative_base())

    for action in ordered_actions:
        if isinstance(action, MetaData):
            _create_ddl(engine, action, tables)
        elif isinstance(action, BaseType):
            _create_ddl(engine, action.metadata, tables)
        elif isinstance(action, AbstractAction):
            action.run(engine, tables)
        elif callable(action):
            _execute_function(engine, action)
        else:
            raise ValueError(
                "create_fixture function takes in sqlalchemy.MetaData or actions as inputs only."
            )


def _create_ddl(engine, metadata, tables):
    _create_schemas(engine, metadata)
    _create_tables(engine, metadata, tables)


def _create_schemas(engine, metadata):
    all_schemas = {table.schema for table in metadata.tables.values() if table.schema}
    for schema in all_schemas:
        statement = "CREATE SCHEMA IF NOT EXISTS {}".format(schema)
        engine.execute(statement)


def _create_tables(engine, metadata, tables):
    if not tables:
        metadata.create_all(engine)
        return

    # Make sure to include any implicit or explicit variations of tables in the `public` schema
    additional_implicit_tables = {table[7:] for table in tables if table.startswith("public.")}
    additional_explicit_tables = {
        "public." + table for table in tables if len(table.split(".")) == 1
    }

    all_tables = set().union(tables, additional_implicit_tables, additional_explicit_tables)

    relevant_table_classes = [
        table for tablename, table in metadata.tables.items() if tablename in all_tables
    ]
    metadata.create_all(engine, tables=relevant_table_classes)


def _execute_function(engine, fn):
    Session = sessionmaker(bind=engine)
    session = Session()

    fn(session)

    session.commit()
    session.close()
