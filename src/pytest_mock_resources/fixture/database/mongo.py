import pytest
from pymongo import MongoClient

from pytest_mock_resources.container.mongo import config


def create_mongo_fixture(**kwargs):
    scope = kwargs.pop("scope", "function")

    if len(kwargs):
        raise KeyError("Unsupported Arguments: {}".format(kwargs))

    @pytest.fixture(scope=scope)
    def _(_mongo_container):
        engine = _create_clean_database_return_engine()

        return engine

    return _


def _create_clean_database_return_engine():
    #  Connects to the "admin" database with root/example
    client = MongoClient(
        config["host"], config["port"], username=config["username"], password=config["password"]
    )
    db = client["admin"]

    # Create a collection called `pytestMockResourceDbs' in the admin tab if it hasnt already been
    # created.
    dbs_collections = db["pytestMockResourcesDbs"]

    #  create a Document in the `pytestMockResourcesDbs` collection:
    result = dbs_collections.insert_one({})
    db_id = str(result.inserted_id)

    #  Create a database where the name is equal to that ID:
    create_db = client[db_id]

    #  Create a user as that databases owner
    create_db.command("createUser", db_id, pwd=config["password"], roles=["dbOwner"])

    #  pass back an authenticated db connection
    limited_client = MongoClient("localhost", config["port"])
    db = limited_client[db_id]
    db.authenticate(db_id, config["password"])
    return db
