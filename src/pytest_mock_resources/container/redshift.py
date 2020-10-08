import pytest


@pytest.fixture(scope="session")
def _redshift_container(_postgres_container):
    return _postgres_container
