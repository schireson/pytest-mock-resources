Fixtures
========

This package gives you the capability to create as many fixtures to represent as many mock instances
of e.g. SQLite, Postgres, Mongo, etc might **actually** exist in your system.

Furthermore, you can prepopulate the connections those fixtures yield to you with whatever
DDL, preset data, or functions you might require.

A new resource (database or otherwise) is created on a per test database, which allows each
fixture to be used in multiple tests without risking data leakage or side-effects from one
test to another.

.. note::

   By default the underlying containers are reused across tests to amortize the container startup
   cost. Tests then create new "resources" (e.g. databases) within that container to avoid
   inter-test pollution.

   This **can** cause inter-test dependencies if your tests are altering container-global resources
   like database users. In the event this is a problem, resources can be configured to **not**
   be session fixtures, although this will likely be drastically slower overall.

See :ref:`Config` for information on customizing the configuration for docker-based fixtures.

.. toctree::

   Relational database fixtures <relational/index.rst>
   Postgres <postgres>
   Redshift <redshift>
   SQLite <sqlite>
   Mongo <mongo>
   Moto <moto>
   Redis <redis>
