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


def get_sqlalchemy_engine(database_name, isolation_level=None):
    URI_TEMPLATE = (
        "postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}?sslmode=disable"
    )
    DB_URI = URI_TEMPLATE.format(
        database=database_name,
        username=config["username"],
        password=config["password"],
        host=config["host"],
        port=config["port"],
    )

    if isolation_level:
        engine = sqlalchemy.create_engine(DB_URI, isolation_level=isolation_level)
    else:
        engine = sqlalchemy.create_engine(DB_URI)

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


def post_postgres_bootup_fn():
    root_engine = get_sqlalchemy_engine(config["root_database"])

    try:
        root_engine.execute(
            """
            CREATE TABLE IF NOT EXISTS pytest_mock_resource_db(
                id serial
            );
            """
        )
    except sqlalchemy.exc.IntegrityError as e:
        # A race condition may occur during table creation if:
        #  - another process has already created the table
        #  - the current process begins creating the table
        #  - the other process commits the table creation
        #  - the current process tries to commit the table creation
        pass


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
        post_bootup_fn=post_postgres_bootup_fn,
    )
)
