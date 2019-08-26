import os
import subprocess  # nosec
import time

import pytest

from pytest_mock_resources.container import ContainerCheckFailed, HOST, IN_CI

# XXX: To become overwritable via pytest config.
config = {
    "host": HOST,
    "port": 8080 if IN_CI else 8080,
    "user": "presto",
    "catalog": "default",
    "image": "starburstdata/presto",
}


@pytest.fixture(scope="session")
def _presto_container():
    os.chdir("docker-hive")

    try:
        subprocess.run(["docker-compose", "up", "-d"])  # nosec
        print("Sleeping...")
        time.sleep(90)
        yield
        subprocess.run(["docker-compose", "down"])  # nosec
    finally:
        os.chdir(os.pardir)


def get_presto_connection():
    import prestodb

    return prestodb.dbapi.Connection(
        host=config["host"], port=config["port"], user=config["user"], catalog=config["catalog"]
    )


def check_presto_fn(_presto_container):
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
