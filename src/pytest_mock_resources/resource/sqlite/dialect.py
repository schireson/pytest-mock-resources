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

from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy.dialects.sqlite import base as sqlite_base
from sqlalchemy.dialects.sqlite.pysqlite import SQLiteDialect_pysqlite
from sqlalchemy.exc import SAWarning
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql import sqltypes


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
    conn.exec_driver_sql("BEGIN")


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
