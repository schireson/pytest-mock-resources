import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL

from pytest_mock_resources import (
    create_postgres_fixture,
    create_redshift_fixture,
    create_sqlite_fixture,
    create_mysql_fixture
)
from pytest_mock_resources.fixture.database.relational.generic import EngineManager

sqlite = create_sqlite_fixture()
postgres = create_postgres_fixture()
redshift = create_redshift_fixture()
mysql = create_mysql_fixture()


def test_basic_sqlite_fixture(sqlite):
    sqlite.execute("select 1")


def test_basic_postgres_fixture(postgres):
    postgres.execute("select 1")


def test_basic_redshift_fixture(redshift):
    redshift.execute("select 1")


def test_basic_postgres_and_redshift_fixture(postgres, redshift):
    postgres.execute("select 1")
    redshift.execute("select 1")


def test_basic_mysql_fixture(mysql):
    mysql.execute("select 1")


redshift_2 = create_redshift_fixture()
redshift_3 = create_redshift_fixture()
postgres_2 = create_postgres_fixture()
mysql_2 = create_mysql_fixture()


def test_multiple_postgres_and_redshift_fixture(
    postgres_2, postgres, redshift_2, redshift_3, redshift
):
    postgres_2.execute("select 1")
    postgres.execute("select 1")
    redshift_2.execute("select 1")
    redshift_3.execute("select 1")
    redshift.execute("select 1")


def test_multiple_mysql_fixture(mysql_2, mysql):
    mysql.execute("select 1")
    mysql_2.execute("select 1")


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

    engine.execute("select 1")


def test_create_custom_connection_from_dict(postgres_3):
    engine = create_engine(
        "postgresql://{username}:{password}@{host}:{port}/{database}?sslmode=disable".format(
            **dict(postgres_3.pmr_credentials)
        ),
        isolation_level="AUTOCOMMIT",
    )

    engine.execute("select 1")


def test_create_custom_connection_url(postgres_3):
    url = URL(**postgres_3.pmr_credentials.as_sqlalchemy_url_kwargs())
    engine = create_engine(url, isolation_level="AUTOCOMMIT")
    engine.execute("select 1")


def test_bad_actions(postgres):
    with pytest.raises(ValueError) as e:
        EngineManager(postgres, ordered_actions=["random_string"])._run_actions()

    assert "create_fixture function takes in sqlalchemy.MetaData or actions as inputs only." in str(
        e.value
    )
