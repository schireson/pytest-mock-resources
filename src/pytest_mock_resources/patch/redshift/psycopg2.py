import contextlib
from unittest import mock

from sqlalchemy.sql.base import Executable

from pytest_mock_resources.container.postgres import PostgresConfig
from pytest_mock_resources.patch.redshift.mock_s3_copy import mock_s3_copy_command, strip
from pytest_mock_resources.patch.redshift.mock_s3_unload import mock_s3_unload_command


@contextlib.contextmanager
def patch_connect(config: PostgresConfig, database: str):
    try:
        # Not all consumers of redshift may be using psycopg2, so it could be unavailable.
        import psycopg2
    except ImportError:
        yield
        return

    new_connect = mock_psycopg2_connect(config, database, _connect=psycopg2._connect)

    # We patch `psycopg2._connect` specifically because it allows us to patch the
    # connection regardless of the import style used by the caller.
    with mock.patch("psycopg2._connect", new=new_connect) as p:
        yield p


def mock_psycopg2_connect(config: PostgresConfig, database: str, _connect):
    """Patch `psycopg2._connect`.

    Add support for S3 COPY and UNLOAD.
    """
    import psycopg2

    class CustomCursor(psycopg2.extensions.cursor):
        """A custom cursor class to define a custom execute method."""

        def execute(self, sql, args=None):
            if isinstance(sql, Executable):
                return super().execute(sql, args)

            if strip(sql).lower().startswith("copy"):
                mock_s3_copy_command(sql, self)
                sql = "commit"

            if strip(sql).lower().startswith("unload"):
                mock_s3_unload_command(sql, self)
                sql = "commit"

            return super().execute(sql, args)

    def _mock_psycopg2_connect(*args, **kwargs):
        """Substitute the default cursor with a custom cursor."""
        conn = _connect(*args, **kwargs)
        dsn_info = conn.get_dsn_parameters()

        # We want to be sure to *only* patch the cursor's behavior when we think the
        # database connection is for the database we're specifically referencing. This
        # should prevent over-patching for connections which are not relevant to our
        # fixture.
        connection_info_matches = (
            config.host == dsn_info["host"]
            and str(config.port) == dsn_info["port"]
            and database == dsn_info["dbname"]
        )

        if connection_info_matches:
            conn.cursor_factory = CustomCursor
        return conn

    return _mock_psycopg2_connect
