import pytest
import sqlalchemy

from pytest_mock_resources.container import (
    ContainerCheckFailed,
    get_container_fn,
    get_docker_host,
    IN_CI,
)

# XXX: To become overwritable via pytest config.
config = {
    "username": "user",
    "password": "password",
    "port": 5432 if IN_CI else 5532,
    "root_database": "dev",
    "image": "postgres:9.6.10-alpine",
}


def get_sqlalchemy_engine(database_name, isolation_level=None):
    URI_TEMPLATE = (
        "postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}?sslmode=disable"
    )
    DB_URI = URI_TEMPLATE.format(
        database=database_name,
        username=config["username"],
        password=config["password"],
        host=get_docker_host(),
        port=config["port"],
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


def check_postgres_fn():
    try:
        get_sqlalchemy_engine(config["root_database"])
    except sqlalchemy.exc.OperationalError:
        raise ContainerCheckFailed(
            "Unable to connect to a presumed Postgres test container via given config: {}".format(
                config
            )
        )


_postgres_container = pytest.fixture("session")(
    get_container_fn(
        "_postgres_container",
        config["image"],
        {5432: config["port"]},
        {
            "POSTGRES_DB": config["root_database"],
            "POSTGRES_USER": config["username"],
            "POSTGRES_PASSWORD": config["password"],
        },
        check_postgres_fn,
    )
)
