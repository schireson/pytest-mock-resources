import os
import socket
import time

import docker
import responses

IN_CI = os.getenv("CI") == "true"  # type: bool

HOST = "host.docker.internal"
try:
    socket.gethostbyname(HOST)
except socket.gaierror:
    HOST = os.environ.get("PYTEST_MOCK_RESOURCES_HOST", "localhost")


class ContainerCheckFailed(Exception):
    """Unable to connect to a Container.
    """


def get_container_fn(image, ports, environment, check_fn):
    def wrapped():
        # XXX: moto library may over-mock responses. SEE: https://github.com/spulec/moto/issues/1026
        responses.add_passthru("http+docker")

        def retriable_check_fn(retries):
            while retries:
                retries -= 1
                try:
                    check_fn()
                    return
                except Exception as e:
                    if not retries:
                        raise e
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

        finally:
            if container:
                container.kill()

    return wrapped


from pytest_mock_resources.container.mongo import _mongo_container  # noqa, isort:skip
from pytest_mock_resources.container.postgres import _postgres_container  # noqa, isort:skip
