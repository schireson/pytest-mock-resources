import pytest
from sqlalchemy import create_engine, text

from pytest_mock_resources import (
    create_mongo_fixture,
    create_moto_fixture,
    create_mysql_fixture,
    create_postgres_fixture,
    create_redis_fixture,
    create_redshift_fixture,
    create_sqlite_fixture,
)

mongo = create_mongo_fixture()
moto = create_moto_fixture()
mysql = create_mysql_fixture()
mysql_session = create_mysql_fixture(session=True)
pg = create_postgres_fixture()
pg_session = create_postgres_fixture(session=True)
pg_async = create_postgres_fixture(async_=True)
pg_async_session = create_postgres_fixture(async_=True, session=True)
redis = create_redis_fixture()
redshift = create_redshift_fixture()
redshift_session = create_redshift_fixture(session=True)
redshift_async = create_redshift_fixture(async_=True)
redshift_async_session = create_redshift_fixture(async_=True, session=True)
sqlite = create_sqlite_fixture()
sqlite_session = create_sqlite_fixture(session=True)


def test_mongo_pmr_credentials(mongo):
    assert mongo.pmr_credentials


def test_moto_pmr_credentials(moto):
    assert moto
    assert moto.pmr_credentials.aws_access_key_id
    assert moto.pmr_credentials.aws_secret_access_key


def test_mysql_pmr_credentials(mysql):
    credentials = mysql.pmr_credentials
    verify_relational(mysql, credentials)


def test_mysql_session_pmr_credentials(mysql_session):
    credentials = mysql_session.pmr_credentials
    verify_relational(mysql_session, credentials, session=True)


def test_postgres_pmr_credentials(pg):
    credentials = pg.pmr_credentials
    verify_relational(pg, credentials)


def test_postgres_session_pmr_credentials(pg_session):
    credentials = pg_session.pmr_credentials
    verify_relational(pg_session, credentials, session=True)


@pytest.mark.asyncio
async def test_postgres_async_pmr_credentials(pg_async):
    assert pg_async.sync_engine.pmr_credentials


@pytest.mark.asyncio
async def test_postgres_async_session_pmr_credentials(pg_async_session):
    assert (await pg_async_session.connection()).sync_engine.pmr_credentials


def test_redis_pmr_credentials(redis):
    assert redis.pmr_credentials


def test_redshift_pmr_credentials(redshift):
    credentials = redshift.pmr_credentials
    verify_relational(redshift, credentials)


def test_redshift_session_pmr_credentials(redshift_session):
    credentials = redshift_session.pmr_credentials
    verify_relational(redshift_session, credentials, session=True)


@pytest.mark.asyncio
async def test_redshift_async_pmr_credentials(redshift_async):
    assert redshift_async.sync_engine.pmr_credentials


@pytest.mark.asyncio
async def test_redshift_async_session_pmr_credentials(redshift_async_session):
    assert (await redshift_async_session.connection()).sync_engine.pmr_credentials


def test_sqlite_pmr_credentials(sqlite):
    assert sqlite.pmr_credentials


def test_sqlite_session_pmr_credentials(sqlite_session):
    assert sqlite_session.pmr_credentials


def verify_relational(connection, credentials, session=False):
    """Verify connection to the same database as the one given to the test function, using credentials."""
    assert credentials

    queries = [
        text("create table foo (id integer)"),
        text("commit"),
    ]
    if not session:
        with connection.begin() as conn:
            for query in queries:
                conn.execute(query)
    else:
        for query in queries:
            connection.execute(query)

    manual_engine = create_engine(credentials.as_url())
    with manual_engine.connect() as conn:
        conn.execute(text("select * from foo"))
