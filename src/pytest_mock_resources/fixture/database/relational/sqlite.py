import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.dialects import registry
from sqlalchemy.dialects.sqlite.base import SQLiteDDLCompiler
from sqlalchemy.dialects.sqlite.pysqlite import SQLiteDialect_pysqlite

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


class PMRSQLiteDialect(SQLiteDialect_pysqlite):
    name = "pmrsqlite"

    ddl_compiler = PMRSQLiteDDLCompiler


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
