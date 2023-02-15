from sqlalchemy.orm import Session

from pytest_mock_resources import compat


class Credentials:
    """Return as `pmr_credentials` attribute on supported docker-based fixtures.

    Examples:
        It's also directly dict-able.
        >>> creds = Credentials('d', 'l', 'p', 'baz', 'user', 'pass')
        >>> dict_creds = dict(creds)
    """

    def __init__(self, drivername, host, port, database, username, password):
        self.drivername = drivername
        self.host = host
        self.port = port
        self.database = str(database)
        self.username = username
        self.password = password

    def __iter__(self):
        for item in self.__dict__:
            yield (item, self[item])

    def __getitem__(self, item):
        return self.__dict__[item]

    def as_url(self):
        """Return a stringified dbapi URL string."""
        return self.as_sqlalchemy_url().render_as_string(hide_password=False)

    def as_sqlalchemy_url(self):
        """Return a sqlalchemy :class:`sqlalchemy.engine.url.URL`."""
        return compat.sqlalchemy.URL(
            drivername=self.drivername,
            host=self.host,
            port=self.port,
            database=self.database,
            username=self.username,
            password=self.password,
        )

    def as_sqlalchemy_url_kwargs(self):
        """Return the valid arguments to sqlalchemy :class:`sqlalchemy.engine.url.URL`."""
        return dict(self)

    def as_psycopg2_kwargs(self):
        """Return the valid arguments to sqlalchemy :class:`psycopg2.connect`."""
        return {
            "host": self.host,
            "port": self.port,
            "user": self.username,
            "password": self.password,
            "dbname": self.database,
        }

    def as_mongo_kwargs(self):
        """Return the valid arguments to a mongo client."""
        return {
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "authSource": self.database,
        }

    def as_redis_kwargs(self):
        """Return the valid arguments to a redis client."""
        return {
            "host": self.host,
            "port": self.port,
            "db": int(self.database),
            "username": self.username,
            "password": self.password,
        }

    @classmethod
    def assign_from_connection(cls, connection):
        if isinstance(connection, Session):
            url = connection.connection().engine.url
        else:
            url = connection.url

        instance = cls(
            drivername=url.drivername,
            host=url.host,
            port=url.port,
            username=url.username,
            password=url.password,
            database=url.database,
        )
        connection.pmr_credentials = instance
        return instance

    @classmethod
    def assign_from_credentials(cls, engine, **credentials):
        instance = Credentials(**credentials)
        engine.pmr_credentials = instance
        return instance
