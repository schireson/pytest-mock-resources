import pytest

from pytest_mock_resources.container import ContainerCheckFailed, get_container_fn, HOST, IN_CI

# XXX: To become overwritable via pytest config.
config = {
    "host": HOST,
    "port": 8080 if IN_CI else 8080,
    "user": "presto",
    "catalog": "hive",
    "image": "starburstdata/presto",
}


def get_presto_connection():
    import prestodb

    return prestodb.dbapi.Connection(
        host=config["host"], port=config["port"], user=config["user"], catalog=config["catalog"]
    )


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


_presto_container = pytest.fixture("session")(
    get_container_fn(
        "_presto_container", config["image"], {8080: config["port"]}, {}, check_presto_fn
    )
)
