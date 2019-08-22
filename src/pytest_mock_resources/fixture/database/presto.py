import pytest

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
        return get_presto_connection()

    return _
