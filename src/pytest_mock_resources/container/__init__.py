import os
import socket
import subprocess  # nosec
import time

import docker
import responses

from pytest_mock_resources import logger

IN_CI = os.getenv("CI") == "true"  # type: bool

HOST = "host.docker.internal"
try:
    socket.gethostbyname(HOST)
except socket.gaierror:
    HOST = os.environ.get("PYTEST_MOCK_RESOURCES_HOST", "localhost")


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


def get_compose_fn(name, compose_dir, check_fn):
    def wrapped():
        # XXX: moto library may over-mock responses. SEE: https://github.com/spulec/moto/issues/1026
        responses.add_passthru("http+docker")

        def retriable_check_fn(retries):
            while retries:
                retries -= 1
                try:
                    check_fn()
                    logger.info(f"{name} is up and running")
                    return
                except Exception:
                    logger.info(f"{name} is still starting up")
                    if not retries:
                        raise
                    time.sleep(1)

        try:
            logger.info(f"Starting up {name}")
            subprocess.run(["docker-compose", "-f", compose_dir, "up", "-d", "-V"])  # nosec
            start_time = time.time()

            logger.info(f"Checking to see if {name} is up and running")
            retriable_check_fn(60)

            end_time = time.time()
            elapsed_seconds = end_time - start_time
            logger.info(f"{name} became ready in {elapsed_seconds} seconds.")
            yield
        except Exception:
            raise
        finally:
            subprocess.run(["docker-compose", "-f", compose_dir, "down", "-v"])  # nosec

    wrapped.__name__ = name

    return wrapped


from pytest_mock_resources.container.mongo import _mongo_container  # noqa, isort:skip
from pytest_mock_resources.container.postgres import _postgres_container  # noqa, isort:skip
from pytest_mock_resources.container.presto import _presto_container  # noqa, isort:skip
