import psycopg2
import pytest
from sqlalchemy import create_engine

from pytest_mock_resources.container import ContainerCheckFailed, get_container_fn, HOST, IN_CI

# XXX: To become overwritable via pytest config.
config = {
    "username": "username",
    "password": "password",
    "host": HOST,
    "port": 5432 if IN_CI else 5532,
    "root_database": "root",
    "image": "postgres:9.6.10-alpine",
}


def get_psycopg2_connection(database_name):
    return psycopg2.connect(
        dbname=database_name,
        user=config["username"],
        password=config["password"],
        host=config["host"],
        port=str(config["port"]),
    )


def get_sqlalchemy_engine(database_name):
    return create_engine(
        "postgresql://{username}:{password}@{host}:{port}/{database}?sslmode=disable".format(
            database=database_name,
            username=config["username"],
            password=config["password"],
            host=config["host"],
            port=config["port"],
        ),
        isolation_level="AUTOCOMMIT",
    )


def check_postgres_fn():
    try:
        get_psycopg2_connection(config["root_database"])
    except psycopg2.OperationalError:
        raise ContainerCheckFailed(
            "Unable to connect to a presumed Postgres test container via given config: {}".format(
                config
            )
        )


_postgres_container = pytest.fixture("session")(
    get_container_fn(
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
