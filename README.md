# Schireson Pytest Mock-Resources

\#schiresonip \#ruby

## Introduction

A collection of pytest plugins to make it easier to test against code that depends on external resources like Postgres and Redshift.

Currently available resources:

* Mock Postgres

      from pytest_mock_resources import create_postgres_fixture

* Mock Redshift

      from pytest_mock_resources import create_redshift_fixture

* Mock SQLite

      from pytest_mock_resources import create_sqlite_fixture

Possible future resources:

* Mock MySQL
* Mock S3
* Mock Rabbit Broker

Feel free to file an [issue](https://github.com/schireson/schireson-pytest-mock-resources/issues) if you find any bugs or want to start a conversation around a mock resource you want implemented!

This package assumes you will be testing your code by using `pytest` and as such, leverages pytest fixtures.

If you aren't familiar with Pytest Fixtures, you can read up on them in the [Pytest documentation](https://docs.pytest.org/en/latest/fixture.html).

## Installing

    pip install --index-url https://artifactory.schireson.com/artifactory/api/pypi/pypi/simple "pytest-mock-resources[postgres]"

NOTE: The `[postgres]` suffix in the install command above is only necessary if you plan on using any `redshift` or `postgres` fixtures.

## Setup Pre-Requisites (For Postgres and Redshift Fixtures Only)

### Running the tests in CircleCI

Add the following section to ALL jobs that will be running tests with `redshift` or `postgres` fixtures:

    jobs:
      <YOUR JOB NAME>:
          docker:
          - image: <IMAGE>  // schireson/cicd-python... circleci/python:2.7.14... etc
          - image: postgres:9.6.10-alpine
              environment:
              POSTGRES_DB: dev
              POSTGRES_USER: user
              POSTGRES_PASSWORD: password
          steps:
          - checkout
          ...

You will receive a `ContainerCheckFailed: Unable to connect to [...] Postgres test container` error in CI if the above is not added to you job config.

### Running tests locally

In order to run tests locally, make sure you have docker installed ([Mac OS](https://docs.docker.com/docker-for-mac/install/), [*nix](https://docs.docker.com/install/), [Windows](https://docs.docker.com/docker-for-windows/install/)).

Once you have docker installed, `pytest` will automatically up and down any necessary docker containers so you don't have to.

### Running tests locally from WITHIN a Docker Container

Add the following mount to your `docker run` command which will allow `pytest` to communicate with your host machine's docker CLI:

    docker run -v /var/run/docker.sock:/var/run/docker.sock [..other options] <IMAGE>

#### OPTIONAL: Running tests locally (with less test startup lag)

If you have any test with a dependency on a Postgres or Redshift fixture, pytest will detect this, check if a `Postgres` instance is available for use and if one isn't available, it will create and manage one for you.

This process can take some seconds on initial test startup, you can avoid this startup cost by up-ing your own detached container for pytest to use:

```bash
$ docker run -d -p 5532:5432 -e POSTGRES_DB=dev -e POSTGRES_USER=user -e POSTGRES_PASSWORD=password postgres:9.6.10-alpine
711f5d5a86896bb4eb76813af4fb6616aee0eff817cdec6ebaf4daa0e9995441
```

You can check on the instance's state via:

```bash
$ docker ps
CONTAINER ID        IMAGE                    COMMAND                  CREATED             STATUS              PORTS                    NAMES
711f5d5a8689        postgres:9.6.10-alpine   "docker-entrypoint.s…"   16 seconds ago      Up 15 seconds       0.0.0.0:5532->5432/tcp   determined_euclid
```

You can terminate the instance whenever you want via:

```bash
$ docker stop 711f5d5a8689  # where 711f5d5a8689 is the `CONTAINER ID` from `docker ps`
711f5d5a86896bb4eb76813af4fb6616aee0eff817cdec6ebaf4daa0e9995441
```

## Database Fixtures

### Introduction to Database Fixtures

This package gives you the capability to create as many mock SQLite, Postgres and Redshift instances with whatever preset data, functions or DDL you need.

Each fixture you create can be used in multiple tests without risking data leakage or side-effects from one test to another.

#### A Simple Example

Say you had a function which did some stuff using a Redshift Connection

```python
# src/package/utilities.py

def sql_sum(redshift_conn):
    """SUPER OPTIMIZED WAY to add up to 15.

    Better than C or Go!
    """
    redshift_conn.execute("CREATE TEMP TABLE mytemp(c INT);")
    redshift_conn.execute(
        """
        INSERT INTO mytemp(c)
        VALUES (1),
            (2),
            (3),
            (4),
            (5);
        """
    )

    return redshift_conn.execute("SELECT SUM(c) FROM mytemp;").fetchone()

```

To test this, we first need to create a `redshift fixture`:

```python
# tests/conftest,py

from pytest_mock_resources import create_redshift_fixture

# Create a redshift fixture available to all tests within the current dir and below!
redshift = create_redshift_fixture()
```

We then create a test that leverages the fixture to test the function:

```python
# tests/test_utilities.py

from package import utilities


# Supply the redshift fixture as an argument
def test_sql_sum(redshift):

    # The `redshift` fixture returns a SQLAlchemy engine which you can use as-is.
    conn = redshift.connect()

    # Run the function we want to test
    result = utilities.sql_sum(conn)

    assert result == (15,)
```

We can then run a `pytest` command and confirm the function works as expected!

### Custom Connection Example

Say you had an entrypoint to your code which required a configuration file and created whatever connections it needed on it's own.

The following configuration can be used to construct your own connection or client in any test.

    username: "user"
    password: "password"
    host: Use PG_HOST fixture
    port: Use PG_PORT fixture
    database: Your fixture's `database` attribute

An example:

```python
# src/package/entrypoint.py

import psycopg2

def main(config):
    conn = psycopg2.connect(
        dbname=config["database"],
        user=config["username"],
        password=config["password"],
        host=config["host"],
        port=str(config["port"]),
    )

    do_the_thing(conn)
    ...
```

In this case, we cannot pass in a connection or engine object - we need to pass in a configuration and let the code do what it needs to do:

```python
# tests/conftest,py

from pytest_mock_resources import create_postgres_fixture

# Create a postgres fixture available to all tests within the current dir and below!
postgres = create_postgres_fixture()
```

We use a `postgres` fixture in this example instead of a `redshift` fixture, but both work the same way!

```python
# tests/test_utilities.py

from package import entrypoint

# Supply PG_HOST, PG_PORT and custom redshift fixtures as arguments
def test_main(PG_HOST, PG_PORT, redshift):

    # Create a configuration object for our purposes
    config = {
        "database"=redshift.database,
        "user"="user",
        "password"="password",
        "host"=PG_HOST,
        "port"=PG_PORT,
    }

    # Run the function we want to test
    result = entrypoint.main(config)

    assert result ...
```

### Preset DDL/Data Examples

The above examples are fairly trivial, in a more realistic situation you would be dealing with pre-set DDL and data.

To address this, the `create_*_fixture` functions can take in an arbitrary amount of **ordered** arguments which can be used to *setup* the fixture prior to you using it. The following is a list of all possible arg types:

* A `Statements` instance.
  * An iterable of executable `strings` to run against the database fixture.
* A SQLAlchemy [metadata](https://docs.sqlalchemy.org/en/latest/core/metadata.html) or [declarative base](https://docs.sqlalchemy.org/en/latest/orm/extensions/declarative/basic_use.html) instance.
  * Used to pre-populate the fixture with all Schemas and Tables found on the instance.
* A `Rows` instance.
  * An iterable of [SQLAlchemy model instances](https://docs.sqlalchemy.org/en/latest/orm/tutorial.html#create-an-instance-of-the-mapped-class) to create DDL and then populate it with data from these model instances.

Adding any of these to your `create_*_fixture` call will result in a fixture which is preset with whatever DDL and data you provided.

These fixtures will also reset to the pre-set data/DDL every time they are used - there will be NO data leakage or side-effects from one test to the other.

#### Statements Example

The `Statements` class is used to supply a `create_*_function` with an ordered list of statments to execute.

```python
# tests/conftest.py:

from pytest_mock_resources import create_redshift_fixture, Statements

statements = Statements(
    """
    CREATE TABLE account(
      user_id serial PRIMARY KEY,
      username VARCHAR (50) UNIQUE NOT NULL,
      password VARCHAR (50) NOT NULL
    );
    """,
    """
    INSERT INTO account VALUES (1, 'user1', 'password1')
    """,
)

redshift = create_redshift_fixture(
    statements,
)
```

```python
# tests/test_something.py:

def test_something_exists(redshift):
    execute = redshift.execute("SELECT password FROM account")

    result = sorted([row[0] for row in execute])
    assert ["password1"] == result
```

#### SQLAlchemy metadata and Base Example

[SQLAlchemy](https://www.sqlalchemy.org/) is an ORM which allows you to define [SQLAlchemy models](https://docs.sqlalchemy.org/en/latest/orm/tutorial.html#declare-a-mapping) to represent your database tables and then use those models to interface with your database.

The `create_*_fixture` can take in any number of SQLAlchemy metadata or Base instances and use them to to create DDL.

Example:

```python
# src/package/models.py:

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "user"
    __table_args__ = {"schema": "stuffs"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
```

```python
# tests/conftest.py:

from package.models import Base
from pytest_mock_resources import create_redshift_fixture

redshift = create_redshift_fixture(
    Base,
)
```

```python
# tests/test_something.py:

def test_something_exists(redshift):
    # Insert a row into the user table DURING the test
    redshift.execute("INSERT INTO stuffs.user(name) VALUES ('Picante', )")

    # Confirm that the user table exists and the row was inserted
    execute = redshift.execute("SELECT name FROM stuffs.user")
    result = sorted([row[0] for row in execute])
    assert ["Picante"] == result
```

Even if you don't plan on using SQLAlchemy models or the ORM layer throughout your actual code, defining these models can be EXTREMELY beneficial for DDL maintenance and testing.

* If you are working against `client` databases, see if [client-redshift-schema](https://github.com/schireson/client-redshift-schema) and [client-vops-schema](https://github.com/schireson/client-flight-manager/tree/master/client-vops-schema) fit your needs.
  * See the example below on how to use them as well!
* If you are working on a project with pre-existing DDL, you can use the awesome [sqlacodegen](https://github.com/agronholm/sqlacodegen) to generate the models from your current DDL!
* If you are working on a new project which requires a SQL Database layer, we HIGHLY recommend using SQLAlchemy in combination with [alembic](https://alembic.sqlalchemy.org/en/latest/) to create and maintain your DDL.

##### Example using client-redshift-schema

```python
# tests/conftest.py:

from pytest_mock_resources import create_redshift_fixture, Statements
from client_redshift_schema import meta
from client_redshift_schema.warehouse import warehouse_stacked_data

statements = Statements(
    warehouse_stacked_data.insert().values(network="ABCDE"),
)

redshift = create_redshift_fixture(
    meta,  # supply the metadata
    statements,
)
```

```python
# tests/test_something.py:

def test_something_exists(redshift):
    execute = redshift.execute("SELECT network FROM warehouse.warehouse_stacked_data")

    # Confirm that the warehouse.warehouse_stacked_data table exists and the row was inserted
    result = sorted([row[0] for row in execute])
    assert ["ABCDE"] == result
```

##### Dealing with Bloated Metadata

By default, each DB fixture recreates the whole database from scratch prior to each test to ensure there are no side-effects from one test to another.

Recreating DDL is fairly quick but if there are a large amount of tables to create, test setup-time can begin to suffer.

An example of this is `client-redshift-schema` which has more than a 1000 tables. As a result, it takes ~5 seconds for each test to setup which is unacceptable. If you have 200 tests running linearly, you will be spending an additional ~17 minutes, waiting for tests to complete.

To counteract this, you can provide an iterable of table names to your `create_*_fixture` call. This will tell the call to ONLY create the tables you have specified instead of creating all of them.

This can be a great way to keep track of all the tables your code interacts with as well!

An example:

```python
# tests/conftest.py:

from pytest_mock_resources import create_redshift_fixture, Statements
from client_redshift_schema import meta
from client_redshift_schema.warehouse import warehouse_stacked_data

statements = Statements(
    warehouse_stacked_data.insert().values(network="ABCDE"),
)

redshift = create_redshift_fixture(
    meta,
    statements,
    # ONLY create this single table for this test.
    tables=[
        "warehouse.warehouse_stacked_data",
    ]
)
```

```python
# tests/test_something.py:

def test_something_exists(redshift):
    execute = redshift.execute("SELECT network FROM warehouse.warehouse_stacked_data")

    # Confirm that the warehouse.warehouse_stacked_data table exists and the row was inserted
    result = sorted([row[0] for row in execute])
    assert ["ABCDE"] == result
```


#### Rows Example

If you are using SQLAlchemy to maintain your DDL, you have the capability to use the `Rows` class to conveniently pre-populate your db fixture with DDL and data in a single line.

Example:

```python
# src/package/models.py:

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
```

```python
# tests/conftest.py:

from package.models import User  # These models could be imported from ANYWHERE
from pytest_mock_resources import create_redshift_fixture, Rows

rows = Rows(
    User(name="Harold"),
    User(name="Catherine"),
)

redshift = create_redshift_fixture(
    # This will AUTOMATICALLY create ALL the schemas and tables found in any row's metadata
    # and then populate those tables via the given model instances.
    rows,
)
```

```python
# tests/test_something.py:

def test_something_exists(redshift):
    execute = redshift.execute("SELECT * FROM user")

    # Confirm that the user table exists and the rows were inserted
    result = sorted([row[1] for row in execute])
    assert ["Catherine", "Harold"] == result
```

#### Function as an Argument Example

Uses can supply a function as an input argument to the fixtures. The function would take in a session argument and expect the user to add and execute things as they see fit. Using this, users can test complex relationships amongst tables.<br>
In the following example, we define 2 classes, `User` and `Object`, with a one-to-many relationship.

```python

class User(Base):
    __tablename__ = "user"
    __table_args__ = {"schema": "stuffs"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    objects = relationship("Object", back_populates="owner")

class Object(Base):
    __tablename__ = "object"
    __table_args__ = {"schema": "stuffs"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    belongs_to = Column(Integer, ForeignKey('stuffs.user.id'))
    owner = relationship("User", back_populates="objects")
```

We also define a function that will be passed to a Postgres fixture as an argument. In the function we define a nested instantiation.

```python

def session_fn(session):
    session.add(User(name='Fake Name', objects=[Object(name='Boots')]))

postgres = create_postgres_fixture(Base, session_fn)

```

An Example Test to test the previously defined fixture. In the test we assert that the relationships previously defined are maintained in the mock database.

```python

def test_session_function(postgres):
    execute = postgres.execute("SELECT * FROM stuffs.object")
    owner_id = sorted([row[2] for row in execute])[0]

    execute = postgres.execute("SELECT * FROM stuffs.user where id = {id}".format(id=owner_id))
    result = [row[1] for row in execute]

    assert result == ['Fake Name']

```

#### COPY Statements for Redshift Fixture Example:
Users can run `COPY` statements locally using the redshift fixture.<br>
Consider a table `items` with columns `(id, name, price)`and a `.csv` stored on an S3 bucket with the following url: `s3:\\mybucket\myfile.csv`. To copy data from the said file to the `items` table, the redshift fixture supports the following command locally:
<br>
```python
# tests/test_something.py

redshift = create_redshift_fixture()

def test_copy_from_s3_file(redshift):
    redshift.execute(
        "CREATE TABLE Items (id INT, Name VARCHAR(16), Price CHAR(1));"
    )
    redshift.execute(
        (
            "COPY items (id, name, price) from `s3:\\mybucket\myfile.csv` "
            "credentials 'aws_access_key_id=<AWS_ACCESS_KEY_ID>;"
            "aws_secret_access_key=<AWS_SECRET_ACCESS_KEY>'"
        )
    )

    execute = redshift.execute('SELECT * FROM items')

    # Assert data in table equals data in .csv file.
```

#### MongoDB Fixture Example:

Users can test MongoDB commands/functions using the `create_mongo_fixture`. Consider the following example:<br>
Let `customer` be a collection, and `insert_into_customer`, a functions that inserts data into this collection.

```python
# src/some_module.py

def insert_into_customer(mongodb_connection):
    collection = mongodb_connection['customer']
    to_insert = {"name": "John", "address": "Highway 37"}
    collection.insert_one(to_insert)

```

A user can test this as follows:

```python
# test/some_test.py

from pytest_mock_resources import create_mongo_fixture
from some_module import insert_into_customer

mongo = create_mongo_fixture()

def test_insert_into_customer(mongo):
    insert_into_customer(mongo)
    collection = mongo['customer']
    returned = collection.find_one()
    # This assumes that there as no previously stored data in the collection.
    assert returned == {"name": "John", "address": "Highway 37"}

```

## Need help?

Contact Omar Khan via slack or omar@schireson.com.

## Contributing Pre-Requisites

[Lucha](https://github.com/schireson/lucha/) must be globally installed (preferably via pipx) to run most MakeFile commands.
