import pytest

from pytest_mock_resources.compat import redis
from pytest_mock_resources.config import DockerContainerConfig
from pytest_mock_resources.container.base import ContainerCheckFailed, get_container


class RedisConfig(DockerContainerConfig):
    """Define the configuration object for redis.

    Args:
        image (str): The docker image:tag specifier to use for redis containers.
            Defaults to :code:`"redis:5.0.7"`.
        host (str): The hostname under which a mounted port will be available.
            Defaults to :code:`"localhost"`.
        port (int): The port to bind the container to.
            Defaults to :code:`6380`.
        ci_port (int): The port to bind the container to when a CI environment is detected.
            Defaults to :code:`6379`.
    """

    name = "redis"

    _fields = {"image", "host", "port", "ci_port"}
    _fields_defaults = {
        "image": "redis:5.0.7",
        "port": 6380,
        "ci_port": 6379,
    }


def check_redis_fn(config):
    try:
        client = redis.Redis(host=config.host, port=config.port)
        client.ping()
    except redis.ConnectionError:
        raise ContainerCheckFailed(
            "Unable to connect to a presumed Redis test container via given config: {}".format(
                config
            )
        )


@pytest.fixture(scope="session")
def _redis_container(pmr_redis_config):
    result = get_container(
        pmr_redis_config,
        ports={6379: pmr_redis_config.port},
        environment={},
        check_fn=check_redis_fn,
    )
    yield next(iter(result))
