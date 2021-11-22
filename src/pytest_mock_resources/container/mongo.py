import pytest

from pytest_mock_resources.compat import pymongo
from pytest_mock_resources.config import DockerContainerConfig, fallback
from pytest_mock_resources.container.base import ContainerCheckFailed, get_container


class MongoConfig(DockerContainerConfig):
    """Define the configuration object for mongo.

    Args:
        image (str): The docker image:tag specifier to use for mongo containers.
            Defaults to :code:`"mongo:3.6"`.
        host (str): The hostname under which a mounted port will be available.
            Defaults to :code:`"localhost"`.
        port (int): The port to bind the container to.
            Defaults to :code:`28017`.
        ci_port (int): The port to bind the container to when a CI environment is detected.
            Defaults to :code:`27017`.
        root_database (str): The name of the root mongo database to create.
            Defaults to :code:`"dev-mongo"`.
    """

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


def get_pymongo_client(config):
    uri = "mongodb://{}:{}".format(config.host, config.port)

    return pymongo.MongoClient(uri)


def check_mongo_fn(config):
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


@pytest.fixture(scope="session")
def _mongo_container(pmr_mongo_config):
    result = get_container(pmr_mongo_config, {27017: pmr_mongo_config.port}, {}, check_mongo_fn)
    yield next(iter(result))
