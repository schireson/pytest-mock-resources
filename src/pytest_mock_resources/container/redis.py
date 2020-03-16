import pytest

from pytest_mock_resources.compat import redis
from pytest_mock_resources.config import DockerContainerConfig, fallback
from pytest_mock_resources.container import ContainerCheckFailed, get_container_fn


class RedisConfig(DockerContainerConfig):
    name = "redis"

    _fields = {"image", "host", "port", "ci_port", "root_database"}
    _fields_defaults = {
        "image": "redis:5.0.7",
        "port": 6380,
        "ci_port": 6379,
    }


@pytest.fixture(scope="session")
def pmr_redis_config():
    return RedisConfig()


def check_redis_fn(config):
    def _check_redis_fn():
        try:
            client = redis.Redis(host=config.host, port=config.port)
            client.ping()
        except redis.ConnectionError:
            raise ContainerCheckFailed(
                "Unable to connect to a presumed Redis test container via given config: {}".format(
                    redis_config
                )
            )

    return _check_redis_fn


@pytest.fixture(scope="session")
def _redis_container(pmr_redis_config):
    fn = get_container_fn(
        name="pmr_redis_container",
        image=redis_config["image"],
        ports={6379: redis_config["port"]},
        environment={},
        check_fn=check_redis_fn,
    )
    result = fn()

    for item in result:
        yield item
