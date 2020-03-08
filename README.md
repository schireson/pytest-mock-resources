![CircleCI](https://img.shields.io/circleci/build/gh/schireson/pytest-mock-resources/master) [![codecov](https://codecov.io/gh/schireson/pytest-mock-resources/branch/master/graph/badge.svg)](https://codecov.io/gh/schireson/pytest-mock-resources) [![Documentation Status](https://readthedocs.org/projects/pytest-mock-resources/badge/?version=latest)](https://pytest-mock-resources.readthedocs.io/en/latest/?badge=latest)

[Read the Docs!](https://pytest-mock-resources.readthedocs.io/en/latest/quickstart.html)

`pytest-mock-resources` is a Pytest Plugin that can be used to rapidly create "resource" fixtures.

If you aren't familiar with Pytest Fixtures, you can read up on them in the [Pytest documentation](https://docs.pytest.org/en/latest/fixture.html).

## Introduction

Code which depends on external resources such a databases (postgres, redshift, etc) can be difficult
to write automated tests for.

Take the following, _simple_ example:

```python
def view_function(session):
    users = (
        session.query(User)
        .options(selectinload(User.purchases))
        .all()
    )
    return [
        {
            'user': user.serialize(),
            'purchases': [p.serialize() for p in user.purchases],
        }
        for user in users
    ]
```

You could test the `view_function` by mocking out the database "session" object and making it return the ideal value on a given call, but testing whether the actual **SQL query** did the correct thing _truly_
requires that you execute the query. Any fake-db mocks that are created would also have to be updated if your usage changes.

On the other hand, tests that depend upon a **real** database instance can be fragile and prone to database management, connection and state issues.

### Enter: `pytest-mock-resources`

`pytest-mock-resources` alleviates these issues so that you can have the best of both worlds - it provides you with the ability to automatically start up **real** managed resources during your pytest run.

Your test file could look something like the following for the example above:

```python
from pytest_mock_resources import create_postgres_fixture

from sqlachemy_models import ModelBase, User, Purchase

# Create a PG fixture which returns a SQLALchemy session object
#  with access to a REAL database that is preset with DDL based on your SQLAlchemy Model Base
pg = create_postgres_fixture(ModelBase, session=True)

# leverage the DB fixture across multiple tests without worrying about polluting the DB or managing the DB instance.
def test_view_function_empty_db(pg):
    response = view_function(pg)
    assert response == []

def test_view_function_user(pg):
    user = User(id=1, name="omar")
    pg.add(user)
    pg.commit()

    response = view_function(pg)
    assert response == [
        {
            "user": {"id": 1, "name": "omar"},
            "purchases": [],
        }
    ]

def test_view_function_user_with_purchases(pg):
    purchase_1 = Purchase(id=1, item="television", price_cents="23100")
    purchase_2 = Purchase(id=2, item="speaker system", price_cents="29900")
    user = User(id=1, name="omar", purchases=[purchase_1, purchase_2])
    pg.add(user)
    pg.commit()

    response = view_function(pg)
    assert response == [
        {
            "user": {"id": 1, "name": "omar"},
            "purchases": [
                {"item": "television", "price"="$231.00"},
                {"item": "speaker system", "price"="$299.00"},
            ],
        }
    ]
```

Resources created through `pytest-mock-resources` have the following benefits by default:

* All created resources (fixtures) are backed by **real** resources in the form of docker containers.

  * For example, a postgres fixture will stand up an official postgres image-based docker container.

  * Docker is required to be available and accessible for the majority of the available fixtures, [see our docs](https://pytest-mock-resources.readthedocs.io/en/latest/docker.html) for any questions!

* All `pytest-mock-resources` fixtures are managed by `pytest-mock-resources` - they automatically start, reset state and stop when needed.

* You can create as many resources as you want:

  ```python
  from pytest_mock_resources import create_postgres_fixture, create_mongo_fixture

  from sqlachemy_models import UserdataBase, ReportBase, AnalyticsBase

  empty_pg = create_postgres_fixture()
  empty_pg_2 = create_postgres_fixture()
  userdata_pg = create_postgres_fixture(UserdataBase)
  report_pg = create_postgres_fixture(ReportBase)
  analytics_pg = create_postgres_fixture(AnalyticsBase)
  analytics_pg_2 = create_postgres_fixture(AnalyticsBase)

  big_data_mongodb = create_mongo_fixture()
  ```

* A single pytest can utilize as many resource fixtures as it needs:

  ```python
  # following the snippet above

  def test_analytic_report_success(userdata_pg, report_pg, analytics_pg, big_data_mongodb):
      create_user(userdata_pg)
      perform_analytics(userdata_pg. analytics_pg)
      run_single_quarter_report(analytics_pg. report_pg)
      run_annual_report(report_pg. big_data_mongodb)
  ```

* Each resource resets it's state to the state described on creation.

* SQLite, Postgres and Redshift based `pytest-mock-resources` have additional conveniences:

  * Creating Fixtures with [preset DDL based on your SQLAlchemy models](https://pytest-mock-resources.readthedocs.io/en/latest/database.html#metadata-models)
  * Creating Fixtures with [preset DDL/Data based on raw SQL Statements](https://pytest-mock-resources.readthedocs.io/en/latest/database.html#statements)
  * Creating Fixtures with [preset data based on SQLAlchemy model instances](https://pytest-mock-resources.readthedocs.io/en/latest/database.html#rows)
  * Or any combo of the above... and much more - [Read the Docs!](https://pytest-mock-resources.readthedocs.io/en/latest/fixtures.html)

## Installing

```bash
# Basic fixture support
pip install "pytest-mock-resources"

# For postgres install EITHER of the following:
pip install "pytest-mock-resources[postgres-binary]"
pip install "pytest-mock-resources[postgres]"

# For redshift install EITHER of the following:
# (redshift fixtures require postgres dependencies...)
pip install "pytest-mock-resources[postgres, redshift]"
pip install "pytest-mock-resources[postgres-binary, redshift]"

# For mongo install the following:
pip install "pytest-mock-resources[mongo]"
```

## Existing Resources (many more possible)

* SQLite

  ```python
  from pytest_mock_resources import create_sqlite_fixture
  ```

* Postgres

  ```python
  from pytest_mock_resources import create_postgres_fixture
  ```

* Redshift

  **Note**: Redshift fixtures use postgres under the hood, but is built to support as much
  redshift functionality as possible (including redshift's `COPY`/`UNLOAD` commands).

  ```python
  from pytest_mock_resources import create_redshift_fixture
  ```

* Mongo

  ```python
  from pytest_mock_resources import create_mongo_fixture
  ```


## Contributing

We anticipate creating more resources, some of the future possibilities include:

* MySQL
* Rabbit Broker
* Redis
* AWS Presto

Feel free to file an [issue](https://github.com/schireson/pytest-mock-resources/issues) if you find any bugs or want a new mock resource or feature.

If you feel super strongly about an [issue](https://github.com/schireson/pytest-mock-resources/issues) or just want to contribute - fork this repo, implement the feature/fix and PR it back to us!
