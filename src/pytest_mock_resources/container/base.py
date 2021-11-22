import time

import docker
import responses


class ContainerCheckFailed(Exception):
    """Unable to connect to a Container."""


def get_container(config, ports, environment, check_fn):
    # XXX: moto library may over-mock responses. SEE: https://github.com/spulec/moto/issues/1026
    responses.add_passthru("http+docker")

    def retriable_check_fn(retries):
        while retries:
            retries -= 1
            try:
                check_fn(config)
                return
            except ContainerCheckFailed:
                if not retries:
                    raise
                time.sleep(0.5)

    client = docker.from_env(version="auto")

    # The creation of container can fail and leave us in a situation where it's
    # we will need to know whether it's been created already or not.
    container = None

    try:

        try:
            retriable_check_fn(1)
        except ContainerCheckFailed:
            try:
                container = client.containers.run(
                    config.image, ports=ports, environment=environment, detach=True, remove=True
                )
            except docker.errors.APIError as e:
                if "port is already allocated" not in str(e):
                    raise

            retriable_check_fn(40)

        yield
    except Exception:
        raise

    finally:
        if container:
            container.kill()

        client.close()
