import pytest
from sqlalchemy import create_engine

from pytest_mock_resources import (
    create_postgres_fixture,
    create_redshift_fixture,
    create_sqlite_fixture,
)
from pytest_mock_resources.fixture.database.relational.generic import EngineManager

sqlite = create_sqlite_fixture()
postgres = create_postgres_fixture()
redshift = create_redshift_fixture()


def test_basic_sqlite_fixture(sqlite):
    sqlite.execute("select 1")


@pytest.mark.postgres
def test_basic_postgres_fixture(postgres):
    postgres.execute("select 1")


@pytest.mark.redshift
def test_basic_redshift_fixture(redshift):
    redshift.execute("select 1")


@pytest.mark.postgres
@pytest.mark.redshift
def test_basic_postgres_and_redshift_fixture(postgres, redshift):
    postgres.execute("select 1")
    redshift.execute("select 1")


redshift_2 = create_redshift_fixture()
redshift_3 = create_redshift_fixture()
postgres_2 = create_postgres_fixture()


@pytest.mark.postgres
@pytest.mark.redshift
def test_multiple_postgres_and_redshift_fixture(
    postgres_2, postgres, redshift_2, redshift_3, redshift
):
    postgres_2.execute("select 1")
    postgres.execute("select 1")
    redshift_2.execute("select 1")
    redshift_3.execute("select 1")
    redshift.execute("select 1")


postgres_3 = create_postgres_fixture()


@pytest.mark.postgres
def test_create_custom_connection(PG_PORT, PG_HOST, postgres_3):
    engine = create_engine(
        "postgresql://{username}:{password}@{host}:{port}/{database}?sslmode=disable".format(
            database=postgres_3.database,
            username="user",
            password="password",
            host=PG_HOST,
            port=PG_PORT,
        ),
        isolation_level="AUTOCOMMIT",
    )

    engine.execute("select 1")


@pytest.mark.postgres
def test_bad_actions(postgres):
    with pytest.raises(ValueError) as e:
        EngineManager(postgres, ordered_actions=["random_string"])._run_actions()

    assert "create_fixture function takes in sqlalchemy.MetaData or actions as inputs only." in str(
        e.value
    )
