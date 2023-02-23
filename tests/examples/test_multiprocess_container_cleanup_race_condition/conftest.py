import pytest

from pytest_mock_resources import create_postgres_fixture, PostgresConfig


@pytest.fixture(scope="session")
def pmr_postgres_config():
    return PostgresConfig(port=5433)


pg = create_postgres_fixture()
