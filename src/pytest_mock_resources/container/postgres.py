import pytest
import sqlalchemy

from pytest_mock_resources.config import DockerContainerConfig, fallback
from pytest_mock_resources.container import ContainerCheckFailed, get_container_fn


class PostgresConfig(DockerContainerConfig):
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
        database=database_name,
        username=config.username,
        password=config.password,
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
    def _check_postgres_fn():
        try:
            get_sqlalchemy_engine(config, config.root_database)
        except sqlalchemy.exc.OperationalError:
            raise ContainerCheckFailed(
                "Unable to connect to a presumed Postgres test container via given config: {}".format(
                    config
                )
            )

    return _check_postgres_fn


@pytest.fixture("session")
def _postgres_container(pmr_postgres_config):
    fn = get_container_fn(
        "_postgres_container",
        pmr_postgres_config.image,
        {5432: pmr_postgres_config.port},
        {
            "POSTGRES_DB": pmr_postgres_config.root_database,
            "POSTGRES_USER": pmr_postgres_config.username,
            "POSTGRES_PASSWORD": pmr_postgres_config.password,
        },
        check_postgres_fn(pmr_postgres_config),
    )
    result = fn()

    for item in result:
        yield item
