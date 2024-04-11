from typing import ClassVar, Iterable

from pytest_mock_resources.container.postgres import PostgresConfig


class RedshiftConfig(PostgresConfig):
    """Define the configuration object for Redshift.

    Args:
        image (str): The docker image:tag specifier to use for Redshift containers.
            Defaults to :code:`"postgres:9.6.10-alpine"`.
        host (str): The hostname under which a mounted port will be available.
            Defaults to :code:`"localhost"`.
        port (int): The port to bind the container to.
            Defaults to :code:`5532`.
        ci_port (int): The port to bind the container to when a CI environment is detected.
            Defaults to :code:`5432`.
        username (str): The username of the root Redshift user
            Defaults to :code:`"user"`.
        password (str): The password of the root Redshift password
            Defaults to :code:`"password"`.
        root_database (str): The name of the root Redshift database to create.
            Defaults to :code:`"dev"`.
        drivername (str): The sqlalchemy driver to use
            Defaults to :code:`"postgresql+psycopg2"`.
    """

    name = "redshift"
    _fields: ClassVar[Iterable] = {
        "image",
        "host",
        "port",
        "ci_port",
        "username",
        "password",
        "root_database",
        "drivername",
    }
    _fields_defaults: ClassVar[dict] = {
        "image": "postgres:9.6.10-alpine",
        "port": 5532,
        "ci_port": 5432,
        "username": "user",
        "password": "password",
        "root_database": "dev",
        "drivername": None,
    }
