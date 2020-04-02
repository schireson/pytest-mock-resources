from sqlalchemy.engine.url import URL


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
        self.database = database
        self.username = username
        self.password = password

    def __iter__(self):
        for item in self.__dict__:
            yield (item, self[item])

    def __getitem__(self, item):
        return self.__dict__[item]

    def as_url(self):
        """Return a stringified dbapi URL string.
        """
        return str(self.as_sqlalchemy_url())

    def as_sqlalchemy_url(self):
        """Return a sqlalchemy :class:`sqlalchemy.engine.url.URL`.
        """
        return URL(
            drivername=self.drivername,
            host=self.host,
            port=self.port,
            database=self.database,
            username=self.username,
            password=self.password,
        )

    def as_sqlalchemy_url_kwargs(self):
        """Return the valid arguments to sqlalchemy :class:`sqlalchemy.engine.url.URL`.
        """
        return dict(self)

    def as_psycopg2_kwargs(self):
        """Return the valid arguments to sqlalchemy :class:`psycopg2.connect`.
        """
        return {
            "host": self.host,
            "port": self.port,
            "user": self.username,
            "password": self.password,
            "dbname": self.database,
        }

    def as_mongo_kwargs(self):
        """Return the valid arguments to a mongo client.
        """
        return {
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "authSource": self.database,
        }

    def as_redis_kwargs(self):
        """Return the valid arguments to a redis client.
        """
        return {
            "host": self.host,
            "port": self.port,
            "db": self.database,
            "username": self.username,
            "password": self.password,
        }


def assign_fixture_credentials(engine, **credentials):
    engine.pmr_credentials = Credentials(**credentials)
