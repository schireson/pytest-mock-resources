import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.dialects import registry  # type: ignore

from pytest_mock_resources.credentials import assign_fixture_credentials
from pytest_mock_resources.resource.sqlite.dialect import (
    do_begin,
    do_connect,
    enable_foreign_key_checks,
    filter_sqlalchemy_warnings,
    make_postgres_like_sqlite_dialect,
)
from pytest_mock_resources.sqlalchemy import EngineManager


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
    dialect_name = "sqlite"

    if postgres_like:
        dialect = make_postgres_like_sqlite_dialect()
        dialect_name = dialect.name
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
