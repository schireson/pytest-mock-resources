import pytest
import sqlalchemy

from pytest_mock_resources.config import DockerContainerConfig, fallback
from pytest_mock_resources.container.base import ContainerCheckFailed, get_container


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
    """

    name = "postgres"
    _fields = {"image", "host", "port", "ci_port", "username", "password", "root_database"}
    _fields_defaults = {
        "image": "postgres:9.6.10-alpine",
        "port": 5532,
        "ci_port": 5432,
        "username": "user",
        "password": "password",
        "root_database": "dev",
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


def get_sqlalchemy_engine(config, database_name, isolation_level=None):
    URI_TEMPLATE = (
        "postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}?sslmode=disable"
    )
    DB_URI = URI_TEMPLATE.format(
        host=config.host,
        port=config.port,
        username=config.username,
        password=config.password,
        database=database_name,
    )

    options = {}
    if isolation_level:
        options["isolation_level"] = isolation_level

    # Trigger any psycopg2-based import failures
    from pytest_mock_resources.compat import psycopg2

    psycopg2.connect

    engine = sqlalchemy.create_engine(DB_URI, **options)

    # Verify engine is connected
    engine.connect()

    return engine


def check_postgres_fn(config):
    try:
        get_sqlalchemy_engine(config, config.root_database)
    except sqlalchemy.exc.OperationalError:
        raise ContainerCheckFailed(
            "Unable to connect to a presumed Postgres test container via given config: {}".format(
                config
            )
        )


@pytest.fixture(scope="session")
def _postgres_container(pmr_postgres_config):
    result = get_container(
        pmr_postgres_config,
        {5432: pmr_postgres_config.port},
        {
            "POSTGRES_DB": pmr_postgres_config.root_database,
            "POSTGRES_USER": pmr_postgres_config.username,
            "POSTGRES_PASSWORD": pmr_postgres_config.password,
        },
        check_postgres_fn,
    )

    yield next(iter(result))
