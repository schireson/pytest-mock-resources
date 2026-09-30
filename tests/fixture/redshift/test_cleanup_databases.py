import pytest
from sqlalchemy import text

from pytest_mock_resources import create_redshift_fixture
from pytest_mock_resources.container.postgres import get_sqlalchemy_engine
from pytest_mock_resources.fixture.base import asyncio_fixture
from tests import skip_if_not_sqlalchemy2

redshift_kept = create_redshift_fixture()
redshift_cleaned = create_redshift_fixture(cleanup_databases=True)
redshift_cleaned_async = create_redshift_fixture(cleanup_databases=True, async_=True)


def test_database_is_kept_by_default(pmr_redshift_config, redshift_kept):
    database_name = redshift_kept.url.database

    assert database_name in list_databases(pmr_redshift_config)
    drop_database(pmr_redshift_config, redshift_kept)


def test_database_is_dropped_when_enabled(assert_databases_dropped, redshift_cleaned):
    assert_databases_dropped.append(redshift_cleaned.url.database)


@pytest.mark.asyncio
@skip_if_not_sqlalchemy2
async def test_async_database_is_dropped_when_enabled(
    assert_databases_dropped_async, redshift_cleaned_async
):
    assert_databases_dropped_async.append(redshift_cleaned_async.url.database)


# NOTE: Fixtures are torn down in reverse order of setup. The tests above request this fixture
#       before the redshift fixture, so its teardown runs after the redshift database is cleaned up.
@pytest.fixture
def assert_databases_dropped(pmr_redshift_container, pmr_redshift_config):
    database_names = []

    yield database_names

    assert len(database_names) == 1
    assert list_databases(pmr_redshift_config).isdisjoint(database_names)


async def check_databases_dropped_async(pmr_redshift_container, pmr_redshift_config):
    database_names = []

    yield database_names

    assert len(database_names) == 1
    assert (await list_databases_async(pmr_redshift_config)).isdisjoint(database_names)


assert_databases_dropped_async = asyncio_fixture(check_databases_dropped_async)


async def list_databases_async(config):
    engine = get_sqlalchemy_engine(config, config.root_database, async_=True, autocommit=True)
    async with engine.connect() as conn:
        rows = (await conn.execute(text("select datname from pg_database"))).all()

    await engine.dispose()

    return {row[0] for row in rows}


def list_databases(config):
    engine = get_sqlalchemy_engine(config, config.root_database, autocommit=True)
    with engine.connect() as conn:
        rows = conn.execute(text("select datname from pg_database")).all()

    engine.dispose()

    return {row[0] for row in rows}


def drop_database(config, engine):
    database_name = engine.url.database
    engine.dispose()
    root_engine = get_sqlalchemy_engine(config, config.root_database, autocommit=True)
    with root_engine.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{database_name}"'))

    root_engine.dispose()
