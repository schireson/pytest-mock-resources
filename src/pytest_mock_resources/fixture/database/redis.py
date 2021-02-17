import pytest

from pytest_mock_resources.compat import redis
from pytest_mock_resources.container.redis import RedisConfig
from pytest_mock_resources.fixture.database.generic import assign_fixture_credentials


@pytest.fixture(scope="session")
def pmr_redis_config():
    """Override this fixture with a :class:`RedisConfig` instance to specify different defaults.

    Examples:
        >>> @pytest.fixture(scope='session')
        ... def pmr_redis_config():
        ...     return RedisConfig(image="redis:6.0")
    """
    return RedisConfig()


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
    def _(_redis_container, pmr_redis_config):
        db = redis.Redis(host=pmr_redis_config.host, port=pmr_redis_config.port)
        db.flushall()
        assign_fixture_credentials(
            db,
            drivername="redis",
            host=pmr_redis_config.host,
            port=pmr_redis_config.port,
            database=None,
            username=None,
            password=None,
        )
        return db

    return _
