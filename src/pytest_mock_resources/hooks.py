import os
import warnings

_resource_kinds = ["postgres", "redshift", "mongo", "redis", "mysql", "moto"]


def pytest_addoption(parser):
    parser.addini(
        "pmr_multiprocess_safe",
        "Enables multiprocess-safe mode",
        type="bool",
        default=False,
    )
    parser.addini(
        "pmr_cleanup_container",
        "Optionally disable attempts to cleanup created containers",
        type="bool",
        default=True,
    )
    parser.addini(
        "pmr_docker_client",
        "Optional docker client name to use: docker, podman, nerdctl",
        type="string",
        default=None,
    )

    group = parser.getgroup("collect")
    group.addoption(
        "--pmr-multiprocess-safe",
        action="store_true",
        default=False,
        help="Enable multiprocess-safe mode",
        dest="pmr_multiprocess_safe",
    )
    group.addoption(
        "--pmr-cleanup-container",
        action="store_true",
        default=True,
        help="Optionally disable attempts to cleanup created containers",
        dest="pmr_cleanup_container",
    )
    group.addoption(
        "--pmr-docker-client",
        default=None,
        help="Optional docker client name to use: docker, podman, nerdctl",
        dest="pmr_docker_client",
    )


def get_pytest_flag(config, name, *, default=None):
    value = getattr(config.option, name, default)
    if value:
        return value

    return config.getini(name)


def use_multiprocess_safe_mode(config):
    return bool(get_pytest_flag(config, "pmr_multiprocess_safe"))


def get_docker_client_name(config) -> str:
    pmr_docker_client = os.getenv("PMR_DOCKER_CLIENT")
    if pmr_docker_client:
        return pmr_docker_client

    docker_client = get_pytest_flag(config, "pmr_docker_client")
    if docker_client:
        return docker_client

    import shutil

    for client_name in ["docker", "podman", "nerdctl"]:
        if shutil.which(client_name):
            break
    else:
        client_name = "docker"

    config.option.pmr_docker_client = client_name
    return client_name


def get_docker_client(config):
    from python_on_whales.docker_client import DockerClient

    client_name = get_docker_client_name(config)
    return DockerClient(client_call=[client_name])


def pytest_configure(config):
    """Register markers for each resource kind."""
    for resource_kind in _resource_kinds:
        config.addinivalue_line(
            "markers",
            f"{resource_kind}: Tests which make use of {resource_kind} fixtures",
        )

    config._pmr_containers = []


def pytest_itemcollected(item):
    """Attach markers to each test which uses a fixture of one of the resources."""
    if not hasattr(item, "fixturenames"):
        return

    fixturenames = set(item.fixturenames)
    for resource_kind in _resource_kinds:
        resource_fixture = f"pmr_{resource_kind}_container"
        if resource_fixture in fixturenames:
            item.add_marker(resource_kind)


def pytest_sessionfinish(session, exitstatus):
    config = session.config

    if not use_multiprocess_safe_mode(config):
        return

    # In the context of multiprocess pytest invocations like pytest-xdist,
    # `workerinput` will be `None` in only the root pytest call.
    workerinput = getattr(session.config, "workerinput", None)
    if workerinput is not None:
        return

    # docker-based fixtures should be optional based on the selected extras.
    try:
        docker = get_docker_client(config)
    except ImportError:
        return

    # We ought to avoid performing deep imports here, this file is auto-loaded
    # by pytest plugin machinery.
    from pytest_mock_resources.container.base import get_tmp_root, load_container_lockfile

    # Kind of a neat side-effect of using the below lock file is that if past
    # PMR runs failed to clean up their container, subsequent runs. Ironically
    # this might also lead to literal concurrent runs of unrelated PMR-enabled
    # pytest runs to clobber one another...:shrug:.
    roots = [get_tmp_root(session.config), get_tmp_root(session.config, parent=True)]
    for fn in roots:
        with load_container_lockfile(fn) as containers:
            if not containers:
                continue

            while containers:
                container_id = containers.pop(0)

                try:
                    container = docker.container.inspect(container_id)
                except Exception:
                    warnings.warn(
                        f"Unrecognized container {container_id}. You may need to manually delete/edit {fn}"
                    )
                else:
                    try:
                        container.kill()
                    except Exception:
                        warnings.warn(f"Failed to kill container {container_id}")

        fn.unlink()
