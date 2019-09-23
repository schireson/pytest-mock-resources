import pytest
from sqlalchemy import create_engine
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


def create_sqlite_fixture(*ordered_actions, **kwargs):
    scope = kwargs.pop("scope", "function")
    tables = kwargs.pop("tables", None)

    if len(kwargs):
        raise KeyError("Unsupported Arguments: {}".format(kwargs))

    registry.register("sqlite.pmrsqlite", __name__, "PMRSQLiteDialect")

    @pytest.fixture(scope=scope)
    def _():
        engine = create_engine("sqlite+pmrsqlite://")
        for engine in manage_engine(engine, ordered_actions, tables=tables):
            yield engine

    return _
