Preset DDL/Data
===============

In previous examples, we've largely ignored the reality that an empty database
is often not useful by itself. You'll need to populate that database with
some minimal amount of schemata and/or data in order to be useful.

To address this, the :code:`create_*_fixture` functions take in an optional number
of "Ordered Actions" whcih can be used to *setup* the fixture prior to you using it.
As the name might imply, the "actions" are executed, in order, before the test
body is entered.

Metadata/Models
---------------
The `SQLAlchemy <https://www.sqlalchemy.org/>`_ ORM allows you to define declarative
`models <https://docs.sqlalchemy.org/en/latest/orm/tutorial.html#declare-a-mapping>`_ to represent
your database tables and then use those models to interface with your database.

The most direct way to pre-create all the DDL which your code depends on, **particularly**
if you already define :class:`sqlalchemy.MetaData` or declarative models, would be to
specify either as an ordered action.

For example, given a models package:

.. code-block:: python
   :caption: package/models.py

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
   :caption: tests/test_user.py

   from package.models import Base
   from pytest_mock_resources import create_postgres_fixture

   pg = create_redshift_fixture(Base)
   # or
   pg = create_redshift_fixture(Base.metadata)

   def test_something_exists(pg):
       # Insert a row into the user table DURING the test
       pg.execute("INSERT INTO stuffs.user(name) VALUES ('Beef', )")

       # Confirm that the user table exists and the row was inserted
       rows = pg.execute("SELECT name FROM stuffs.user")
       result = [row[0] for row in rows]
       assert ["Picante", "Beef"] == result


.. note::
   
   If you have split MetaData, you can pass in as many unique MetaData or declarative_base
   instances as necessary.

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


Bloated Metadata
~~~~~~~~~~~~~~~~
By default, each DB fixture recreates the whole database from scratch prior to each test to ensure
there are no side-effects from one test to another.

Recreating DDL is generally fairly quick but if there are a large amount of tables to create,
test setup-time can begin to suffer. In one of our databases, there are more than a 1000 tables!
As a result, it takes ~5 seconds for each test to setup which is unacceptable. If you have 200
tests running linearly, you might be spending an additional ~17 minutes, waiting for tests to complete.

To counteract this, you can provide an iterable of table names to your :code:`create_*_fixture` call.
This will tell the call to ONLY create the tables you have specified instead of creating all of them.

This can be a great way to keep track of all the tables a given block of code interacts with as well!

.. code-block:: python
   :caption: tests/conftest.py

   from pytest_mock_resources import create_redshift_fixture, Statements
   from redshift_schema import meta, example_table

   redshift = create_redshift_fixture(
       meta,
       # ONLY create this small set of tables for this test.
       tables=[
           example_table,
           "example_table_mapping_table",
       ]
   )


The :code:`tables` argument accepts any of:

* SQLAlchemy declarative model class
* SQLAlchemy table object
* Exact string table name
* Globbed table name

  Globbing, in comparison to regular expressions, in this context tends to lead to shorter
  and easier to read definitions. This is especially true when one uses schemas, leading
  to :code:`.` literals in your fully qualified table names.

  .. code-block:: python

     create_<backend>_fixture(Base, tables=['schema.*'])  # Only tables for a specific schema
     create_<backend>_fixture(Base, tables=['category_*'])  # Only tables with a specific suffix
     create_<backend>_fixture(Base, tables=['*_category'])  # Only tables with a specific prefix


Rows
----
If you are using SQLAlchemy to define your schema, you have the capability to use the :code:`Rows`
class to conveniently pre-populate your db fixture with data.

.. code-block:: python
   from package.models import Base, User
   from pytest_mock_resources import create_redshift_fixture, Rows

   rows = Rows(
       User(name="Harold"),
       User(name="Catherine"),
   )

   redshift = create_redshift_fixture(Base, rows)

   def test_something_exists(redshift):
       execute = redshift.execute("SELECT * FROM user")
       result = sorted([row[1] for row in execute])
       assert ["Catherine", "Harold"] == result

This will automatically insert any records defined by the :class:`Rows` before test execution.

.. admonition:: info

   You can also omit the above ``Base`` reference to the model base or metadata when
   using rows, yielding ``redshift = create_redshift_fixture(rows)``.

   Rows will backtrack to the corresponding metadata and treat it as though the
   metadata were passed in immediately preceding the ``Rows`` action.


Statements/StaticStatements
---------------------------
Either a :class:`Statements` or :class:`StaticStatements` object can be constructed,
which will execute arbitrary SQL before entering the test.

Both operate in exactly the same way, however :class:`StaticStatements` let the
library know that the included SQL statements are safe to "cache" in order to
reduce database creation costs. For that reason, you should prefer
a ``StaticStatements`` over a ``Statements`` where possible.

For example, the creation of temp tables or other transaction-specific operations,
are places where a static statement might be inappropriate.

.. code-block:: python
   :caption: tests/test_something.py

   from pytest_mock_resources import create_redshift_fixture, Statements

   statements = Statements(
       """
       CREATE TABLE account(
         user_id serial PRIMARY KEY,
         username VARCHAR (50) UNIQUE NOT NULL,
         password VARCHAR (50) NOT NULL
       );
       """,
       "INSERT INTO account VALUES (1, 'user1', 'password1')",
   )

   redshift = create_redshift_fixture(statements)

   def test_something_exists(redshift):
       execute = redshift.execute("SELECT password FROM account")
       result = sorted([row[0] for row in execute])
       assert ["password1"] == result


.. note::

   You can either supply an SQL ``str``, or :code:`SQLAlchemy` statements (
   such as ``text()``, select, insert, DDL, or other constructs),


Functions
---------
Sometimes ``Rows`` or ``Statements`` are not dynamic enough. So any callable
can be passed as an action. The only requirement is that it accept a lone
argument for the test engine/session.

.. note::

   The same object which is injected into the test function is handed to the provided
   function as its sole argument.

   That is, if you provide ``session=True``, you will receive a session object, whereas
   otherwise you will receive a vanilla engine object.


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
