import pytest
from pytest_mock_resources import create_redis_fixture
from pytest_mock_resources.compat import redis

redis_client = create_redis_fixture()
redis_client_decode = create_redis_fixture(decode_responses=True)

client_parameters = [("redis_client", False), ("redis_client_decode", True)]


def _sets_setup(redis_client):
    redis_client.sadd("friends:leto", "ghanima")
    redis_client.sadd("friends:leto", "duncan")
    redis_client.sadd("friends:paul", "duncan")
    redis_client.sadd("friends:paul", "gurney")


def _hash_setup(redis_client):
    redis_client.hset("user", "name", "foo")
    redis_client.hset("user", "age", 30)


def _list_setup(redis_client):
    redis_client.lpush("dbs", "mongo")
    redis_client.lpush("dbs", "redis")
    redis_client.lpush("dbs", "postgres")
    redis_client.lpush("dbs", "mysql")
    redis_client.lpush("dbs", "mysql_lite")


class TestGeneric:
    def test_basic_redis_fixture(self, redis_client):
        keys = redis_client.keys()
        assert keys == []

    def test_custom_connection(self, redis_client):
        r = redis.Redis(**redis_client.pmr_credentials.as_redis_kwargs())
        r.set("foo", "bar")
        value = r.get("foo").decode("utf-8")
        assert value == "bar"

    def test_custom_connection_url(self, redis_client):
        r = redis.from_url(redis_client.pmr_credentials.as_url())
        r.set("foo", "bar")
        value = r.get("foo").decode("utf-8")
        assert value == "bar"


@pytest.mark.parametrize("redis,is_decoded", client_parameters)
class TestStrings:
    def test_set(self, redis, is_decoded, request):
        redis_client = request.getfixturevalue(redis)

        redis_client.set("foo", "bar")
        value = redis_client.get("foo")
        if not is_decoded:
            value = value.decode("utf-8")
        assert value == "bar"

    def test_append(self, redis, is_decoded, request):
        redis_client = request.getfixturevalue(redis)

        redis_client.set("foo", "bar")
        redis_client.append("foo", "baz")
        value = redis_client.get("foo")
        if not is_decoded:
            value = value.decode("utf-8")
        assert value == "barbaz"

    def test_int_operations(self, redis, is_decoded, request):
        redis_client = request.getfixturevalue(redis)

        redis_client.set("foo", 1)
        redis_client.incr("foo")
        value = redis_client.get("foo")
        if not is_decoded:
            value = value.decode("utf-8")
        assert int(value) == 2

        redis_client.decr("foo")
        value = redis_client.get("foo")
        if not is_decoded:
            value = value.decode("utf-8")
        assert int(value) == 1

        redis_client.incrby("foo", 4)
        value = redis_client.get("foo")
        if not is_decoded:
            value = value.decode("utf-8")
        assert int(value) == 5

        redis_client.decrby("foo", 3)
        value = redis_client.get("foo")
        if not is_decoded:
            value = value.decode("utf-8")

        assert int(value) == 2

    def test_float_operations(self, redis, is_decoded, request):
        redis_client = request.getfixturevalue(redis)

        redis_client.set("foo", 1.2)
        value = redis_client.get("foo")
        if not is_decoded:
            value = value.decode("utf-8")
        assert float(value) == 1.2

        redis_client.incrbyfloat("foo", 4.1)
        value = redis_client.get("foo")
        if not is_decoded:
            value = value.decode("utf-8")
        assert float(value) == 5.3

        redis_client.incrbyfloat("foo", -3.1)
        value = redis_client.get("foo")
        if not is_decoded:
            value = value.decode("utf-8")
        assert float(value) == 2.2

    def test_multiple_keys(self, redis, is_decoded, request):
        redis_client = request.getfixturevalue(redis)

        test_mapping = {"foo": "bar", "baz": 1, "flo": 1.2}
        redis_client.mset(test_mapping)

        value = redis_client.get("foo")
        if not is_decoded:
            value = value.decode("utf-8")
        assert value == "bar"

        value = redis_client.get("baz")
        if not is_decoded:
            value = value.decode("utf-8")
        assert int(value) == 1

        value = redis_client.get("flo")
        if not is_decoded:
            value = value.decode("utf-8")
        assert float(value) == 1.2

    def test_querries(self, redis, is_decoded, request):
        redis_client = request.getfixturevalue(redis)

        test_mapping = {"foo1": "bar1", "foo2": "bar2", "flo": "flo"}
        redis_client.mset(test_mapping)
        foo_keys = redis_client.keys("foo*")
        if is_decoded:
            assert "foo1" in foo_keys
            assert "foo2" in foo_keys
            assert "flo" not in foo_keys
        else:
            assert b"foo1" in foo_keys
            assert b"foo2" in foo_keys
            assert b"flo" not in foo_keys


@pytest.mark.parametrize("redis,is_decoded", client_parameters)
class TestSets:
    def test_sadd(self, redis, is_decoded, request):
        redis_client = request.getfixturevalue(redis)

        _sets_setup(redis_client)
        friends_leto = redis_client.smembers("friends:leto")
        friends_paul = redis_client.smembers("friends:paul")

        if is_decoded:
            assert friends_leto == {"duncan", "ghanima"}
            assert friends_paul == {"gurney", "duncan"}
        else:
            assert friends_leto == {b"duncan", b"ghanima"}
            assert friends_paul == {b"gurney", b"duncan"}

    def test_set_operations(self, redis, is_decoded, request):
        redis_client = request.getfixturevalue(redis)

        _sets_setup(redis_client)
        inter = redis_client.sinter("friends:leto", "friends:paul")
        if is_decoded:
            assert inter == {"duncan"}
        else:
            assert inter == {b"duncan"}

        union = redis_client.sunion("friends:leto", "friends:paul")
        if is_decoded:
            assert union == {"ghanima", "duncan", "gurney"}
        else:
            assert union == {b"ghanima", b"duncan", b"gurney"}

        diff = redis_client.sdiff("friends:leto", "friends:paul")
        if is_decoded:
            assert diff == {"ghanima"}
        else:
            assert diff == {b"ghanima"}

        cardinality_leto = redis_client.scard("friends:leto")
        assert cardinality_leto == 2

        rand_member = redis_client.srandmember("friends:leto")
        assert rand_member in redis_client.smembers("friends:leto")

        redis_client.smove("friends:leto", "friends:paul", "ghanima")
        assert redis_client.sismember("friends:paul", "ghanima")


@pytest.mark.parametrize("redis,is_decoded", client_parameters)
class TestHashes:
    def test_hset(self, redis, is_decoded, request):
        redis_client = request.getfixturevalue(redis)

        _hash_setup(redis_client)
        user = redis_client.hgetall("user")
        if is_decoded:
            assert user == {"name": "foo", "age": "30"}
        else:
            assert user == {b"name": b"foo", b"age": b"30"}

    def test_hash_operations(self, redis, is_decoded, request):
        redis_client = request.getfixturevalue(redis)

        _hash_setup(redis_client)
        assert redis_client.hexists("user", "name")
        assert redis_client.hexists("user", "age")

        keys = redis_client.hkeys("user")
        if is_decoded:
            assert keys == ["name", "age"]
        else:
            assert keys == [b"name", b"age"]

        len = redis_client.hlen("user")
        assert len == 2

        vals = redis_client.hvals("user")
        if is_decoded:
            assert vals == ["foo", "30"]
        else:
            assert vals == [b"foo", b"30"]


@pytest.mark.parametrize("redis,is_decoded", client_parameters)
class TestLists:
    def test_lset(self, redis, is_decoded, request):
        redis_client = request.getfixturevalue(redis)

        _list_setup(redis_client)
        items = redis_client.lrange("dbs", 0, 4)
        if is_decoded:
            assert items == ["mysql_lite", "mysql", "postgres", "redis", "mongo"]
        else:
            assert items == [b"mysql_lite", b"mysql", b"postgres", b"redis", b"mongo"]

    def test_list_operations(self, redis, is_decoded, request):
        redis_client = request.getfixturevalue(redis)

        _list_setup(redis_client)
        assert redis_client.llen("dbs") == 5
        assert redis_client.lindex("dbs", 1) == ("mysql" if is_decoded else b"mysql")
        assert redis_client.lpop("dbs") == (
            "mysql_lite" if is_decoded else b"mysql_lite"
        )

        redis_client.rpush("dbs", "RabbitMQ")
        assert redis_client.rpop("dbs") == ("RabbitMQ" if is_decoded else b"RabbitMQ")

        redis_client.ltrim("dbs", 1, -1)
        rest = redis_client.lrange("dbs", 0, -1)
        assert rest == (
            ["postgres", "redis", "mongo"]
            if is_decoded
            else [b"postgres", b"redis", b"mongo"]
        )
