import pytest

from pytest_mock_resources.container import HOST
from pytest_mock_resources.container.mongo import config, get_pymongo_client


@pytest.fixture(scope="session")
def MONGO_HOST():
    return config["host"]


@pytest.fixture(scope="session")
def MONGO_PORT():
    return config["port"]


def create_mongo_fixture(**kwargs):
    scope = kwargs.pop("scope", "function")

    if len(kwargs):
        raise KeyError("Unsupported Arguments: {}".format(kwargs))

    @pytest.fixture(scope=scope)
    def _(_mongo_container):
        return _create_clean_database()

    return _


def _create_clean_database():
    from pymongo import MongoClient

    client = get_pymongo_client()
    db = client[config["root_database"]]

    # Create a collection called `pytestMockResourceDbs' in the admin tab if it hasnt already been
    # created.
    db_collection = db["pytestMockResourcesDbs"]

    #  create a Document in the `pytestMockResourcesDbs` collection:
    result = db_collection.insert_one({})
    db_id = str(result.inserted_id)

    #  Create a database where the name is equal to that ID:
    create_db = client[db_id]

    #  Create a user as that databases owner
    create_db.command("createUser", db_id, pwd="password", roles=["dbOwner"])  # nosec

    #  pass back an authenticated db connection
    limited_client = MongoClient(HOST, config["port"])
    db = limited_client[db_id]
    db.authenticate(db_id, "password")

    db.config = {"username": db_id, "password": "password", "database": db_id}

    return db
