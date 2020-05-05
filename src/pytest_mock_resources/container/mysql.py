import pytest
import sqlalchemy

from pytest_mock_resources.container import (
    ContainerCheckFailed,
    get_container_fn,
    get_docker_host,
    IN_CI,
)

config = {
    "username": "root",
    "password": "password",
    "port": 3306 if IN_CI else 3406,
    "root_database": "dev",
    "image": "mysql:5.6",
}


def get_sqlalchemy_engine(database_name, isolation_level=None):
    URI_TEMPLATE = (
        "mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
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

    from pytest_mock_resources.compat import pymysql

    pymysql.connect

    engine = sqlalchemy.create_engine(DB_URI, **options)

    # Verify engine is connected
    engine.connect()

    return engine


def check_mysql_fn():
    try:
        get_sqlalchemy_engine(config["root_database"])
    except sqlalchemy.exc.OperationalError:
        raise ContainerCheckFailed(
            "Unable to connect to a presumed MySQL test container via given config: {}".format(
                config
            )
        )


_mysql_container = pytest.fixture("session")(
    get_container_fn(
        "_mysql_container",
        config["image"],
        {3306: config["port"]},
        {
            "MYSQL_DATABASE": config["root_database"],
            # "MYSQL_USER": config["username"],
            # "MYSQL_PASSWORD": config["password"],
            "MYSQL_ROOT_PASSWORD": config["password"]
        },
        check_mysql_fn,
    )
)
