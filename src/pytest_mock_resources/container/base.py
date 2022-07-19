import contextlib
import json
import pathlib
import socket
import time

import responses

from pytest_mock_resources.hooks import get_pytest_flag, use_multiprocess_safe_mode

DEFAULT_RETRIES = 40
DEFAULT_INTERVAL = 0.5


class ContainerCheckFailed(Exception):
    """Unable to connect to a Container."""


def retry(func=None, *, args=(), kwargs={}, retries=1, interval=DEFAULT_INTERVAL, on_exc=Exception):
    while retries:
        retries -= 1
        try:
            result = func(*args, **kwargs)
        except on_exc:
            if not retries:
                raise
            time.sleep(interval)
        else:
            return result


def get_container(pytestconfig, config, *, retries=DEFAULT_RETRIES, interval=DEFAULT_INTERVAL):

    multiprocess_safe_mode = use_multiprocess_safe_mode(pytestconfig)

    # XXX: moto library may over-mock responses. SEE: https://github.com/spulec/moto/issues/1026
    responses.add_passthru("http+docker")

    # The creation of container can fail and leave us in a situation where it's
    # we will need to know whether it's been created already or not.
    container = None

    if config.port is None:
        config.set("port", unused_tcp_port())

    run_kwargs = dict(
        publish=[(dest, source) for source, dest in config.ports().items()],
        envs=config.environment(),
        name=container_name(config.name, config.port),
    )

    try:
        if multiprocess_safe_mode:
            from filelock import FileLock

            # get the temp directory shared by all workers (assuming pytest-xdist)
            root_tmp_dir = pytestconfig._tmp_path_factory.getbasetemp().parent
            fn = root_tmp_dir / f"pmr_create_container_{config.port}.lock"
            # wait for the container one process at a time
            with FileLock(str(fn)):
                container = wait_for_container(
                    config.check_fn,
                    run_args=(config.image,),
                    run_kwargs=run_kwargs,
                    retries=retries,
                    interval=interval,
                )
            if container:
                record_container_creation(pytestconfig, container)

        else:
            container = wait_for_container(
                config.check_fn,
                run_args=(config.image,),
                run_kwargs=run_kwargs,
                retries=retries,
                interval=interval,
            )

        yield container
    finally:
        cleanup_container = get_pytest_flag(pytestconfig, "pmr_cleanup_container", default=True)
        if cleanup_container and container and not multiprocess_safe_mode:
            container.kill()


def wait_for_container(
    check_fn, *, run_args, run_kwargs, retries=DEFAULT_RETRIES, interval=DEFAULT_INTERVAL
):
    """Wait for evidence that the container is up and healthy.

    The caller must provide a `check_fn` which should `raise ContainerCheckFailed` if
    it finds that the container is not yet up.
    """
    from python_on_whales import docker

    try:
        from python_on_whales.exceptions import DockerException
    except ImportError:  # pragma: no cover
        from python_on_whales.utils import DockerException

    try:
        # Perform a single attempt, for the happy-path where the container already exists.
        retry(check_fn, retries=1, interval=interval, on_exc=ContainerCheckFailed)
    except ContainerCheckFailed:
        # In the event it doesn't exist, we attempt to start the container
        try:
            container = docker.run(*run_args, **run_kwargs, detach=True, remove=True)
        except DockerException as e:
            container = None
            # This sometimes happens if multiple container fixtures race for the first
            # creation of the container, we want to still retry wait in this case.
            port_allocated_error = "port is already allocated"
            name_allocated_error = "to be able to reuse that name"

            error = str(e)
            if port_allocated_error not in error and name_allocated_error not in error:
                raise

        # And then we perform more lengthy retry cycle.
        retry(check_fn, retries=retries, interval=interval, on_exc=ContainerCheckFailed)
        return container
    return None


def container_name(name: str, port: int) -> str:
    return f"pmr_{name}_{port}"


def record_container_creation(pytestconfig, container):
    """Record the fact of the creation of a container.

    Record both a local reference to the container in pytest's `config` fixture,
    as well as a global PMR lock file of created containers.
    """
    pytestconfig._pmr_containers.append(container)

    fn = get_tmp_root(pytestconfig, parent=True)
    with load_container_lockfile(fn) as data:
        data.append(container.id)
        fn.write_text(json.dumps(data))


def get_tmp_root(pytestconfig, *, parent=False):
    """Get the path to the PMR lock file."""
    tmp_path_factory = pytestconfig._tmp_path_factory

    root_tmp_dir = tmp_path_factory.getbasetemp().parent
    if parent:
        root_tmp_dir = root_tmp_dir.parent

    return root_tmp_dir / "pmr.json"


@contextlib.contextmanager
def load_container_lockfile(path: pathlib.Path):
    """Produce the contents of the given file behind a file lock."""
    import filelock

    with filelock.FileLock(str(path) + ".lock"):
        if path.is_file():
            with open(path, "rb") as f:
                yield json.load(f)
        else:
            yield []


def unused_tcp_port():
    """Find an unused localhost TCP port from 1024-65535 and return it."""
    with contextlib.closing(socket.socket()) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]
