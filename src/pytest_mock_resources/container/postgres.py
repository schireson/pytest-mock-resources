import pytest
import sqlalchemy

from pytest_mock_resources.container import ContainerCheckFailed, get_container_fn, HOST, IN_CI

# XXX: To become overwritable via pytest config.
config = {
    "username": "user",
    "password": "password",
    "host": HOST,
    "port": 5432 if IN_CI else 5532,
    "root_database": "dev",
    "image": "postgres:9.6.10-alpine",
}


def get_sqlalchemy_engine(database_name):
    string = "postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}?sslmode=disable"
    engine = sqlalchemy.create_engine(
        string.format(
            database=database_name,
            username=config["username"],
            password=config["password"],
            host=config["host"],
            port=config["port"],
        ),
        isolation_level="AUTOCOMMIT",
    )

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
