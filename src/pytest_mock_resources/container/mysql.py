import sqlalchemy

from pytest_mock_resources import compat
from pytest_mock_resources.config import DockerContainerConfig, fallback
from pytest_mock_resources.container.base import ContainerCheckFailed


class MysqlConfig(DockerContainerConfig):
    """Define the configuration object for MySql.

    Args:
        image (str): The docker image:tag specifier to use for mysql containers.
            Defaults to :code:`"mysql:5.6"`.
        host (str): The hostname under which a mounted port will be available.
            Defaults to :code:`"localhost"`.
        port (int): The port to bind the container to.
            Defaults to :code:`5532`.
        ci_port (int): The port to bind the container to when a CI environment is detected.
            Defaults to :code:`5432`.
        username (str): The username of the root user
            Defaults to :code:`"user"`.
        password (str): The password of the root password
            Defaults to :code:`"password"`.
        root_database (str): The name of the root database to create.
            Defaults to :code:`"dev"`.
    """

    name = "mysql"
    _fields = {"image", "host", "port", "ci_port", "username", "password", "root_database"}
    _fields_defaults = {
        "image": "mysql:5.6",
        "port": 3406,
        "ci_port": 3306,
        # XXX: For now, username is disabled/ignored. We need root access for PMR
        #      internals.
        "username": "root",
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
        return {3306: self.port}

    def environment(self):
        return {
            "MYSQL_DATABASE": self.root_database,
            "MYSQL_ROOT_PASSWORD": self.password,
        }

    def check_fn(self):
        try:
            get_sqlalchemy_engine(self, self.root_database)
        except sqlalchemy.exc.OperationalError:
            raise ContainerCheckFailed(
                "Unable to connect to a presumed MySQL test container via given config: {}".format(
                    self
                )
            )


def get_sqlalchemy_engine(config, database_name, isolation_level=None):
    DB_URI = str(
        compat.sqlalchemy.URL(
            "mysql+pymysql",
            username=config.username,
            password=config.password,
            host=config.host,
            port=config.port,
            database=database_name,
        )
    )

    options = {}
    if isolation_level:
        options["isolation_level"] = isolation_level

    from pytest_mock_resources.compat import pymysql

    pymysql.connect

    engine = sqlalchemy.create_engine(DB_URI, **options)

    # Verify engine is connected
    engine.connect()

    return engine
