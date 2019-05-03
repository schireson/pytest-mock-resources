import argparse
import enum
import subprocess  # nosec


@enum.unique
class FixtureBase(enum.Enum):
    POSTGRES = "postgres"
    MONGO = "mongo"

    @classmethod
    def options(cls):
        return ", ".join(fixture_base.value for fixture_base in cls)

    @property
    def command(self):
        postgres_command = [
            "docker",
            "run",
            "-d",
            "--rm",
            "-p",
            "5532:5432",
            "-e",
            "POSTGRES_DB=dev",
            "-e",
            "POSTGRES_USER=user",
            "-e",
            "POSTGRES_PASSWORD=password",
            "postgres:9.6.10-alpine",
        ]
        mongo_command = ["docker", "run", "-d", "--rm", "-p", "28017:27017", "mongo:3.6"]
        fixture_base_command_map = {
            FixtureBase.MONGO: mongo_command,
            FixtureBase.POSTGRES: postgres_command,
        }

        return fixture_base_command_map[self]


# TODO: Add an options arg to DOWN a fixture_base's container
parser = argparse.ArgumentParser(
    description="Premptively run docker containers to speed up initial startup of PMR Fixtures."
)
parser.add_argument(
    "fixture_bases",
    metavar="Fixture Base",
    type=str,
    nargs="+",
    help="Available Fixture Bases: {}".format(FixtureBase.options()),
)


def main():
    args = parser.parse_args()

    for fixture_base in args.fixture_bases:
        command = FixtureBase(fixture_base).command
        subprocess.run(command)


if __name__ == "__main__":
    main()
