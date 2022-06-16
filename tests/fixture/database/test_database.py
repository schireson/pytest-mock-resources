import pytest
from sqlalchemy import create_engine, text

from pytest_mock_resources import (
    compat,
    create_mysql_fixture,
    create_postgres_fixture,
    create_redshift_fixture,
    create_sqlite_fixture,
)
from pytest_mock_resources.sqlalchemy.engine_manager import EngineManager

sqlite = create_sqlite_fixture()
postgres = create_postgres_fixture()
redshift = create_redshift_fixture()
mysql = create_mysql_fixture()


def test_basic_sqlite_fixture(sqlite):
    with sqlite.connect() as conn:
        conn.execute(text("select 1"))


def test_basic_postgres_fixture(postgres):
    with postgres.connect() as conn:
        conn.execute(text("select 1"))


def test_basic_redshift_fixture(redshift):
    with redshift.connect() as conn:
        conn.execute(text("select 1"))


def test_basic_postgres_and_redshift_fixture(postgres, redshift):
    with postgres.connect() as conn:
        conn.execute(text("select 1"))

    with redshift.connect() as conn:
        conn.execute(text("select 1"))


def test_basic_mysql_fixture(mysql):
    with mysql.connect() as conn:
        conn.execute(text("select 1"))


redshift_2 = create_redshift_fixture()
redshift_3 = create_redshift_fixture()
postgres_2 = create_postgres_fixture()
mysql_2 = create_mysql_fixture()


def test_multiple_postgres_and_redshift_fixture(
    postgres_2, postgres, redshift_2, redshift_3, redshift
):
    with postgres_2.connect() as conn:
        conn.execute(text("select 1"))
    with postgres.connect() as conn:
        conn.execute(text("select 1"))
    with redshift_2.connect() as conn:
        conn.execute(text("select 1"))
    with redshift_3.connect() as conn:
        conn.execute(text("select 1"))
    with redshift.connect() as conn:
        conn.execute(text("select 1"))


def test_multiple_mysql_fixture(mysql_2, mysql):
    with mysql.connect() as conn:
        conn.execute(text("select 1"))
    with mysql_2.connect() as conn:
        conn.execute(text("select 1"))


postgres_3 = create_postgres_fixture()


def test_create_custom_connection(postgres_3):
    creds = postgres_3.pmr_credentials
    engine = create_engine(
        "postgresql://{username}:{password}@{host}:{port}/{database}?sslmode=disable".format(
            database=creds.database,
            username=creds.username,
            password=creds.password,
            host=creds.host,
            port=creds.port,
        ),
        isolation_level="AUTOCOMMIT",
    )

    with engine.connect() as conn:
        conn.execute(text("select 1"))


def test_create_custom_connection_from_dict(postgres_3):
    engine = create_engine(
        "postgresql://{username}:{password}@{host}:{port}/{database}?sslmode=disable".format(
            **dict(postgres_3.pmr_credentials)
        ),
        isolation_level="AUTOCOMMIT",
    )

    with engine.connect() as conn:
        conn.execute(text("select 1"))


def test_create_custom_connection_url(postgres_3):
    url = compat.sqlalchemy.URL(**postgres_3.pmr_credentials.as_sqlalchemy_url_kwargs())
    engine = create_engine(url, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        conn.execute(text("select 1"))


def test_bad_actions(postgres):
    with pytest.raises(ValueError) as e:
        EngineManager.create(postgres, dynamic_actions=["random_string"])

    assert (
        "`random_string` invalid: create_<x>_fixture functions accept sqlalchemy.MetaData or actions as inputs."
        in str(e.value)
    )


postgres_async = create_postgres_fixture(async_=True)


@pytest.mark.asyncio
async def test_basic_postgres_fixture_async(postgres_async):
    async with postgres_async.connect() as conn:
        await conn.execute(text("select 1"))
