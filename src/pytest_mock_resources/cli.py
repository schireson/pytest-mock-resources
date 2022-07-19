import argparse
import enum
from typing import Dict, Type

from pytest_mock_resources import (
    MongoConfig,
    MysqlConfig,
    PostgresConfig,
    RedisConfig,
    RedshiftConfig,
)
from pytest_mock_resources.config import DockerContainerConfig
from pytest_mock_resources.container.base import container_name, get_container

postgres_image = PostgresConfig().image
mysql_image = MysqlConfig().image
mongo_image = MongoConfig().image


class StubPytestConfig:
    pmr_multiprocess_safe = False
    pmr_cleanup_container = False

    class option:
        pmr_multiprocess_safe = False
        pmr_cleanup_container = False

    def getini(self, attr):
        return getattr(self, attr)


@enum.unique
class FixtureType(enum.Enum):
    mongo = "mongo"
    mysql = "mysql"
    postgres = "postgres"
    redis = "redis"
    redshift = "redshift"

    @classmethod
    def options(cls):
        return ", ".join(fixture_base.value for fixture_base in cls)


_container_producers: Dict[FixtureType, Type[DockerContainerConfig]] = {
    FixtureType.mongo: MongoConfig,
    FixtureType.mysql: MysqlConfig,
    FixtureType.postgres: PostgresConfig,
    FixtureType.redis: RedisConfig,
    FixtureType.redshift: RedshiftConfig,
}


def main():
    parser = create_parser()
    args = parser.parse_args()

    pytestconfig = StubPytestConfig()

    stop = args.stop
    start = not stop

    for fixture_base in args.fixture_bases:
        fixture_type = FixtureType(fixture_base)
        execute(fixture_type, pytestconfig, start=start, stop=stop)


def create_parser():
    # TODO: Add an options arg to DOWN a fixture_base's container
    parser = argparse.ArgumentParser(
        description="Premptively run docker containers to speed up initial startup of PMR Fixtures."
    )
    parser.add_argument(
        "fixture_bases",
        metavar="Fixture Base",
        type=str,
        nargs="+",
        help="Available Fixture Bases: {}".format(FixtureType.options()),
    )
    parser.add_argument(
        "--stop", action="store_true", help="Stop previously started PMR containers"
    )
    return parser


def execute(fixture_type: FixtureType, pytestconfig: StubPytestConfig, start=True, stop=False):
    config_cls = _container_producers[fixture_type]
    config = config_cls()

    if start:
        generator = get_container(pytestconfig, config)
        for _ in generator:
            pass

    if stop:
        from python_on_whales import docker

        name = container_name(fixture_type.value, config.port)
        try:
            container = docker.container.inspect(name)
        except Exception:
            print(f"Failed to stop {fixture_type.value} container")
        else:
            container.kill()


if __name__ == "__main__":
    main()
