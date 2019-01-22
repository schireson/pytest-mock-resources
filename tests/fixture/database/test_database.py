import pytest
from sqlalchemy import create_engine

from pytest_mock_resources import (
    create_postgres_fixture,
    create_redshift_fixture,
    create_sqlite_fixture,
)
from pytest_mock_resources.fixture.database import _run_actions

sqlite = create_sqlite_fixture()
postgres = create_postgres_fixture()
redshift = create_redshift_fixture()


def test_basic_sqlite_fixture(sqlite):
    sqlite.execute("select 1")


def test_basic_postgres_fixture(postgres):
    postgres.execute("select 1")


def test_basic_redshift_fixture(redshift):
    redshift.execute("select 1")


def test_basic_postgres_and_redshift_fixture(postgres, redshift):
    postgres.execute("select 1")
    redshift.execute("select 1")


redshift_2 = create_redshift_fixture(database_name="redshift2")
redshift_3 = create_redshift_fixture(database_name="redshift3")
postgres_2 = create_postgres_fixture(database_name="postgres2")


def test_multiple_postgres_and_redshift_fixture(
    postgres_2, postgres, redshift_2, redshift_3, redshift
):
    postgres_2.execute("select 1")
    postgres.execute("select 1")
    redshift_2.execute("select 1")
    redshift_3.execute("select 1")
    redshift.execute("select 1")


named_postgres = create_postgres_fixture(database_name="HAILmary123")


def test_create_custom_connection(PG_PORT, PG_HOST, named_postgres):
    engine = create_engine(
        "postgresql://{username}:{password}@{host}:{port}/{database}?sslmode=disable".format(
            database="HAILmary123",
            username="user",
            password="password",
            host=PG_HOST,
            port=PG_PORT,
        ),
        isolation_level="AUTOCOMMIT",
    )

    engine.execute("select 1")


def test_bad_actions(postgres):
    with pytest.raises(ValueError) as e:
        _run_actions(postgres, ["random_string"])

    assert "create_fixture function takes in sqlalchemy.MetaData or actions as inputs only." in str(
        e
    )
