import pytest

from pytest_mock_resources.container.postgres import PostgresConfig


@pytest.fixture(scope="session")
def pmr_postgres_config():
    print('asdfasdfasdf')
    return PostgresConfig(port=None)
