import abc
from time import sleep

import pytest
import six
from pyhive import hive
from pyhive.sqlalchemy_presto import PrestoDialect
from sqlalchemy import create_engine, MetaData, schema
from sqlalchemy.dialects import registry
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import DATE
from thrift.transport.TTransport import TTransportException

from pytest_mock_resources.container.presto import config, get_presto_connection
from pytest_mock_resources.fixture.database.relational.generic import _execute_function


class CustomPrestoDialect(PrestoDialect):
    name = "custom_presto"
    supports_multivalues_insert = True


registry.register(
    "custom_presto", "pytest_mock_resources.fixture.database.presto", "CustomPrestoDialect"
)


@compiles(DATE, b"hive")
def compile_date_hive(type_, compiler, **kw):
    return "DATE"


@compiles(schema.PrimaryKeyConstraint, b"hive")
def visit_primary_key_constraint(self, constraint):
    return ""


@compiles(schema.CreateColumn, b"hive")
def compile(element, compiler, **kw):
    column = element.element

    text = "%s %s" % (column.name, compiler.type_compiler.process(column.type))

    return text


@six.add_metaclass(abc.ABCMeta)
class AbstractAction(object):
    @abc.abstractmethod
    def run(self, engine, tables):
        """Run an action on a database via the passed-in engine.

        Args:
            engine (sqlalchemy.engine.Engine)
        """


@pytest.fixture(scope="session")
def PRESTO_HOST():
    return config["host"]


@pytest.fixture(scope="session")
def PRESTO_PORT():
    return config["port"]


def create_hive_fixture_raw(**kwargs):
    scope = kwargs.pop("scope", "function")

    if len(kwargs):
        raise KeyError("Unsupported Arguments: {}".format(kwargs))

    @pytest.fixture(scope=scope)
    def _(_presto_container):
        try:
            return hive.connect("localhost", database="default")
        except TTransportException:
            print("Sleeping more...")
            sleep(90)
            return hive.connect("localhost", database="default")

    return _


def create_presto_fixture_raw(**kwargs):
    scope = kwargs.pop("scope", "function")

    if len(kwargs):
        raise KeyError("Unsupported Arguments: {}".format(kwargs))

    @pytest.fixture(scope=scope)
    def _(_presto_container):
        return get_presto_connection()

    return _


def create_hive_fixture(*ordered_actions, **kwargs):
    scope = kwargs.pop("scope", "function")
    tables = kwargs.pop("tables", None)

    if len(kwargs):
        raise KeyError("Unsupported Arguments: {}".format(kwargs))

    @pytest.fixture(scope=scope)
    def _(_presto_container):
        engine = create_engine("hive://localhost:10000/default")

        try:
            _run_actions(engine, ordered_actions, tables=tables)
        except TTransportException:
            print("Sleeping more...")
            sleep(90)
            _run_actions(engine, ordered_actions, tables=tables)

        return engine

    return _


def create_presto_fixture(*ordered_actions, **kwargs):
    scope = kwargs.pop("scope", "function")

    if len(kwargs):
        raise KeyError("Unsupported Arguments: {}".format(kwargs))

    @pytest.fixture(scope=scope)
    def _(_presto_container):
        return create_engine("custom_presto://localhost:8080/default")

    return _


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
    for this_schema in all_schemas:
        statement = "CREATE DATABASE IF NOT EXISTS {}".format(this_schema)
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
