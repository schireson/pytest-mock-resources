import pytest

from pytest_mock_resources.config import PostgresConfig


@pytest.fixture(scope="session")
def pmr_postgres_config():
    return PostgresConfig(port=None)
