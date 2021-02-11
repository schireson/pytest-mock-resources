import pytest
import sqlalchemy
from sqlalchemy.engine.url import URL

from pytest_mock_resources.config import DockerContainerConfig, fallback
from pytest_mock_resources.container.base import ContainerCheckFailed, get_container


class MysqlConfig(DockerContainerConfig):
    """Define the configuration object for MySql.

    Args:
        image (str): The docker image:tag specifier to use for postgres containers.
            Defaults to :code:`"postgres:9.6.10-alpine"`.
        host (str): The hostname under which a mounted port will be available.
            Defaults to :code:`"localhost"`.
        port (int): The port to bind the container to.
            Defaults to :code:`5532`.
        ci_port (int): The port to bind the container to when a CI environment is detected.
            Defaults to :code:`5432`.
        username (str): The username of the root postgres user
            Defaults to :code:`"user"`.
        password (str): The password of the root postgres password
            Defaults to :code:`"password"`.
        root_database (str): The name of the root postgres database to create.
            Defaults to :code:`"dev"`.
    """

    name = "mysql"
    _fields = {"image", "host", "port", "ci_port", "username", "password", "root_database"}
    _fields_defaults = {
        "image": "mysql:5.6",
        "port": 3406,
        "ci_port": 3306,
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


def get_sqlalchemy_engine(config, database_name, isolation_level=None):
    DB_URI = str(
        URL(
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


def check_mysql_fn(config):
    try:
        get_sqlalchemy_engine(config, config.root_database)
    except sqlalchemy.exc.OperationalError:
        raise ContainerCheckFailed(
            "Unable to connect to a presumed MySQL test container via given config: {}".format(
                config
            )
        )


@pytest.fixture(scope="session")
def _mysql_container(pmr_mysql_config):
    result = get_container(
        pmr_mysql_config,
        {3306: pmr_mysql_config.port},
        {
            "MYSQL_DATABASE": pmr_mysql_config.root_database,
            "POSTGRES_USER": pmr_mysql_config.username,
            "MYSQL_ROOT_PASSWORD": pmr_mysql_config.password,
        },
        check_mysql_fn,
    )

    yield next(iter(result))
