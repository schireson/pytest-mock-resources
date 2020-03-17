from __future__ import absolute_import

import contextlib

from sqlalchemy import create_engine
from sqlalchemy.sql.elements import TextClause

from pytest_mock_resources.compat import mock, psycopg2
from pytest_mock_resources.patch.redshift.mock_s3_copy import strip
from pytest_mock_resources.patch.redshift.sqlalchemy import (
    execute_mock_s3_copy_command,
    execute_mock_s3_unload_command,
)


def mock_psycopg2_connect(config, _connect):
    """Patch `psycopg2._connect`.

    Add support for S3 COPY and UNLOAD.
    """

    class CustomCursor(psycopg2.extensions.cursor):
        """A custom cursor class to define a custom execute method."""

        def execute(self, sql, args=None):
            dsn_params = self.connection.get_dsn_parameters()
            engine = create_engine(
                "postgresql+psycopg2://{user}:{password}@{hostname}:{port}/{dbname}".format(
                    user=config.username,
                    password=config.password,
                    hostname=config.host,
                    port=config.port,
                    dbname=dsn_params["dbname"],
                )
            )
            if not isinstance(sql, TextClause) and strip(sql).lower().startswith("copy"):
                return execute_mock_s3_copy_command(sql, engine)
            if not isinstance(sql, TextClause) and strip(sql).lower().startswith("unload"):
                return execute_mock_s3_unload_command(sql, engine)
            return super(CustomCursor, self).execute(sql, args)

    def _mock_psycopg2_connect(*args, **kwargs):
        """Substitute the default cursor with a custom cursor."""
        conn = _connect(*args, **kwargs)
        conn.cursor_factory = CustomCursor
        return conn

    return _mock_psycopg2_connect


@contextlib.contextmanager
def patch_connect(config):
    new_connect = mock_psycopg2_connect(config, _connect=psycopg2._connect)
    with mock.patch("psycopg2._connect", new=new_connect) as p:
        yield p
