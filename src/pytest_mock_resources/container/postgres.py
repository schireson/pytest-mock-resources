import sqlalchemy
import sqlalchemy.exc

from pytest_mock_resources.compat.sqlalchemy import URL
from pytest_mock_resources.config import DockerContainerConfig, fallback
from pytest_mock_resources.container.base import ContainerCheckFailed


class PostgresConfig(DockerContainerConfig):
    """Define the configuration object for postgres.

    Args:
        image (str): The docker image:tag specifier to use for postgres containers.
            Defaults to :code:`"postgres:9.6.10-alpine"`.
        host (str): The hostname under which a mounted port will be available.
            Defaults to :code:`"localhost"`.
        port (int): The port to bind the container to.
            Defaults to :code:`5532`.
        ci_port (int): The port to bind the container to when a CI environment is detected.
            Defaults to :code:`5432`.
        username (str): The username of the root postgres user
            Defaults to :code:`"user"`.
        password (str): The password of the root postgres password
            Defaults to :code:`"password"`.
        root_database (str): The name of the root postgres database to create.
            Defaults to :code:`"dev"`.
        drivername (str): The sqlalchemy driver to use
            Defaults to :code:`"postgresql+psycopg2"`.
    """

    name = "postgres"
    _fields = {
        "image",
        "host",
        "port",
        "ci_port",
        "username",
        "password",
        "root_database",
        "drivername",
    }
    _fields_defaults = {
        "image": "postgres:9.6.10-alpine",
        "port": 5532,
        "ci_port": 5432,
        "username": "user",
        "password": "password",
        "root_database": "dev",
        "drivername": "postgresql+psycopg2",
    }

    @fallback
    def username(self):
        raise NotImplementedError()

    @fallback
    def password(self):
        raise NotImplementedError()

    @fallback
    def root_database(self):
        raise NotImplementedError()

    @fallback
    def drivername(self):
        raise NotImplementedError()

    def ports(self):
        return {5432: self.port}

    def environment(self):
        return {
            "POSTGRES_DB": self.root_database,
            "POSTGRES_USER": self.username,
            "POSTGRES_PASSWORD": self.password,
        }

    def check_fn(self):
        import socket

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((self.host, int(self.port)))
        except (ConnectionRefusedError, socket.error):
            raise ContainerCheckFailed(
                f"Unable to connect to a presumed Postgres test container via given config: {self}"
            )
        finally:
            s.close()


def get_sqlalchemy_engine(config, database_name, async_=False, autocommit=False, **engine_kwargs):
    # For backwards compatibility, our hardcoded default is psycopg2, and async fixtures
    # will not work with psycopg2, so we instead swap the default to the preferred async driver.
    drivername = config.drivername
    if async_ and drivername.endswith("psycopg2"):
        drivername = drivername.replace("psycopg2", "asyncpg")

    url = URL(
        drivername=drivername,
        host=config.host,
        port=config.port,
        username=config.username,
        password=config.password,
        database=database_name,
    )

    if autocommit:
        engine_kwargs["isolation_level"] = "AUTOCOMMIT"

    if getattr(url.get_dialect(), "is_async", None):
        from sqlalchemy.ext.asyncio import create_async_engine

        engine = create_async_engine(url, **engine_kwargs)
    else:
        engine = sqlalchemy.create_engine(url, **engine_kwargs)

    return engine
