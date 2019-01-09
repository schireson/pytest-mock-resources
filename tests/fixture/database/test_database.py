from pytest_mock_resources import create_postgres_fixture, create_redshift_fixture


def test_basic_sqlite_fixture(sqlite):
    sqlite.execute("select 1")


def test_basic_postgres_fixture(postgres):
    postgres.execute("select 1")


def test_basic_redshift_fixture(redshift):
    redshift.execute("select 1")


def test_basic_postgres_and_redshift_fixture(postgres, redshift):
    postgres.execute("select 1")
    redshift.execute("select 1")


redshift_2 = create_redshift_fixture("redshift2")
redshift_3 = create_redshift_fixture("redshift3")
postgres_2 = create_postgres_fixture("postgres2")


def test_multiple_postgres_and_redshift_fixture(
    postgres_2, postgres, redshift_2, redshift_3, redshift
):
    postgres_2.execute("select 1")
    postgres.execute("select 1")
    redshift_2.execute("select 1")
    redshift_3.execute("select 1")
    redshift.execute("select 1")
