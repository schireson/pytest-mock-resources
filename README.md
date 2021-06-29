![CircleCI](https://img.shields.io/circleci/build/gh/schireson/pytest-mock-resources/master)
[![codecov](https://codecov.io/gh/schireson/pytest-mock-resources/branch/master/graph/badge.svg)](https://codecov.io/gh/schireson/pytest-mock-resources)
[![Documentation
Status](https://readthedocs.org/projects/pytest-mock-resources/badge/?version=latest)](https://pytest-mock-resources.readthedocs.io/en/latest/?badge=latest)

## Introduction

Code which depends on external resources such a databases (postgres, redshift, etc) can be difficult
to write automated tests for. Conventional wisdom might be to mock or stub out the actual database
calls and assert that the code works correctly before/after the calls.

However take the following, *simple* example:

``` python
def serialize(users):
    return [
        {
            'user': user.serialize(),
            'address': user.address.serialize(),
            'purchases': [p.serialize() for p in user.purchases],
        }
        for user in users
    ]

def view_function(session):
    users = session.query(User).join(Address).options(selectinload(User.purchases)).all()
    return serialize(users)
```

Sure, you can test `serialize`, but whether the actual **query** did the correct thing *truly*
requires that you execute the query.

## The Pitch

Having tests depend upon a **real** postgres instance running somewhere is a pain, very fragile, and
prone to issues across machines and test failures.

Therefore `pytest-mock-resources` (primarily) works by managing the lifecycle of docker containers
and providing access to them inside your tests.

As such, this package makes 2 primary assumptions:

- You're using `pytest` (hopefully that's appropriate, given the package name)
- For many resources, `docker` is required to be available and running (or accessible through remote
  docker).

If you aren't familiar with Pytest Fixtures, you can read up on them in the [Pytest
documentation](https://docs.pytest.org/en/latest/fixture.html).

In the above example, your test file could look something like

``` python
from pytest_mock_resources import create_postgres_fixture
from models import ModelBase

pg = create_postgres_fixture(ModelBase, session=True)

def test_view_function_empty_db(pg):
  response = view_function(pg)
  assert response == ...

def test_view_function_user_without_purchases(pg):
  pg.add(User(...))
  pg.flush()

  response = view_function(pg)
  assert response == ...

def test_view_function_user_with_purchases(pg):
  pg.add(User(..., purchases=[Purchase(...)]))
  pg.flush()

  response = view_function(pg)
  assert response == ...
```

## Existing Resources (many more possible)

- SQLite

  ``` python
  from pytest_mock_resources import create_sqlite_fixture
  ```

- Postgres

  ``` python
  from pytest_mock_resources import create_postgres_fixture
  ```

- Redshift

  **note** Uses postgres under the hood, but the fixture tries to support as much redshift
  functionality as possible (including redshift's `COPY`/`UNLOAD` commands).

  ``` python
  from pytest_mock_resources import create_redshift_fixture
  ```

- Mongo

  ``` python
  from pytest_mock_resources import create_mongo_fixture
  ```

- Redis

  ``` python
  from pytest_mock_resources import create_redis_fixture
  ```

- MySQL

  ``` python
  from pytest_mock_resources import create_mysql_fixture
  ```

## Features

General features include:

- Support for "actions" which pre-populate the resource you're mocking before the test
- [Async fixtures](https://pytest-mock-resources.readthedocs.io/en/latest/async.html)
- Custom configuration for container/resource startup

## Installing

``` bash
# Basic fixture support
pip install "pytest-mock-resources"

# For postgres install EITHER of the following:
pip install "pytest-mock-resources[postgres-binary]"
pip install "pytest-mock-resources[postgres]"

# For postgres async
pip install "pytest-mock-resources[postgres-async]"

# For redshift install EITHER of the following:
# (redshift fixtures require postgres dependencies...)
pip install "pytest-mock-resources[postgres, redshift]"
pip install "pytest-mock-resources[postgres-binary, redshift]"

# For mongo install the following:
pip install "pytest-mock-resources[mongo]"

# For redis
pip install "pytest-mock-resources[redis]"

# For mysql
pip install "pytest-mock-resources[mysql]"
```

## Possible Future Resources

- Rabbit Broker
- AWS Presto

Feel free to file an [issue](https://github.com/schireson/pytest-mock-resources/issues) if you find
any bugs or want to start a conversation around a mock resource you want implemented!

## Python 2

Releases in the 1.x series were supportive of python 2. However starting from 2.0.0, support for
python 2 was dropped. We may accept bugfix PRs for the 1.x series, however new development and
features will not be backported.
