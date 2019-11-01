from sqlalchemy import create_engine
from sqlalchemy.sql.elements import TextClause

from pytest_mock_resources.compat import functools, mock, psycopg2
from pytest_mock_resources.container.postgres import config
from pytest_mock_resources.patch.redshift.create_engine import (
    execute_mock_s3_copy_command,
    execute_mock_s3_unload_command,
)
from pytest_mock_resources.patch.redshift.mock_s3_copy import strip


class CustomCursor(psycopg2.extensions.cursor):
    """A custom cursor class to define a custom execute method."""

    def execute(self, sql, args=None):
        dsn_params = self.connection.get_dsn_parameters()
        engine = create_engine(
            "postgresql+psycopg2://{user}:{password}@{hostname}:{port}/{dbname}".format(
                user=dsn_params["user"],
                password=config["password"],
                hostname=dsn_params["host"],
                port=dsn_params["port"],
                dbname=dsn_params["dbname"],
            )
        )
        if not isinstance(sql, TextClause) and strip(sql).lower().startswith("copy"):
            return execute_mock_s3_copy_command(sql, engine)
        if not isinstance(sql, TextClause) and strip(sql).lower().startswith("unload"):
            return execute_mock_s3_unload_command(sql, engine)
        return super(CustomCursor, self).execute(sql, args)


def patch_psycopg2_connect(path):
    """Patch any occourances of `psycopg2.connect` with mock_psycopg2_connect function.

    The `path` should be the path to the `psycopg2` module you want to patch.
    """

    class MockPsycoPg2:
        """Avoid an infinite circular mock scenario.

        Mocks the whole of psycopg2, so as to not accidentally infinitely mock the mocked `connect`.
        """

        def __getattr(self, name):
            return getattr(psycopg2, name)

        def connect(self, *args, **kwargs):
            return mock_psycopg2_connect(*args, **kwargs)

    def _patch_psycopg2_connect(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with mock.patch(path, new=MockPsycoPg2()):
                return func(*args, **kwargs)

        return wrapper

    return _patch_psycopg2_connect


def mock_psycopg2_connect(*args, **kwargs):
    """Substitute the default cursor with a custom cursor."""
    conn = psycopg2.connect(*args, cursor_factory=CustomCursor, **kwargs)
    return conn
