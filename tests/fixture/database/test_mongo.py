from pytest_mock_resources import create_mongo_fixture

mongo = create_mongo_fixture()


def test_basic_mongo_fixture(mongo):
    collections = mongo.list_collection_names()
    assert collections == []


def test_collection_exists(mongo):
    collection = mongo["customers"]
    to_insert = {"name": "John", "address": "Highway 37"}
    collection.insert_one(to_insert)
    collections = mongo.list_collection_names()
    assert "customers" in collections


def test_insert_one(mongo):
    collection = mongo["customers"]
    to_insert = {"name": "John", "address": "Highway 37"}
    collection.insert_one(to_insert)
    returned = collection.find_one()
    assert returned == to_insert


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
    cursor = collection.find().sort("name")
    returned = [row for row in cursor]
    assert returned == sorted(to_insert, key=lambda x: x["name"])


def test_query(mongo):
    collection = mongo["customers"]
    to_insert = [
        {"name": "John", "address": "Highway 37"},
        {"name": "Viola", "address": "Highway 37"},
    ]
    collection.insert_many(to_insert)

    query = {"address": "Highway 37"}
    cursor = collection.find(query).sort("name")
    returned = [row for row in cursor]
    assert returned == sorted(to_insert, key=lambda x: x["name"])


def test_delete_one(mongo):
    collection = mongo["customers"]
    to_insert = [
        {"name": "John", "address": "Highway 37"},
        {"name": "Viola", "address": "Highway 37"},
    ]
    collection.insert_many(to_insert)

    query = {"name": {"$regex": "^J"}}
    collection.delete_one(query)
    cursor = collection.find().sort("name")
    returned = [row for row in cursor]

    assert returned == sorted(to_insert[1:], key=lambda x: x["name"])


def test_delete_all(mongo):
    collection = mongo["customers"]
    to_insert = [
        {"name": "John", "address": "Highway 37"},
        {"name": "Viola", "address": "Highway 37"},
    ]
    collection.insert_many(to_insert)

    query = {"address": "Highway 37"}
    collection.delete_many(query)

    cursor = collection.find()
    returned = [row for row in cursor]

    assert returned == []
