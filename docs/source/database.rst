.. toctree::

Relational Database Fixtures
============================

There is a page specifically for :ref:`redshift-label` , but all the relational database
(sqlite, postgres, redshift, etc) fixtures have the same signatures, and therefore
support the same utilities for running DDL, setup, and whatnot.

Basics
------

Say you had a function which required a redshift engine.

.. code-block:: python

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

To test this, we first need to create a :code:`redshift fixture`:

.. code-block:: python

   # tests/conftest,py
   from pytest_mock_resources import create_redshift_fixture

   redshift = create_redshift_fixture()

By putting this in the top-level :code:`conftest.py` file, it is made available to all tests,
though **note** you can create the fixture at at any location, in order scope it to a subset
of your tests.

We then create a test that leverages the fixture to test the function:

.. code-block:: python

   # tests/test_utilities.py
   from package import utilities

   # Supply the redshift fixture as an argument
   def test_sql_sum(redshift):
       # Run the function we want to test
       result = utilities.sql_sum(conn)

       assert result == (15,)

We can then run a `pytest` command and confirm the function works as expected!

Custom Engines
--------------

Suppose you you're doing end-to-end testing, which includes the code which loads your configuration
required to *create* an engine. The vanilla :code:`redshift` fixture above won't quite cut it
in that case.

.. code-block:: python

   # src/package/entrypoint.py

   import psycopg2
   import sqlalchemy

   def psycopg2_main(**config):
       conn = psycopg2.connect(**config)
       do_the_thing(conn)
       ...

   def sqlalchemy_main(**config):
       conn = sqlalchemy.create_engine(**config)
       do_the_thing(conn)
       ...

As you can see, we must pass in valid credentials to *create* an engine, rather than the engine
itself. You'll need to make use of the :code:`pmr_credentials` attribute.

.. code-block:: python

   from pytest_mock_resources import (
       create_postgres_fixture,
       create_redshift_fixture,
   )

   from package import entrypoint

   postgres = create_postgres_fixture()
   redshift = create_redshift_fixture()

   def test_psycopg2_main_postgres(postgres):
       credentials = postgres.pmr_credentials
       result = entrypoint.psycopg2_main(**credentials.as_psycopg2_connect_args())
       assert result ...

   def test_psycopg2_main_redshift(redshift):
       credentials = redshift.pmr_credentials
       result = entrypoint.psycopg2_main(**credentials.as_psycopg2_connect_args())
       assert result ...

As you can see, :code:`postgres` and :code:`redshift` both work the same way, and can provide
arguments directly into the psycopg2 :code:`connect` function. Now lets see how :code:`sqlalchemy`
can work.

.. code-block:: python

   def test_sqlalchemy_main_postgres(postgres):
       credentials = postgres.pmr_credentials
       result = entrypoint.sqlalchemy_main(**credentials.as_url())
       assert result ...

   def test_sqlalchemy_main_redshift(redshift):
       credentials = redshift.pmr_credentials
       result = entrypoint.sqlalchemy_main(**credentials.as_url())
       assert result ...

Again, all fixtures have the same interface. :code:`as_url()` returns an inter-dbapi compatible
connection string, which should be a valid input to all the supported connection modes. However,
there are also sqlalchemy, psycopg2, and mongo specific conversion functions. In case that's
required. And finally, if all else fails, :code:`pmr_credentials` is an object with public
attributes for all the connection information.


Preset DDL/Data
---------------

The above examples are fairly trivial, in a more realistic situation you would be dealing with
pre-set DDL and data.

To address this, the :code:`create_*_fixture` functions can take in an arbitrary amount of
**ordered** arguments which can be used to *setup* the fixture prior to you using it. The following
is a list of all possible arg types:

* A :code:`Statements` instance.

  * An iterable of executable :code:`strings` to run against the database fixture.

* A `SQLAlchemy metadata <https://docs.sqlalchemy.org/en/latest/core/metadata.html>`_ or
  `declarative base <https://docs.sqlalchemy.org/en/latest/orm/extensions/declarative/basic_use.html>`_
  instance.

  * Used to pre-populate the fixture with all Schemas and Tables found on the instance.

* A :code:`Rows` instance.

  * An iterable of `SQLAlchemy model instances <https://docs.sqlalchemy.org/en/latest/orm/tutorial.html#create-an-instance-of-the-mapped-class>`_
    to create DDL and then populate it with data from these model instances.

Adding any of these to your :code:`create_*_fixture` call will result in a fixture which is preset with whatever DDL and data you provided.

These fixtures will also reset to the pre-set data/DDL every time they are used - there will be NO data leakage or side-effects from one test to the other.

Statements
~~~~~~~~~~

The :code:`Statements` class is used to supply a :code:`create_*_function` with an ordered list of statments to execute.

.. code-block:: python

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

Note, you can execute arbitrary SQL strings or :code:`SQLAlchemy` statements (DDL or otherwise),
and the listed statements will be executed on a fresh database for each test. This ensures that
the state of the database is identical across all tests which share that fixture.

.. code-block:: python

   # tests/test_something.py:
 
   def test_something_exists(redshift):
       execute = redshift.execute("SELECT password FROM account")
 
       result = sorted([row[0] for row in execute])
       assert ["password1"] == result

Metadata/Models
~~~~~~~~~~~~~~~

The `SQLAlchemy <https://www.sqlalchemy.org/>`_ ORM allows you to define declarative
`models <https://docs.sqlalchemy.org/en/latest/orm/tutorial.html#declare-a-mapping>`_ to represent
your database tables and then use those models to interface with your database.

The :code:`create_*_fixture` functions can take in any number of SQLAlchemy metadata or Base
instances and use them to to create DDL.

For example, given a models package:

.. code-block:: python

   # src/package/models.py:
 
   from sqlalchemy import Column, Integer, String
   from sqlalchemy.ext.declarative import declarative_base
 
   Base = declarative_base()
 
   class User(Base):
       __tablename__ = "user"
       __table_args__ = {"schema": "stuffs"}
 
       id = Column(Integer, primary_key=True, autoincrement=True)
       name = Column(String)

A corresponding test file could look like

.. code-block:: python

   # tests/test_user.py:
 
   from package.models import Base
   from pytest_mock_resources import create_postgres_fixture
 
   pg = create_redshift_fixture(
       Base,
 
       # Of course you can use this with statements
       Statements("INSERT INTO stuffs.user(name) VALUES ('Picante', )"),
   )
 
   def test_something_exists(pg):
       # Insert a row into the user table DURING the test
       pg.execute("INSERT INTO stuffs.user(name) VALUES ('Beef', )")
 
       # Confirm that the user table exists and the row was inserted
       rows = pg.execute("SELECT name FROM stuffs.user")
       result = [row[0] for row in rows]
       assert ["Picante", "Beef"] == result
 
Even if you don't plan on using SQLAlchemy models or the ORM layer throughout your actual code,
defining these models can be EXTREMELY beneficial for DDL maintenance and testing.

.. admonition:: info

   If you are working on a new project which requires a SQL Database layer, we HIGHLY recommend
   using SQLAlchemy in combination with `alembic <https://alembic.sqlalchemy.org/en/latest/>`_ to
   create and maintain your DDL.

.. admonition:: info

   If you are working on a project with pre-existing DDL, you can use a tool like
   `sqlacodegen <https://github.com/agronholm/sqlacodegen>`_ to generate the models from your
   current DDL!


Dealing with Bloated Metadata
#############################

By default, each DB fixture recreates the whole database from scratch prior to each test to ensure
there are no side-effects from one test to another.

Recreating DDL is generally fairly quick but if there are a large amount of tables to create,
test setup-time can begin to suffer. In one of our databases, there are more than a 1000 tables!
As a result, it takes ~5 seconds for each test to setup which is unacceptable. If you have 200
tests running linearly, you will be spending an additional ~17 minutes, waiting for tests to complete.

To counteract this, you can provide an iterable of table names to your :code:`create_*_fixture` call.
This will tell the call to ONLY create the tables you have specified instead of creating all of them.

This can be a great way to keep track of all the tables a given block of code interacts with as well!

.. code-block:: python

   # tests/conftest.py:
 
   from pytest_mock_resources import create_redshift_fixture, Statements
   from redshift_schema import meta, example_table
 
   redshift = create_redshift_fixture(
       meta,
       statements,
       Statements(
           example_table.insert().values(name="ABCDE"),
       ),
 
       # ONLY create this single table for this test.
       tables=[
           example_table,
           "example_table_mapping_table",
       ]
   )


As you can see, in the above example, tables accepts _any_ of: the string table name, the
SQLAlchemy table object, or a SQLAlchemy model class.

.. code-block:: python

   # tests/test_something.py:

   def test_something_exists(redshift):
       execute = redshift.execute("SELECT network FROM warehouse.warehouse_stacked_data")

       # Confirm that the warehouse.warehouse_stacked_data table exists and the row was inserted
       result = sorted([row[0] for row in execute])
       assert ["ABCDE"] == result


Rows
~~~~

If you are using SQLAlchemy to maintain your DDL, you have the capability to use the :code:`Rows`
class to conveniently pre-populate your db fixture with DDL and data in a single line.

.. code-block:: python

   # src/package/models.py:

   from sqlalchemy import Column, Integer, String
   from sqlalchemy.ext.declarative import declarative_base

   Base = declarative_base()

   class User(Base):
       __tablename__ = "user"

       id = Column(Integer, primary_key=True, autoincrement=True)
       name = Column(String)

.. code-block:: python

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

.. code-block:: python

   # tests/test_something.py:

   def test_something_exists(redshift):
       execute = redshift.execute("SELECT * FROM user")

       # Confirm that the user table exists and the rows were inserted
       result = sorted([row[1] for row in execute])
       assert ["Catherine", "Harold"] == result


Functions
~~~~~~~~~

Uses can supply a function as an input argument to the fixtures as well:

.. code-block:: python

   # Create models with relationships
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


   # Leverage model relationships in a seed data function
   def session_fn(session):
       session.add(User(name='Fake Name', objects=[Object(name='Boots')]))


   # Leverage seed data function to create seeded fixture
   postgres = create_postgres_fixture(Base, session_fn)


   # Leverage seeded fixture
   def test_session_function(postgres):
       execute = postgres.execute("SELECT * FROM stuffs.object")
       owner_id = sorted([row[2] for row in execute])[0]

       execute = postgres.execute("SELECT * FROM stuffs.user where id = {id}".format(id=owner_id))
       result = [row[1] for row in execute]

       assert result == ['Fake Name']
