import pytest

from pytest_mock_resources.compat import redis
from pytest_mock_resources.container import (
    ContainerCheckFailed,
    get_container_fn,
    get_docker_host,
    IN_CI,
)

redis_config = {
    "port": 6379 if IN_CI else 6380,
    "image": "redis:5.0.7",
}


def check_redis_fn():
    try:
        client = redis.Redis(host=get_docker_host(), port=redis_config["port"])
        client.ping()
    except redis.ConnectionError:
        raise ContainerCheckFailed(
            "Unable to connect to a presumed Redis test container via given config: {}".format(
                redis_config
            )
        )


_redis_container = pytest.fixture(scope="session")(
    get_container_fn(
        name="pmr_redis_container",
        image=redis_config["image"],
        ports={6379: redis_config["port"]},
        environment={},
        check_fn=check_redis_fn,
    )
)
