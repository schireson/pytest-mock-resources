import sqlalchemy

from pytest_mock_resources.config import DockerContainerConfig, fallback
from pytest_mock_resources.container.base import ContainerCheckFailed
from pytest_mock_resources.container.postgres import get_sqlalchemy_engine


class RedshiftConfig(DockerContainerConfig):
    """Define the configuration object for Redshift.

    Args:
        image (str): The docker image:tag specifier to use for Redshift containers.
            Defaults to :code:`"postgres:9.6.10-alpine"`.
        host (str): The hostname under which a mounted port will be available.
            Defaults to :code:`"localhost"`.
        port (int): The port to bind the container to.
            Defaults to :code:`5532`.
        ci_port (int): The port to bind the container to when a CI environment is detected.
            Defaults to :code:`5432`.
        username (str): The username of the root Redshift user
            Defaults to :code:`"user"`.
        password (str): The password of the root Redshift password
            Defaults to :code:`"password"`.
        root_database (str): The name of the root Redshift database to create.
            Defaults to :code:`"dev"`.
    """

    name = "redshift"
    _fields = {"image", "host", "port", "ci_port", "username", "password", "root_database"}
    _fields_defaults = {
        "image": "postgres:9.6.10-alpine",
        "port": 5532,
        "ci_port": 5432,
        "username": "user",
        "password": "password",
        "root_database": "dev",
    }

    @fallback
    def username(self):
        raise NotImplementedError()

    @fallback
    def password(self):
        raise NotImplementedError()

    @fallback
    def root_database(self):
        raise NotImplementedError()

    def ports(self):
        return {5432: self.port}

    def environment(self):
        return {
            "POSTGRES_DB": self.root_database,
            "POSTGRES_USER": self.username,
            "POSTGRES_PASSWORD": self.password,
        }

    def check_fn(self):
        try:
            get_sqlalchemy_engine(self, self.root_database)
        except sqlalchemy.exc.OperationalError:
            raise ContainerCheckFailed(
                "Unable to connect to a presumed Redshift test container via given config: {}".format(
                    self
                )
            )
