import pytest

from pytest_mock_resources.container import HOST
from pytest_mock_resources.container.presto import config, get_presto_connection


@pytest.fixture(scope="session")
def PRESTO_HOST():
    return config["host"]


@pytest.fixture(scope="session")
def PRESTO_PORT():
    return config["port"]


def create_presto_fixture(**kwargs):
    scope = kwargs.pop("scope", "function")

    if len(kwargs):
        raise KeyError("Unsupported Arguments: {}".format(kwargs))

    @pytest.fixture(scope=scope)
    def _(_presto_container):
        return _create_clean_database()

    return _


def _create_clean_database():
    import prestodb
    
    connection = get_presto_connection()

    # TODO

    return connection
