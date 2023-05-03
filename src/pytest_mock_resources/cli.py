from __future__ import annotations

import argparse

from pytest_mock_resources.config import DockerContainerConfig
from pytest_mock_resources.container.base import container_name, get_container


class StubPytestConfig:
    pmr_multiprocess_safe = False
    pmr_cleanup_container = False

    class option:
        pmr_multiprocess_safe = False
        pmr_cleanup_container = False

    def getini(self, attr):
        return getattr(self, attr)


def main():
    parser = create_parser()
    args = parser.parse_args()

    pytestconfig = StubPytestConfig()

    stop = args.stop
    start = not stop

    for fixture in args.fixtures:
        if fixture not in DockerContainerConfig.subclasses:
            valid_options = ", ".join(DockerContainerConfig.subclasses)
            raise argparse.ArgumentError(
                args.fixtures,
                f"'{fixture}' invalid. Valid options include: {valid_options}",
            )

        execute(fixture, pytestconfig, start=start, stop=stop)


def create_parser():
    parser = argparse.ArgumentParser(
        description="Premptively run docker containers to speed up initial startup of PMR Fixtures."
    )
    parser.add_argument(
        "fixtures",
        metavar="Fixture",
        type=str,
        nargs="+",
        help="Available Fixtures: {}".format(", ".join(DockerContainerConfig.subclasses)),
    )
    parser.add_argument(
        "--stop", action="store_true", help="Stop previously started PMR containers"
    )
    return parser


def execute(fixture: str, pytestconfig: StubPytestConfig, start=True, stop=False):
    config_cls = DockerContainerConfig.subclasses[fixture]
    config = config_cls()

    if start:
        generator = get_container(pytestconfig, config)
        for _ in generator:
            pass

    if stop:
        from python_on_whales import docker

        assert config.port
        name = container_name(fixture, int(config.port))
        try:
            container = docker.container.inspect(name)
        except Exception:
            print(f"Failed to stop {fixture} container")
        else:
            container.kill()


if __name__ == "__main__":
    main()
