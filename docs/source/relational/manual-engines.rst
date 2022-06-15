Manually Constructed Engines
============================
Due to the dynamic nature of the creation of the databases themselves, its
non-trivial for a user to know what the connection string, for example, would
be for the database ahead of time. Which makes testing code which manually
constructs its own :class:`sqlalchemy.Engine` objects internally more difficult.

Therefore, generally preferable way to use the fixtures is that you will be yielded
a preconstructed engine pointing at the database to which your test is intended
to run against; and to write your code such that it accepts the engine as a
function/class parameter.

However, this is not always possible for all classes of tests, nor does it help
for code which might already be written with a tightly coupled mechanism for
engine creation.

For (contrived) example:

.. code-block:: python
   :caption: package/entrypoint.py

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

As you can see, in order to test these functions, we must pass in valid **credentials**
rather than an engine itself.

pmr_credentials
---------------
Each of the fixtures you might create will attach a :code:`pmr_credentials`
attribute onto the engine it yields to the test which will be an instance of a
:class:`Credentials` class.

Attributes on this class include all the credentials required to connect to the
particular database. Additionally, there are convenience methods specifically meant to
coerce the credentials into a form directly accepted by common connection
mechanisms like :class:`psycopg2.connect` or :class:`sqlalchemy.engine.url.URL`.

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

   def test_sqlalchemy_main_postgres(postgres):
       credentials = postgres.pmr_credentials
       result = entrypoint.sqlalchemy_main(**credentials.as_url())
       assert result ...
