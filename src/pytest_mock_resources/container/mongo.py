import pytest

from pytest_mock_resources.compat import pymongo
from pytest_mock_resources.container import (
    ContainerCheckFailed,
    get_container_fn,
    get_docker_host,
    IN_CI,
)

# XXX: To become overwritable via pytest config.
config = {
    "port": 27017 if IN_CI else 28017,
    "root_database": "dev-mongo",
    "image": "mongo:3.6",
}


def get_pymongo_client():
    uri = "mongodb://{}:{}".format(get_docker_host(), config["port"])

    return pymongo.MongoClient(uri)


def check_mongo_fn():
    try:
        client = get_pymongo_client()
        db = client[config["root_database"]]
        db.command("ismaster")
    except pymongo.errors.ConnectionFailure:
        raise ContainerCheckFailed(
            "Unable to connect to a presumed MongoDB test container via given config: {}".format(
                config
            )
        )


_mongo_container = pytest.fixture("session")(
    get_container_fn(
        "_mongo_container", config["image"], {27017: config["port"]}, {}, check_mongo_fn
    )
)
