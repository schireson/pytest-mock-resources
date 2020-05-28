import os
import socket
import time

import docker
import responses

from pytest_mock_resources.compat import functools

IN_CI = os.getenv("CI") == "true"  # type: bool


@functools.lru_cache()
def get_docker_host():
    host = "host.docker.internal"
    try:
        socket.gethostbyname(host)
        return host
    except socket.gaierror:
        return os.environ.get("PYTEST_MOCK_RESOURCES_HOST", "localhost")


class ContainerCheckFailed(Exception):
    """Unable to connect to a Container.
    """


def get_container_fn(name, image, ports, environment, check_fn):
    def wrapped():
        # XXX: moto library may over-mock responses. SEE: https://github.com/spulec/moto/issues/1026
        responses.add_passthru("http+docker")

        def retriable_check_fn(retries):
            while retries:
                retries -= 1
                try:
                    check_fn()
                    return
                except Exception:
                    if not retries:
                        raise
                    time.sleep(1)

        try:
            container = None
            try:
                retriable_check_fn(1)
            except ContainerCheckFailed:
                client = docker.from_env(version="auto")
                container = client.containers.run(
                    image, ports=ports, environment=environment, detach=True, remove=True
                )
                retriable_check_fn(20)

            yield
        except Exception:
            raise

        finally:
            if container:
                container.kill()

    wrapped.__name__ = name

    return wrapped


# flake8: noqa
from pytest_mock_resources.container.mongo import _mongo_container  # isort:skip
from pytest_mock_resources.container.postgres import _postgres_container  # isort:skip
from pytest_mock_resources.container.redis import _redis_container  # isort:skip
from pytest_mock_resources.container.redshift import _redshift_container  # isort:skip
from pytest_mock_resources.container.mysql import _mysql_container # isort:skip
