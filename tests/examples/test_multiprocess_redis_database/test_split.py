"""Produce a test example which would induce a redis database related race condition.

The premise is that given a pytest invocation: `pytest -n 4 test_split.py`,
multiple processes would start up simultaneously, and all connecting to the same
redis database.

The tests would then proceed to clobber one another's values, leading to flaky
tests.

A correct implementation would use some mechanism to avoid this inter-parallel-test
key conflict problem.
"""
import random
import time


def test_node_one(redis, pytestconfig):
    run_test(redis, pytestconfig)


def test_node_two(redis, pytestconfig):
    run_test(redis, pytestconfig)


def test_node_three(redis, pytestconfig):
    run_test(redis, pytestconfig)


def test_node_four(redis, pytestconfig):
    run_test(redis, pytestconfig)


def run_test(redis, pytestconfig):
    worker_id = int(pytestconfig.workerinput["workerid"][2:])
    database = redis.connection_pool.get_connection("set").db
    assert worker_id == database
    print(worker_id, database)

    redis.set("foo", "bar")
    time.sleep(random.randrange(1, 10) / 10)
    value = redis.get("foo")

    assert value == b"bar"

    redis.flushdb()
