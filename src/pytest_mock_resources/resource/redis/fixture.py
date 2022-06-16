import pytest
import redis

from pytest_mock_resources.config import RedisConfig
from pytest_mock_resources.container import get_container
from pytest_mock_resources.credentials import assign_fixture_credentials


@pytest.fixture(scope="session")
def pmr_redis_config():
    """Override this fixture with a :class:`RedisConfig` instance to specify different defaults.

    Examples:
        >>> @pytest.fixture(scope='session')
        ... def pmr_redis_config():
        ...     return RedisConfig(image="redis:6.0")
    """
    return RedisConfig()


@pytest.fixture(scope="session")
def pmr_redis_container(pytestconfig, pmr_redis_config):
    yield from get_container(pytestconfig, pmr_redis_config)


def create_redis_fixture(scope="function"):
    @pytest.fixture(scope=scope)
    def _(request, pmr_redis_container, pmr_redis_config):
        database_number = 0
        if hasattr(request.config, "workerinput"):
            worker_input = request.config.workerinput
            worker_id = worker_input["workerid"]  # For example "gw0".
            database_number = int(worker_id[2:])

        if database_number >= 16:
            raise ValueError(
                "The redis fixture currently only supports up to 16 parallel executions"
            )

        db = redis.Redis(host=pmr_redis_config.host, port=pmr_redis_config.port, db=database_number)
        db.flushdb()

        assign_fixture_credentials(
            db,
            drivername="redis",
            host=pmr_redis_config.host,
            port=pmr_redis_config.port,
            database=database_number,
            username=None,
            password=None,
        )
        return db

    return _
