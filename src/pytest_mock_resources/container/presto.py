import os

import pytest
from pyhive import hive
from thrift.transport.TTransport import TTransportException

import pytest_mock_resources
from pytest_mock_resources.container import ContainerCheckFailed, get_compose_fn, HOST, IN_CI

# XXX: To become overwritable via pytest config.
config = {
    "host": HOST,
    "port": 8080 if IN_CI else 8080,
    "user": "presto",
    "catalog": "default",
    "image": "starburstdata/presto",
}

module_dir = os.path.dirname(pytest_mock_resources.__file__)
docker_compose_dir = os.path.join(
    module_dir, os.pardir, os.pardir, "docker-hive", "docker-compose.yml"
)


def get_presto_connection():
    import prestodb

    return prestodb.dbapi.Connection(
        host=config["host"], port=config["port"], user=config["user"], catalog=config["catalog"]
    )


def get_hive_connection():
    return hive.connect("localhost", database="default")


def check_presto_fn():
    from requests.exceptions import ConnectionError

    try:
        connection = get_presto_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()

    except ConnectionError:
        raise ContainerCheckFailed(
            "Unable to connect to a presumed Presto test container via given config: {}".format(
                config
            )
        )

    try:
        get_hive_connection()
    except TTransportException:
        raise ContainerCheckFailed(
            "Unable to connect to a presumed Presto test container via given config: {}".format(
                config
            )
        )


_presto_container = pytest.fixture("session")(
    get_compose_fn("_presto_container", docker_compose_dir, check_presto_fn)
)
