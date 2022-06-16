from pytest_mock_resources.container.base import ContainerCheckFailed
from pytest_mock_resources.container.config import DockerContainerConfig, fallback


class MongoConfig(DockerContainerConfig):
    """Define the configuration object for mongo.

    Args:
        image (str): The docker image:tag specifier to use for mongo containers.
            Defaults to :code:`"mongo:3.6"`.
        host (str): The hostname under which a mounted port will be available.
            Defaults to :code:`"localhost"`.
        port (int): The port to bind the container to.
            Defaults to :code:`28017`.
        ci_port (int): The port to bind the container to when a CI environment is detected.
            Defaults to :code:`27017`.
        root_database (str): The name of the root mongo database to create.
            Defaults to :code:`"dev-mongo"`.
    """

    name = "mongo"

    _fields = {"image", "host", "port", "ci_port", "root_database"}
    _fields_defaults = {
        "image": "mongo:3.6",
        "port": 28017,
        "ci_port": 27017,
        "root_database": "dev-mongo",
    }

    @fallback
    def root_database(self):
        raise NotImplementedError()

    def ports(self):
        return {27017: self.port}

    def check_fn(self):
        import pymongo

        try:
            client = pymongo.MongoClient(self.host, self.port)
            db = client[self.root_database]
            db.command("ismaster")
        except pymongo.errors.ConnectionFailure:
            raise ContainerCheckFailed(
                "Unable to connect to a presumed MongoDB test container via given config: {}".format(
                    self
                )
            )


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
        import sqlalchemy.exc

        from pytest_mock_resources.resource.mysql.fixture import get_sqlalchemy_engine

        try:
            get_sqlalchemy_engine(self, self.root_database)
        except sqlalchemy.exc.OperationalError:
            raise ContainerCheckFailed(
                "Unable to connect to a presumed MySQL test container via given config: {}".format(
                    self
                )
            )


class PostgresConfig(DockerContainerConfig):
    """Define the configuration object for postgres.

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

    name = "postgres"
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
        import sqlalchemy.exc

        from pytest_mock_resources.resource.postgres.sqlalchemy import get_sqlalchemy_engine

        try:
            get_sqlalchemy_engine(self, self.root_database)
        except sqlalchemy.exc.OperationalError:
            raise ContainerCheckFailed(
                "Unable to connect to a presumed Postgres test container via given config: {}".format(
                    self
                )
            )


class RedisConfig(DockerContainerConfig):
    """Define the configuration object for redis.

    Args:
        image (str): The docker image:tag specifier to use for redis containers.
            Defaults to :code:`"redis:5.0.7"`.
        host (str): The hostname under which a mounted port will be available.
            Defaults to :code:`"localhost"`.
        port (int): The port to bind the container to.
            Defaults to :code:`6380`.
        ci_port (int): The port to bind the container to when a CI environment is detected.
            Defaults to :code:`6379`.
    """

    name = "redis"

    _fields = {"image", "host", "port", "ci_port"}
    _fields_defaults = {
        "image": "redis:5.0.7",
        "port": 6380,
        "ci_port": 6379,
    }

    def ports(self):
        return {6379: self.port}

    def check_fn(self):
        import redis

        try:
            client = redis.Redis(host=self.host, port=self.port)
            client.ping()
        except redis.ConnectionError:
            raise ContainerCheckFailed(
                "Unable to connect to a presumed Redis test container via given config: {}".format(
                    self
                )
            )


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
        import sqlalchemy.exc

        from pytest_mock_resources.resource.postgres.sqlalchemy import get_sqlalchemy_engine

        try:
            get_sqlalchemy_engine(self, self.root_database)
        except sqlalchemy.exc.OperationalError:
            raise ContainerCheckFailed(
                "Unable to connect to a presumed Redshift test container via given config: {}".format(
                    self
                )
            )
