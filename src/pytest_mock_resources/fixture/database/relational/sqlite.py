"""Adapt SQLite to act more in line with typical postgresql usage.

SQLite is a desireable test database target because it introduces much less latency across
tests, is parallelizable, and has a lower minimum fixed test-startup cost.

Unfortunately, SQLite and postgresql do not behave identically in all cases. However, in
many (typically CRUD) API type database designs, there is no need for postgresql-specific
features, and SQLite can act as an appropriate stand in.

Where possible though, this module changes the default SQLite behavior to more closely
mimic postgresql, so as to increase the number of places where SQLite can frictionlessly
stand in for postgresql.
"""
import json

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.dialects import registry
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy.dialects.sqlite.base import SQLiteDDLCompiler, SQLiteTypeCompiler
from sqlalchemy.dialects.sqlite.pysqlite import SQLiteDialect_pysqlite
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql import sqltypes

from pytest_mock_resources.fixture.database.relational.generic import manage_engine


class PMRSQLiteDDLCompiler(SQLiteDDLCompiler):
    """Add features sqlite doesn't support by default.

    Adds:
     * Handling `CREATE SCHEMA`.
    """

    def visit_create_schema(self, create):
        schema = self.preparer.format_schema(create.element)
        return "ATTACH DATABASE ':memory:' AS " + schema

    def visit_drop_schema(self, create):
        schema = self.preparer.format_schema(create.element)
        return "DETACH DATABASE " + schema


class PMRSQLiteTypeCompiler(SQLiteTypeCompiler):
    """Add features sqlite doesn't support by default.

    Adds:
     * Handling of postgres column types: JSON, JSONB
    """

    @compiles(JSON, "pmrsqlite")
    @compiles(JSONB, "pmrsqlite")
    @compiles(sqltypes.JSON, "pmrsqlite")
    def compile_json(type_, compiler, **kwargs):
        return "BLOB"


class PMRSQLiteDialect(SQLiteDialect_pysqlite):
    """Define the dialect that collects all postgres-like adapations.
    """

    name = "pmrsqlite"

    ddl_compiler = PMRSQLiteDDLCompiler
    type_compiler = PMRSQLiteTypeCompiler

    def _json_serializer(self, value):
        return json.dumps(value, sort_keys=True)


def enable_foreign_key_checks(dbapi_connection, connection_record):
    """Enable foreign key constraint checks.

    SQLite supports FOREIGN KEY syntax when emitting CREATE statements for tables,
    however by default these constraints have no effect on the operation of the table.
    https://docs.sqlalchemy.org/en/latest/dialects/sqlite.html#foreign-key-support
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def create_sqlite_fixture(*ordered_actions, **kwargs):
    scope = kwargs.pop("scope", "function")
    tables = kwargs.pop("tables", None)

    if len(kwargs):
        raise KeyError("Unsupported Arguments: {}".format(kwargs))

    registry.register("sqlite.pmrsqlite", __name__, "PMRSQLiteDialect")

    @pytest.fixture(scope=scope)
    def _():
        raw_engine = create_engine("sqlite+pmrsqlite://")

        # This *must* happen before the connection occurs (implicitly in `manage_engine`).
        event.listen(raw_engine, "connect", enable_foreign_key_checks)

        for engine in manage_engine(raw_engine, ordered_actions, tables=tables):
            yield engine

        event.remove(raw_engine, "connect", enable_foreign_key_checks)

    return _
