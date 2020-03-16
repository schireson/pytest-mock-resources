import pytest

from pytest_mock_resources.compat import pymongo
from pytest_mock_resources.config import DockerContainerConfig, fallback
from pytest_mock_resources.container import ContainerCheckFailed, get_container_fn


class MongoConfig(DockerContainerConfig):
    name = "mongo"

    _fields = {"image", "host", "port", "ci_port", "root_database"}
    _fields_defaults = {
        "image": "mongo:3.6",
        "port": 28017,
        "ci_port": 27017,
        "root_database": "dev-mongo",
    }

    @fallback
    def root_database(self):
        raise NotImplementedError()


@pytest.fixture(scope="session")
def pmr_mongo_config():
    return MongoConfig()


def get_pymongo_client(config):
    uri = "mongodb://{}:{}".format(config.host, config.port)

    return pymongo.MongoClient(uri)


def check_mongo_fn(config):
    def _check_mongo_fn():
        try:
            client = get_pymongo_client(config)
            db = client[config.root_database]
            db.command("ismaster")
        except pymongo.errors.ConnectionFailure:
            raise ContainerCheckFailed(
                "Unable to connect to a presumed MongoDB test container via given config: {}".format(
                    config
                )
            )

    return _check_mongo_fn


@pytest.fixture(scope="session")
def _mongo_container(pmr_mongo_config):
    fn = get_container_fn(
        "_mongo_container",
        pmr_mongo_config.image,
        {27017: pmr_mongo_config.port},
        {},
        check_mongo_fn(pmr_mongo_config),
    )
    result = fn()

    for item in result:
        yield item
