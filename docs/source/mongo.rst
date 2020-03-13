Mongo
=====

Users can test MongoDB dependant code using the `create_mongo_fixture`.

Consider the following example:

.. code-block:: python

    # src/some_module.py

    def insert_into_customer(mongodb_connection):
        collection = mongodb_connection['customer']
        to_insert = {"name": "John", "address": "Highway 37"}
        collection.insert_one(to_insert)

A user can test this as follows:

.. code-block:: python

    # tests/some_test.py

    from pytest_mock_resources import create_mongo_fixture
    from some_module import insert_into_customer

    mongo = create_mongo_fixture()

    def test_insert_into_customer(mongo):
        insert_into_customer(mongo)

        collection = mongo['customer']
        returned = collection.find_one()

        assert returned == {"name": "John", "address": "Highway 37"}


Custom Connections
------------------

Custom connections can also be generated via the fixture's yielded attributes/MONGO_* fixtures:

.. code-block:: python

    # tests/some_test.py

    from pymongo import MongoClient

    from pytest_mock_resources import create_mongo_fixture

    mongo = create_mongo_fixture()


    def test_create_custom_connection(mongo):
        client = MongoClient(**mongo.pmr_credentials.as_mongo_kwargs())
        db = client[mongo.config["database"]]

        collection = db["customers"]
        to_insert = [
            {"name": "John"},
            {"name": "Viola"},
        ]
        collection.insert_many(to_insert)

        result = collection.find().sort("name")
        returned = [row for row in result]

        assert returned == to_insert
