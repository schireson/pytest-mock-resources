# Schireson Pytest Mock-Resources

#schiresonip #ruby

## Introduction

Pytest Mock-Resources is a collection of convenient pytest plugins to make it easier to test against code that depends on external resourcess.

Currently available resources:

* Mock Postgres
* Mock Redshift
* Mock SQLite

## Mock Redshift and Postgres

## Configuration

If you need to construct your own connection or client in any test, the following config can be used:

    username: "username"
    password: "password"
    host: from pytest_mock_resources import HOST
    port: "5532"
    database: database_name you passed into the create_*_fixture function

## Example

    # src/package/models.py:

    from sqlalchemy import Column, Integer
    from sqlalchemy.ext.declarative import declarative_base

    # Define your SQLAlchemy Base and Models or import them from somewhere
    Base = declarative_base()

    class User(Base):
        __tablename__ = "user"
        __table_args__ = {"schema": "stuffs"}

        id = Column(Integer, primary_key=True, autoincrement=True)


    # tests/conftest.py:

    import pytest

    from package.models import Base, User
    from pytest_mock_resources import create_redshift_fixture, CreateAll, Rows

    create_all = CreateAll(Base)

    rows = Rows(
        User(name="Harold"),
        User(name="Catherine"),
    )

    redshift = create_redshift_fixture(
        database_name="redshift",
        ordered_actions=[
            create_all,
            rows,
        ],
    )


    # tests/test_something.py:

    def test_something_exists(redshift):
        execute = redshift_ordered_actions.execute("SELECT * FROM user")

        result = sorted([row[0] for row in execute])
        assert ["Catherine", "Harold"] == result

## Installing

    pip install --index-url https://artifactory.schireson.com/artifactory/api/pypi/pypi/simple "pytest-mock-resources[postgres]"

## Contributing Pre-Requisites

* [Lucha](https://github.com/schireson/lucha/) must be globally installed (preferably via pipx) to run most MakeFile commands.

## Running the tests

* Running the unit tests: `pytest` or `make test`
* Running the linters: `make lint`

## Changing the dependencies

### Adding a new dependency

Add the requirements to the relevant package's `deps/requirements.in` or `deps/dev-requirements.in`
then (inside the package's folder) run:

    make sync-deps

### Synchronizing your virtualenv with the requirements

    make init

### Updating an existing dependency

    pip-compile --upgrade-package docker
