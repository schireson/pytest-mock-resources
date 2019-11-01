.. toctree::

.. _redshift-label:

Redshift
========

COPY/UNLOAD
~~~~~~~~~~~

:code:`COPY` and :code:`UNLOAD` will work out of the box, when you're testing code which accepts
a sqlalchemy engine or session object, because we can preconfigure it to work properly. In these
scenarios, you should simply be able to send in the fixture provided into your test and be on
your merry way.

This does **not** work so seemlessly if you're testing code which creates its own connection.
Consider the following module that creates a redshift engine and then uses said engine to run
a :code:`COPY` command:

.. code-block:: python

    # src/app.py
    from sqlalchemy import create_engine

    def main(**connect_args):
        engine = get_redshift_engine(connect_args)

        return run_major_thing(engine)

    def get_redshift_engine(config):
        return create_engine(**config)

    def run_major_thing(engine):
        engine.execute(
            """
            COPY x.y FROM 's3://bucket/file.csv' credentials....
            """
        )

To test this WHOLE module, INCLUDING the engine creation, you will need to use the
:code:`patch_create_engine` decorator.

This allows an engine returned by the :code:`create_engine()` function to support :code:`COPY` and
:code:`UNLOAD` statements.

.. code-block:: python

    #test/test_app

    from pytest_mock_resources import create_redshift_fixture, patch_create_engine

    redshift = create_redshift_fixture()

    from app import main

    @patch_create_engine('app.create_engine')
    def test_main(redshift):
        creds = redshift.credentials.as_psycopg2_connect_args()
        assert main(**creds) == ....


----

Another scenario is if the code under test operates directly on a :code:`psycopg2` connection.
Consider the following module that uses the :code:`psycopg2.connect` function to create a
connection and then uses a cursor to run a :code:`COPY` command:

.. code-block:: python

    # src/app.py
    import psycopg2


    def main(**connect_args):
        with psycopg2.connect(**connect_args) as conn:
            with conn.cursor() as cursor:
                return run_major_thing(cursor)

    def run_major_thing(cursor):
        cursor.execute(
            """
            COPY x.y FROM 's3://bucket/file.csv' credentials....
            """
        )

To test this, you will need to use :code:`patch_psycopg2_connect` decorator.
This allows the cursors stemming from a :code:`psycopg2` connection to support :code:`COPY` and
:code:`UNLOAD` statements.

.. code-block:: python

    #test/test_app

    from pytest_mock_resources import create_redshift_fixture, patch_create_engine

    redshift = create_redshift_fixture()

    from app import main

    @patch_psycopg2_connect('app.psycopg2.connect')
    def test_main(redshift):
        config = redshift.pmr_credentials.as_psycopg2_kwargs()

        assert main(**config) == ....
