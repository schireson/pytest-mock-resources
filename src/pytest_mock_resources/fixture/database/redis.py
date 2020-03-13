import pytest

from pytest_mock_resources.compat import redis
from pytest_mock_resources.container import get_docker_host
from pytest_mock_resources.container.redis import redis_config
from pytest_mock_resources.fixture.database.generic import assign_fixture_credentials


def create_redis_fixture(**kwargs):
    """Create a Redis fixture.

    Args:
        scope (str): The scope of the fixture can be specified by the user, defaults to "function".

    Raises:
        KeyError: If any additional arguments are provided to the function than what is necessary.
    """
    scope = kwargs.pop("scope", "function")

    if len(kwargs):
        raise KeyError("Unsupported Arguments: {}".format(kwargs))

    @pytest.fixture(scope=scope)
    def _(_redis_container):
        db = redis.Redis(host=get_docker_host(), port=redis_config["port"])
        db.flushall()
        assign_fixture_credentials(
            db,
            drivername="redis",
            host=get_docker_host(),
            port=redis_config["port"],
            database=None,
            username=None,
            password=None,
        )
        return db

    return _
