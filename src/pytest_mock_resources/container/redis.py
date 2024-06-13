from typing import ClassVar, Iterable

from pytest_mock_resources.compat import redis
from pytest_mock_resources.config import DockerContainerConfig, fallback
from pytest_mock_resources.container.base import ContainerCheckFailed


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
        decode_responses (bool): Whether to decode responses from the server on the client.
            Defaults to :code:`False`.
    """

    name = "redis"

    _fields: ClassVar[Iterable] = {
        "image",
        "host",
        "port",
        "ci_port",
        "decode_responses",
    }
    _fields_defaults: ClassVar[dict] = {
        "image": "redis:5.0.7",
        "port": 6380,
        "ci_port": 6379,
        "decode_responses": False,
    }

    @fallback
    def decode_responses(self):
        raise NotImplementedError()

    def ports(self):
        return {6379: self.port}

    def check_fn(self):
        try:
            client = redis.Redis(host=self.host, port=self.port)
            client.ping()
        except redis.ConnectionError:
            raise ContainerCheckFailed(
                f"Unable to connect to a presumed Redis test container via given config: {self}"
            )
