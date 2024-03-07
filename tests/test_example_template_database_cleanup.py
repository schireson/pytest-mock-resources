from unittest.mock import patch

import pytest
from sqlalchemy import text

from pytest_mock_resources import create_postgres_fixture, get_container, PostgresConfig


@pytest.fixture(scope="session")
def pmr_postgres_config():
    return PostgresConfig(port=None)


@pytest.fixture
def pmr_postgres_container(pytestconfig, pmr_postgres_config: PostgresConfig):
    yield from get_container(pytestconfig, pmr_postgres_config)


pg = create_postgres_fixture(session=True)


@pytest.mark.postgres
def test_postgres_template_database_cleanup(pytester, pg):
    """Execute two tests in a subprocess and assert they clean up their databases.

    Normally, two tests sharing a fixture would share a template database and leave
    both their individual test databases and their corresponding template databases
    behind as artifacts.

    This test asserts that the template database and test database are **both** cleaned up.
    """
    pytester.copy_example()

    args = ["-vv", "test_cleanup.py"]

    databases_before = get_databases(pg)

    port = pg.connection().engine.url.port
    assert port

    with patch("os.environ", new={"PORT": port, "CLEAN": "1"}):
        result = pytester.inline_run(*args)
    result.assertoutcome(passed=2, skipped=0, failed=0)

    databases_after = get_databases(pg)
    assert databases_before == databases_after

    # Re-run it after, without cleaning turned on to make sure this isn't a false positive
    with patch("os.environ", new={"PORT": port}):
        result = pytester.inline_run(*args)

    result.assertoutcome(passed=2, skipped=0, failed=0)

    databases_after = get_databases(pg)
    assert databases_before != databases_after


def get_databases(pg):
    return sorted([n for (n,) in pg.execute(text("select datname from pg_database")).all()])
