_resource_kinds = ["postgres", "redshift", "mongo", "redis", "mysql"]


def pytest_configure(config):
    """Register markers for each resource kind.
    """
    for resource_kind in _resource_kinds:
        config.addinivalue_line(
            "markers",
            "postgres: Tests which make use of {kind} fixtures".format(kind=resource_kind),
        )


def pytest_itemcollected(item):
    """Attach markers to each test which uses a fixture of one of the resources.
    """
    if not hasattr(item, "fixturenames"):
        return

    fixturenames = set(item.fixturenames)
    for resource_kind in _resource_kinds:
        resource_fixture = "_{}_container".format(resource_kind)
        if resource_fixture in fixturenames:
            item.add_marker(resource_kind)
