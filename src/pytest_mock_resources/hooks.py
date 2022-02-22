import warnings

_resource_kinds = ["postgres", "redshift", "mongo", "redis", "mysql"]


def pytest_addoption(parser):
    parser.addini(
        "pmr_multiprocess_safe",
        "Enables multiprocess-safe mode",
        type='bool',
        default=False,
    )

    group = parser.getgroup("collect")
    group.addoption(
        "--pmr-multiprocess-safe",
        action="store_true",
        default=False,
        help="Enable multiprocess-safe mode",
        dest="pmr_multiprocess_safe",
    )


def use_multiprocess_safe_mode(config):
    cli_enabled = config.option.pmr_multiprocess_safe
    if cli_enabled:
        return True

    config_enabled = config.getini("pmr_multiprocess_safe")
    return config_enabled


def pytest_configure(config):
    """Register markers for each resource kind."""
    for resource_kind in _resource_kinds:
        config.addinivalue_line(
            "markers",
            "{kind}: Tests which make use of {kind} fixtures".format(kind=resource_kind),
        )

    config._pmr_containers = []


def pytest_itemcollected(item):
    """Attach markers to each test which uses a fixture of one of the resources."""
    if not hasattr(item, "fixturenames"):
        return

    fixturenames = set(item.fixturenames)
    for resource_kind in _resource_kinds:
        resource_fixture = "_{}_container".format(resource_kind)
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
        import docker
    except ImportError:
        return

    # We ought to avoid performing deep imports here, this file is auto-loaded
    # by pytest plugin machinery.
    from pytest_mock_resources.config import get_env_config
    from pytest_mock_resources.container.base import get_tmp_root, load_container_lockfile

    # Kind of a neat side-effect of using the below lock file is that if past
    # PMR runs failed to clean up their container, subsequent runs. Ironically
    # this might also lead to literal concurrent runs of unrelated PMR-enabled
    # pytest runs to clobber one another...:shrug:.
    fn = get_tmp_root(session.config)
    with load_container_lockfile(fn) as containers:
        if not containers:
            return

        version = get_env_config("docker", "api_version", "auto")
        client = docker.from_env(version=version)
        while containers:
            container_id = containers.pop(0)

            try:
                container = client.containers.get(container_id)
            except Exception:
                warnings.warn(f"Unrecognized container {container_id}")
            else:
                try:
                    container.kill()
                except Exception:
                    warnings.warn(f"Failed to kill container {container_id}")

    fn.unlink()
