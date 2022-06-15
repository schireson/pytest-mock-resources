Basics
------
Say you've written a function, which accepts a :class:`sqlalchemy.Engine`, and
performs some operation which is literally not able to be tested without a
connection to a real database.

.. code-block:: python
   :caption: package/utilities.py

   def sql_sum(redshift_conn):
       """SUPER OPTIMIZED WAY to add up to 15.
       """
       redshift_conn.execute("CREATE TEMP TABLE mytemp(c INT);")
       redshift_conn.execute(
           """
           INSERT INTO mytemp(c)
           VALUES (1), (2), (3), (4), (5);
           """
       )

       return redshift_conn.execute("SELECT SUM(c) FROM mytemp;").fetchone()

With this library, you would define your test fixture, for the corresponding
database in use. And then any references to that fixture in a test, will produce 
a :class:`sqlalchemy.Engine`.

Alternatively, you can specify `session=True`, to ensure you're handed a
:class:`sqlalchemy.orm.Session` instead.

.. code-block:: python
   :caption: tests/test_utilities.py

   # Redshift Example:
   from pytest_mock_resources import create_redshift_fixture
   from package.utilities import sql_sum

   db = create_redshift_fixture()
   # or
   db = create_redshift_fixture(session=True)

   def test_sql_sum(db):
      sql_sum(db)


   # Postgres Example:
   from pytest_mock_resources import create_postgres_fixture
   from package.utilities import sql_sum

   db = create_postgres_fixture()
   # or
   db = create_postgres_fixture(session=True)

   def test_sql_sum(db):
      sql_sum(db)


Note that beyond your definition of the fixture, the test code remains
exactly the same between examples among different databases.

What's happening when under the hood is that a docker container (except
with SQLite) is being spun up on a per-test-session basis, and then
individual sub-container databases are being created on a per-test basis,
and yielded to each test.
