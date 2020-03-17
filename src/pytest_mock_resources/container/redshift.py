import pytest


@pytest.fixture("session")
def _redshift_container(_postgres_container):
    return _postgres_container
