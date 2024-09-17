import pytest

from pytest_mock_resources.compat import redis
from pytest_mock_resources.container.base import get_container
from pytest_mock_resources.container.redis import RedisConfig
from pytest_mock_resources.credentials import Credentials


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


def create_redis_fixture(scope="function", decode_responses: bool = False):
    """Produce a Redis fixture.

    Any number of fixture functions can be created. Under the hood they will all share the same
    database server.

    .. note::

       If running tests in parallel, the implementation fans out to different redis "database"s,
       up to a 16 (which is the default container fixed limit). This means you can only run
       up to 16 simultaneous tests.

       Additionally, any calls to `flushall` or any other cross-database calls **will** still
       represent cross-test state.

       Finally, the above notes are purely describing the current implementation, and should not
       be assumed. In the future, the current database selection mechanism may change, or
       databases may not be used altogether.

    Args:
        scope (str): The scope of the fixture can be specified by the user, defaults to "function".
        decode_responses (bool): Whether to decode the responses from redis.

    Raises:
        KeyError: If any additional arguments are provided to the function than what is necessary.
    """

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

        db = redis.Redis(
            host=pmr_redis_config.host,
            port=pmr_redis_config.port,
            db=database_number,
            decode_responses=decode_responses or pmr_redis_config.decode_responses,
        )
        db.flushdb()

        Credentials.assign_from_credentials(
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
