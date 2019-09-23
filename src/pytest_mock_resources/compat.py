class ImportAdaptor(object):
    __wrapped__ = False

    def __init__(self, package, **attrs):
        self.package = package

        for key, value in attrs.items():
            setattr(self, key, value)

    def fail(self):
        raise RuntimeError(
            "Cannot use postgres or redshift fixtures without psycopg2. Install "
            "pytest-mock-resources[postgres]."
        )

    def __getattr__(self, attr):
        self.fail()


try:
    from unittest import mock
except ImportError:
    import mock  # type: ignore # noqa

try:
    import functools32 as functools
except ImportError:
    import functools  # type: ignore # noqa


try:
    import psycopg2
except ImportError:
    psycopg2 = ImportAdaptor("psycopg2", extensions=ImportAdaptor("psycopg2", cursor=ImportAdaptor))
