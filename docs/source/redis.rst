Redis
=====

Users can test Redis dependent code using the `create_redis_fixture`.

.. autofunction:: pytest_mock_resources.create_redis_fixture

Consider the following example:

.. code-block:: python

    # src/some_module.py

    def insert_into_friends(redis_client):
        redis_client.sadd("friends:leto", "ghanima")
        redis_client.sadd("friends:leto", "duncan")
        redis_client.sadd("friends:paul", "duncan")
        redis_client.sadd("friends:paul", "gurney")

A user can test this as follows:

.. code-block:: python

    # tests/some_test.py

    from pytest_mock_resources import create_redis_fixture
    from some_module import insert_into_friends

    redis = create_redis_fixture()

    def test_insert_into_friends(redis):
        insert_into_friends(redis)

        friends_leto = redis.smembers("friends:leto")
        friends_paul = redis.smembers("friends:paul")

        assert friends_leto == {b"duncan", b"ghanima"}
        assert friends_paul == {b"gurney", b"duncan"}


Manual Engine Creation
----------------------

Engines can be created manually via the fixture's yielded attributes/REDIS_* fixtures:

.. code-block:: python

    # tests/some_test.py

    from redis import Redis

    from pytest_mock_resources import create_redis_fixture

    redis = create_redis_fixture()


    def test_create_custom_connection(redis):
        client = Redis(**redis.pmr_credentials.as_redis_kwargs())
        client.set("foo", "bar")
        client.append("foo", "baz")
        value = client.get("foo").decode("utf-8")
        assert value == "barbaz"
