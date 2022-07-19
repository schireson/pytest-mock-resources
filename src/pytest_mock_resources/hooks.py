import warnings

_resource_kinds = ["postgres", "redshift", "mongo", "redis", "mysql"]


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


def get_pytest_flag(config, name, *, default=None):
    value = getattr(config.option, name, default)
    if value:
        return True

    config_value = config.getini(name)
    return config_value


def use_multiprocess_safe_mode(config):
    return get_pytest_flag(config, "pmr_multiprocess_safe")


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
        resource_fixture = "pmr_{}_container".format(resource_kind)
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
        from python_on_whales import docker
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
                    warnings.warn(f"Unrecognized container {container_id}")
                else:
                    try:
                        container.kill()
                    except Exception:
                        warnings.warn(f"Failed to kill container {container_id}")

        fn.unlink()
