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
import contextlib
import datetime
import json
import warnings

import pytest
from sqlalchemy import create_engine, dialects, event
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy.dialects.sqlite import base as sqlite_base
from sqlalchemy.dialects.sqlite.pysqlite import SQLiteDialect_pysqlite
from sqlalchemy.exc import SAWarning
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql import sqltypes

from pytest_mock_resources.fixture.database.generic import assign_fixture_credentials
from pytest_mock_resources.fixture.database.relational.generic import EngineManager


class PMRSQLiteDDLCompiler(sqlite_base.SQLiteDDLCompiler):
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


class UTC(datetime.tzinfo):
    """UTC timezone.

    Blame python2:
    https://docs.python.org/2/library/datetime.html#datetime.tzinfo.fromutc
    """

    ZERO = datetime.timedelta(0)

    def utcoffset(self, dt):
        return self.ZERO

    def dst(self, dt):
        return self.ZERO

    def tzname(self, dt):
        return "UTC"


utc = UTC()


class PMRDateTime(sqlite_base.DATETIME):
    def bind_processor(self, dialect):
        processor = super(PMRDateTime, self).bind_processor(dialect)

        def process(value):
            if isinstance(value, datetime.datetime):
                if value.tzinfo is None:
                    value = value.replace(tzinfo=utc)
                result = value.astimezone(utc)
                return processor(result)

        return process

    def result_processor(self, dialect, coltype):
        processor = super(PMRDateTime, self).result_processor(dialect, coltype)

        def process(value):
            result = processor(value)
            if self.timezone:
                if result is not None and result.tzinfo is None:
                    result = result.replace(tzinfo=utc)
            return result

        return process


PostgresLikeSQLitePDialect = None


def make_postgres_like_sqlite_dialect():
    if not hasattr(sqlite_base, "JSON"):
        raise RuntimeError(
            "Must have sqlalchemy>=1.3.0 in order to make use of the postgres-like sqlite dialect."
        )

    class PostgresLikeTypeCompiler(sqlite_base.SQLiteTypeCompiler):
        """Add features sqlite doesn't support by default.

        Adds:
         * Handling of postgres column types: JSON, JSONB
        """

        @compiles(JSON, "pmrsqlite")
        @compiles(JSONB, "pmrsqlite")
        @compiles(sqltypes.JSON, "pmrsqlite")
        def compile_json(type_, compiler, **kwargs):
            return "BLOB"

    class PostgresLikeDialect(SQLiteDialect_pysqlite):
        """Define the dialect that collects all postgres-like adapations."""

        name = "pmrsqlite"

        supports_statement_cache = True
        ddl_compiler = PMRSQLiteDDLCompiler
        type_compiler = PostgresLikeTypeCompiler
        colspecs = {
            sqltypes.Date: sqlite_base.DATE,
            sqltypes.DateTime: PMRDateTime,
            sqltypes.JSON: sqlite_base.JSON,
            sqltypes.JSON.JSONIndexType: sqlite_base.JSONIndexType,
            sqltypes.JSON.JSONPathType: sqlite_base.JSONPathType,
            sqltypes.Time: sqlite_base.TIME,
        }

        def _json_serializer(self, value):
            return json.dumps(value, sort_keys=True)

    global PostgresLikeSQLitePDialect
    PostgresLikeSQLitePDialect = PostgresLikeDialect
    return PostgresLikeSQLitePDialect


def enable_foreign_key_checks(dbapi_connection, connection_record):
    """Enable foreign key constraint checks.

    SQLite supports FOREIGN KEY syntax when emitting CREATE statements for tables,
    however by default these constraints have no effect on the operation of the table.
    https://docs.sqlalchemy.org/en/latest/dialects/sqlite.html#foreign-key-support
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def do_connect(dbapi_connection, connection_record):
    """Disable pysqlite's emitting of the BEGIN statement entirely.

    Also stops it from emitting COMMIT before any DDL.

    https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#pysqlite-serializable
    """
    dbapi_connection.isolation_level = None


def do_begin(conn):
    """Emit our own BEGIN.

    SQLite lazily emits begin on first write operation by default. This impacts our ability
    to correctly manage the session in `EngineManager`.

    https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#pysqlite-serializable
    """
    try:
        conn.exec_driver_sql("BEGIN")
    except AttributeError:  # pragma: no cover
        conn.execute("BEGIN")


@contextlib.contextmanager
def filter_sqlalchemy_warnings(decimal_warnings_enabled=True):
    with warnings.catch_warnings():
        if decimal_warnings_enabled:
            warnings.filterwarnings(
                "ignore",
                (
                    r"^Dialect pmrsqlite\+pysqlite does \*not\* support Decimal objects natively\, and "
                    r"SQLAlchemy must convert from floating point - rounding errors and other issues may occur\. "
                    r"Please consider storing Decimal numbers as strings or integers on this platform for "
                    r"lossless storage\.$"
                ),
                SAWarning,
            )

        yield


def _database_producer():
    i = 1
    while True:
        yield "db{}".format(i)
        i += 1


_database_names = _database_producer()


def create_sqlite_fixture(
    *ordered_actions,
    scope="function",
    tables=None,
    session=None,
    decimal_warnings=False,
    postgres_like=True
):
    """Produce a SQLite fixture.

    Any number of fixture functions can be created. Under the hood they will all share the same
    database server.

    Arguments:
        ordered_actions: Any number of ordered actions to be run on test setup.
        scope: Passthrough pytest's fixture scope.
        tables: Subsets the tables created by `ordered_actions`. This is generally
            most useful when a model-base was specified in `ordered_actions`.
        session: Whether to return a session instead of an engine directly. This can
            either be a bool or a callable capable of producing a session.
        decimal_warnings: Whether to show sqlalchemy decimal warnings related to precision loss. The
            default `False` suppresses these warnings.
        postgres_like: Whether to add extra SQLite features which attempt to mimic postgres
            enough to stand in for it for testing.
    """

    dialect_name = "sqlite"

    if postgres_like:
        dialect = make_postgres_like_sqlite_dialect()
        dialect_name = dialect.name
        registry = getattr(dialects, "registry")
        registry.register("sqlite.{}".format(dialect_name), __name__, "PostgresLikeSQLitePDialect")

    driver_name = "sqlite+{}".format(dialect_name)

    @pytest.fixture(scope=scope)
    def _():
        # XXX: Ideally we eventually make use of the shared memory cache to enable connecting by
        #      credentials with sqlite.
        # database_name = "file:{}?mode=memory&cache=shared".format(next(_database_names))
        database_name = ""

        raw_engine = create_engine("{}:///{}".format(driver_name, database_name))

        # This *must* happen before the connection occurs (implicitly in `EngineManager`).
        event.listen(raw_engine, "connect", enable_foreign_key_checks)

        # https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#pysqlite-serializable
        event.listen(raw_engine, "connect", do_connect)
        event.listen(raw_engine, "begin", do_begin)

        engine_manager = EngineManager.create(
            raw_engine, ordered_actions, tables=tables, session=session
        )
        for engine in engine_manager.manage_sync():
            with filter_sqlalchemy_warnings(decimal_warnings_enabled=(not decimal_warnings)):
                assign_fixture_credentials(
                    raw_engine,
                    drivername=driver_name,
                    host="",
                    port=None,
                    database=database_name,
                    username="",
                    password="",
                )

                yield engine

        event.remove(raw_engine, "connect", enable_foreign_key_checks)

    return _
