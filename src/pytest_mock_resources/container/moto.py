from typing import ClassVar, Iterable

from pytest_mock_resources.config import DockerContainerConfig
from pytest_mock_resources.container.base import ContainerCheckFailed


class MotoConfig(DockerContainerConfig):
    """Define the configuration object for moto.

    Args:
        image (str): The docker image:tag specifier to use for postgres containers.
            Defaults to :code:`"postgres:9.6.10-alpine"`.
        host (str): The hostname under which a mounted port will be available.
            Defaults to :code:`"localhost"`.
        port (int): The port to bind the container to.
            Defaults to :code:`5532`.
        ci_port (int): The port to bind the container to when a CI environment is detected.
            Defaults to :code:`5432`.
    """

    name = "moto"

    _fields: ClassVar[Iterable] = {"image", "host", "port"}
    _fields_defaults: ClassVar[dict] = {
        "image": "motoserver/moto:4.0.6",
        "port": 5555,
    }

    def ports(self):
        return {5000: self.port}

    def check_fn(self):
        import requests

        try:
            url = endpoint_url(self)
            requests.get(url, timeout=60)
        except requests.exceptions.RequestException:
            raise ContainerCheckFailed(
                f"Unable to connect to a presumed moto test container via given config: {self}"
            )


def endpoint_url(config):
    return f"http://{config.host}:{config.port}"
