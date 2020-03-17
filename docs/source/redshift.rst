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

This **should** also work seamlessly if you're testing code which creates its own connection directly.
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


The :code:`redshift` fixture should automatically instrument direct calls to
:func:`psycopg2.connect` (or :func:`sqlalchemy.create_engine`.
