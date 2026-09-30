import copy

import pytest
from sqlalchemy import text

from pytest_mock_resources import create_postgres_fixture
from pytest_mock_resources.container.postgres import get_sqlalchemy_engine
from pytest_mock_resources.fixture.base import asyncio_fixture
from pytest_mock_resources.fixture.postgresql import (
    _async_fixture,
    _sync_fixture,
    DatabaseDropWarning,
)
from tests import skip_if_not_sqlalchemy2

postgres_default = create_postgres_fixture()
postgres_disabled = create_postgres_fixture(cleanup_databases=False)
postgres_default_async = create_postgres_fixture(async_=True)

MANAGER_KWARGS = {
    "ordered_actions": (),
    "tables": None,
    "createdb_template": "template1",
    "session": None,
    "fixture_id": None,
    "actions_share_transaction": None,
}


def test_database_is_kept_when_disabled(pmr_postgres_container, pmr_postgres_config):
    fixture = _sync_fixture(pmr_postgres_config, MANAGER_KWARGS, {}, cleanup_databases=False)
    engine, _ = next(fixture)
    database_name = engine.url.database

    fixture.close()

    assert database_name in list_databases(pmr_postgres_config)
    drop_database(pmr_postgres_config, database_name)


def test_database_is_dropped_when_enabled(pmr_postgres_container, pmr_postgres_config):
    fixture = _sync_fixture(pmr_postgres_config, MANAGER_KWARGS, {}, cleanup_databases=True)
    engine, _ = next(fixture)
    database_name = engine.url.database
    assert database_name in list_databases(pmr_postgres_config)

    fixture.close()

    assert database_name not in list_databases(pmr_postgres_config)


def test_database_is_dropped_after_test_failure(pmr_postgres_container, pmr_postgres_config):
    fixture = _sync_fixture(pmr_postgres_config, MANAGER_KWARGS, {}, cleanup_databases=True)
    engine, _ = next(fixture)
    database_name = engine.url.database

    with pytest.raises(AssertionError) as exc_info:
        fixture.throw(AssertionError("test failed"))

    assert str(exc_info.value) == "test failed"

    assert database_name not in list_databases(pmr_postgres_config)


def test_database_is_dropped_with_leaked_connection(pmr_postgres_container, pmr_postgres_config):
    fixture = _sync_fixture(pmr_postgres_config, MANAGER_KWARGS, {}, cleanup_databases=True)
    engine, _ = next(fixture)
    database_name = engine.url.database
    leaked_engine = get_sqlalchemy_engine(pmr_postgres_config, database_name)
    leaked_conn = leaked_engine.connect()
    assert count_connections(pmr_postgres_config, database_name) >= 1

    fixture.close()

    assert database_name not in list_databases(pmr_postgres_config)
    assert count_connections(pmr_postgres_config, database_name) == 0
    leaked_conn.invalidate()
    leaked_engine.dispose()


def test_other_databases_are_left_alone(pmr_postgres_container, pmr_postgres_config):
    dropped = _sync_fixture(pmr_postgres_config, MANAGER_KWARGS, {}, cleanup_databases=True)
    kept = _sync_fixture(pmr_postgres_config, MANAGER_KWARGS, {}, cleanup_databases=False)
    next(dropped)
    kept_engine, _ = next(kept)
    kept_name = kept_engine.url.database
    kept_conn = kept_engine.connect()

    dropped.close()

    assert kept_name in list_databases(pmr_postgres_config)
    assert kept_conn.execute(text("select 1")).scalar() == 1
    kept_conn.close()
    kept.close()
    drop_database(pmr_postgres_config, kept_name)


def test_already_dropped_database_is_ignored(pmr_postgres_container, pmr_postgres_config):
    fixture = _sync_fixture(pmr_postgres_config, MANAGER_KWARGS, {}, cleanup_databases=True)
    engine, _ = next(fixture)
    database_name = engine.url.database
    engine.dispose()
    drop_database(pmr_postgres_config, database_name)

    fixture.close()

    assert database_name not in list_databases(pmr_postgres_config)


def test_drop_failure_warns_with_database_name(pmr_postgres_container, pmr_postgres_config):
    unreachable_config = copy.copy(pmr_postgres_config)
    fixture = _sync_fixture(unreachable_config, MANAGER_KWARGS, {}, cleanup_databases=True)
    engine, _ = next(fixture)
    database_name = engine.url.database
    unreachable_config.set("root_database", "pmr_missing_root_database")

    with pytest.warns(DatabaseDropWarning) as warning_records:
        fixture.close()

    assert len(warning_records) == 1
    message = str(warning_records[0].message)
    assert message.startswith(f"Failed to drop database '{database_name}' at fixture teardown: ")
    assert "pmr_missing_root_database" in message
    assert database_name in list_databases(pmr_postgres_config)
    drop_database(pmr_postgres_config, database_name)


@pytest.mark.asyncio
@skip_if_not_sqlalchemy2
async def test_async_database_is_dropped_when_enabled(pmr_postgres_container, pmr_postgres_config):
    fixture = _async_fixture(pmr_postgres_config, MANAGER_KWARGS, {}, cleanup_databases=True)
    engine, _ = await fixture.__anext__()
    database_name = engine.url.database
    assert database_name in await list_databases_async(pmr_postgres_config)

    with pytest.raises(StopAsyncIteration):
        await fixture.__anext__()

    assert database_name not in await list_databases_async(pmr_postgres_config)


@pytest.mark.asyncio
@skip_if_not_sqlalchemy2
async def test_async_database_is_kept_when_disabled(pmr_postgres_container, pmr_postgres_config):
    fixture = _async_fixture(pmr_postgres_config, MANAGER_KWARGS, {}, cleanup_databases=False)
    engine, _ = await fixture.__anext__()
    database_name = engine.url.database

    with pytest.raises(StopAsyncIteration):
        await fixture.__anext__()

    assert database_name in await list_databases_async(pmr_postgres_config)
    await drop_database_async(pmr_postgres_config, database_name)


def test_database_is_dropped_by_default(assert_databases_dropped, postgres_default):
    assert_databases_dropped.append(postgres_default.url.database)


def test_database_is_kept_when_fixture_disables_it(assert_databases_kept, postgres_disabled):
    assert_databases_kept.append(postgres_disabled.url.database)


@pytest.mark.asyncio
@skip_if_not_sqlalchemy2
async def test_async_database_is_dropped_by_default(
    assert_databases_dropped_async, postgres_default_async
):
    assert_databases_dropped_async.append(postgres_default_async.url.database)


# NOTE: Fixtures are torn down in reverse order of setup. The tests above request these fixtures
#       before the postgres fixture, so their teardown runs after the postgres database is handled.
@pytest.fixture
def assert_databases_dropped(pmr_postgres_container, pmr_postgres_config):
    database_names = []

    yield database_names

    assert len(database_names) == 1
    assert list_databases(pmr_postgres_config).isdisjoint(database_names)


@pytest.fixture
def assert_databases_kept(pmr_postgres_container, pmr_postgres_config):
    database_names = []

    yield database_names

    assert len(database_names) == 1
    assert list_databases(pmr_postgres_config).issuperset(database_names)
    drop_database(pmr_postgres_config, database_names[0])


async def check_databases_dropped_async(pmr_postgres_container, pmr_postgres_config):
    database_names = []

    yield database_names

    assert len(database_names) == 1
    assert (await list_databases_async(pmr_postgres_config)).isdisjoint(database_names)


assert_databases_dropped_async = asyncio_fixture(check_databases_dropped_async)


def list_databases(config):
    rows = run_root_query(config, "select datname from pg_database")

    return {row[0] for row in rows}


def count_connections(config, database_name):
    rows = run_root_query(
        config,
        "select count(*) from pg_stat_activity where datname = :name",
        {"name": database_name},
    )

    return rows[0][0]


def drop_database(config, database_name):
    run_root_query(config, f'DROP DATABASE IF EXISTS "{database_name}"')


def run_root_query(config, statement, params=None):
    engine = get_sqlalchemy_engine(config, config.root_database, autocommit=True)
    with engine.connect() as conn:
        result = conn.execute(text(statement), params or {})
        rows = result.all() if result.returns_rows else []

    engine.dispose()

    return rows


async def list_databases_async(config):
    rows = await run_root_query_async(config, "select datname from pg_database")

    return {row[0] for row in rows}


async def drop_database_async(config, database_name):
    await run_root_query_async(config, f'DROP DATABASE IF EXISTS "{database_name}"')


async def run_root_query_async(config, statement):
    engine = get_sqlalchemy_engine(config, config.root_database, async_=True, autocommit=True)
    async with engine.connect() as conn:
        result = await conn.execute(text(statement))
        rows = result.all() if result.returns_rows else []

    await engine.dispose()

    return rows
