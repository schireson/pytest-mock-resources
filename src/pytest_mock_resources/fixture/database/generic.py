from sqlalchemy.engine.url import URL


class Credentials:
    def __init__(self, drivername, host, port, database, username, password):
        self.drivername = drivername
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password

    def as_url(self):
        return str(self.as_url())

    def as_sqlalchemy_url(self):
        return URL(
            drivername=self.drivername,
            host=self.host,
            port=self.port,
            database=self.database,
            username=self.username,
            password=self.password,
        )

    def as_psycopg2_kwargs(self):
        return {
            "host": self.host,
            "port": self.port,
            "user": self.username,
            "password": self.password,
            "dbname": self.database,
        }

    def as_mongo_kwargs(self):
        return {
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "authSource": self.database,
        }


def assign_fixture_credentials(engine, **credentials):
    engine.pmr_credentials = Credentials(**credentials)
