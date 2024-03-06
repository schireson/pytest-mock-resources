from __future__ import annotations

import argparse
import sys

from pytest_mock_resources.config import DockerContainerConfig
from pytest_mock_resources.container.base import container_name, get_container
from pytest_mock_resources.hooks import get_docker_client
from pytest_mock_resources.plugin import find_entrypoints, load_entrypoints


class StubPytestConfig:
    pmr_multiprocess_safe = False
    pmr_cleanup_container = False
    pmr_docker_client = None

    class option:  # noqa: N801
        pmr_multiprocess_safe = False
        pmr_cleanup_container = False

    def getini(self, attr):
        return getattr(self, attr)


def main():
    entrypoints = find_entrypoints()
    load_entrypoints(entrypoints)

    parser = create_parser()
    args = parser.parse_args()

    if args.load:
        load_entrypoints(args.load)

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
        description="Preemptively run docker containers to speed up initial startup of PMR Fixtures."
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

    parser.add_argument(
        "--load",
        action="append",
        help="Import a module in order to load 3rd party resources.",
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
        docker = get_docker_client(config)

        assert config.port
        name = container_name(fixture, int(config.port))
        try:
            container = docker.container.inspect(name)
        except Exception:
            sys.stderr.write(f"Failed to stop {fixture} container\n")
        else:
            container.kill()


if __name__ == "__main__":
    main()
