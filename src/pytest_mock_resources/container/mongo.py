import pytest
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from pytest_mock_resources.container import ContainerCheckFailed, get_container_fn, HOST, IN_CI

# XXX: To become overwritable via pytest config.
config = {
    "username": "user",
    "password": "password",
    "host": HOST,
    "port": 27017 if IN_CI else 28017,
    "root_database": "dev-mongo",
    "image": "mongo:3.6",
}


def get_pymongo_engine(database_name):
    client = MongoClient(
        config["host"], config["port"], username=config["username"], password=config["password"]
    )
    engine = client[database_name]

    # Check if connection exists
    # Throws ConnectionFailure on failure
    engine.command("ismaster")

    return engine


def check_mongo_fn():
    try:
        get_pymongo_engine(config["root_database"])
    except ConnectionFailure:
        raise ContainerCheckFailed(
            "Unable to connect to a presumed MongoDB test container via given config: {}".format(
                config
            )
        )


_mongo_container = pytest.fixture("session")(
    get_container_fn(
        config["image"],
        {27017: config["port"]},
        {
            "MONGO_INITDB_ROOT_USERNAME": config["username"],
            "MONGO_INITDB_ROOT_PASSWORD": config["password"],
        },
        check_mongo_fn,
    )
)
