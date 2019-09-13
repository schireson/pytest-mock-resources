import pytest

from pytest_mock_resources import create_mongo_fixture

mongo = create_mongo_fixture()


@pytest.mark.mongo
def test_basic_mongo_fixture(mongo):
    collections = mongo.list_collection_names()
    assert collections == []


@pytest.mark.mongo
def test_collection_exists(mongo):
    collection = mongo["customers"]
    to_insert = {"name": "John", "address": "Highway 37"}
    collection.insert_one(to_insert)
    collections = mongo.list_collection_names()
    assert "customers" in collections


@pytest.mark.mongo
def test_insert_one(mongo):
    collection = mongo["customers"]
    to_insert = {"name": "John", "address": "Highway 37"}
    collection.insert_one(to_insert)
    returned = collection.find_one()
    assert returned == to_insert


@pytest.mark.mongo
def test_insert_all(mongo):
    collection = mongo["customers"]
    to_insert = [
        {"name": "Amy", "address": "Apple st 652"},
        {"name": "Hannah", "address": "Mountain 21"},
        {"name": "Michael", "address": "Valley 345"},
        {"name": "Sandy", "address": "Ocean blvd 2"},
        {"name": "Betty", "address": "Green Grass 1"},
        {"name": "Richard", "address": "Sky st 331"},
        {"name": "Susan", "address": "One way 98"},
        {"name": "Vicky", "address": "Yellow Garden 2"},
        {"name": "Ben", "address": "Park Lane 38"},
        {"name": "William", "address": "Central st 954"},
        {"name": "Chuck", "address": "Main Road 989"},
        {"name": "Viola", "address": "Sideway 1633"},
    ]
    collection.insert_many(to_insert)
    result = collection.find().sort("name")
    returned = [row for row in result]
    assert returned == sorted(to_insert, key=lambda x: x["name"])


@pytest.mark.mongo
def test_query(mongo):
    collection = mongo["customers"]
    to_insert = [
        {"name": "John", "address": "Highway 37"},
        {"name": "Viola", "address": "Highway 37"},
    ]
    collection.insert_many(to_insert)

    query = {"address": "Highway 37"}
    result = collection.find(query).sort("name")
    returned = [row for row in result]
    assert returned == sorted(to_insert, key=lambda x: x["name"])


@pytest.mark.mongo
def test_delete_one(mongo):
    collection = mongo["customers"]
    to_insert = [
        {"name": "John", "address": "Highway 37"},
        {"name": "Viola", "address": "Highway 37"},
    ]
    collection.insert_many(to_insert)

    query = {"name": {"$regex": "^J"}}
    collection.delete_one(query)
    result = collection.find().sort("name")
    returned = [row for row in result]

    assert returned == sorted(to_insert[1:], key=lambda x: x["name"])


@pytest.mark.mongo
def test_delete_all(mongo):
    collection = mongo["customers"]
    to_insert = [
        {"name": "John", "address": "Highway 37"},
        {"name": "Viola", "address": "Highway 37"},
    ]
    collection.insert_many(to_insert)

    query = {"address": "Highway 37"}
    collection.delete_many(query)

    result = collection.find()
    returned = [row for row in result]

    assert returned == []


mongo_1 = create_mongo_fixture()
mongo_2 = create_mongo_fixture()
mongo_3 = create_mongo_fixture()


@pytest.mark.mongo
def test_multiple_mongos(mongo_1, mongo_2, mongo_3):
    def validate_isolation(db_client):
        collection = db_client["customers"]
        to_insert = [
            {"name": "John", "address": "Highway 37"},
            {"name": "Viola", "address": "Highway 37"},
        ]
        collection.insert_many(to_insert)

        result = collection.find().sort("name")
        returned = [row for row in result]

        assert returned == to_insert

    validate_isolation(mongo_1)
    validate_isolation(mongo_2)
    validate_isolation(mongo_3)


@pytest.mark.mongo
def test_create_custom_connection(mongo, MONGO_HOST, MONGO_PORT):
    from pymongo import MongoClient

    client = MongoClient(
        MONGO_HOST,
        MONGO_PORT,
        username=mongo.config["username"],
        password=mongo.config["password"],
        authSource=mongo.config["database"],
    )
    db = client[mongo.config["database"]]

    collection = db["customers"]
    to_insert = [
        {"name": "John", "address": "Highway 37"},
        {"name": "Viola", "address": "Highway 37"},
    ]
    collection.insert_many(to_insert)

    result = collection.find().sort("name")
    returned = [row for row in result]

    assert returned == to_insert
