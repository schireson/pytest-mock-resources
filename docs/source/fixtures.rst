Fixtures
========

This package gives you the capability to create as many fixtures to represent as many mock instances
of e.g. SQLite, Postgres, Mongo, etc might **actually** exist in your system.

Furthermore, you can prepopulate the connections those fixtures yield to you with whatever
DDL, preset data, or functions you might require.

Each fixture you create can be used in multiple tests without risking data leakage or side-effects
from one test to another, see :ref:`internals-label` for more details.


.. toctree::

   Relational database fixtures <database>
   Redshift <redshift>
   SQLite <sqlite>
   Mongo <mongo>
   Redis <redis>
   MySQL <mysql>

   Internals <internals>
