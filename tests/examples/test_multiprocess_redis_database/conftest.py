import pytest

from pytest_mock_resources import create_redis_fixture, RedisConfig


@pytest.fixture(scope="session")
def pmr_redis_config():
    return RedisConfig(port=6380)


redis = create_redis_fixture()
