SQLite
======
While SQLite is a widely used database in its own right, we also aim to make SQLite a reasonable
stand-in for (at least) postgres, in tests where possible. We **do** make postgres tests run as
fast as possible, but tests using postgres objectively run more slowly than those with SQLite.

While SQLite cannot match Postgres perfectly, in many scenarios (particularly those which use ORMs,
which tend to make use of cross-compatible database features) it can be used to more quickly verify
the code. And in the event that you begin using a feature only supportable in postgres, or which
behaves differently in SQLite, you're one :code:`s/create_slite_fixture/create_postgres_fixture`
away from resolving that problem. Additionally, you can choose to only use postgres for the subset
of tests which require such features.

To that end, we've extended the sqlalchemy SQLite dialect to include features to match postgres
as closely as possible. We **do** however, recommend that use of this dialect is restricted
purely to **tests** in order to be used as a postgres stand-in, rather than for use in actual
application code.

Schemas
-------
As an in-memory database (for the most part), SQLite does not behave the same way when encountering
schemas.

For example, given sqlalchemy model defined as:

.. code-block:: python

    from .models import ModelBase

    class User(ModelBase):
        __tablename__ ='user'
        __table_args__ = {'schema': 'private'}


SQLite generally would produce an error upon use of that table, but will now work by default, and
behave similarly to postgres.

A caveat to this is that SQLite has no notion of a "search path" like in postgres. Therefore,
programmatic use altering the search path from the default "public" (in postgres), or referencing
a "public" table as "public.tablename" would not be supported.


Foreign Keys
------------
SQLite supports FOREIGN KEY syntax when emitting CREATE statements for tables,
however by default these constraints have no effect on the operation of the table.

We simply, turn that support on by default, to match the postgres behavior.


JSON/JSONB
----------
Tables which use either :code:`sqlalchemy.dialects.postgresql.JSON/JSONB` or
:code:`sqlalchemy.types.Json` will work as they would in postgres.

SQLite itself, recently added support for json natively, but this allows a much wider version
range of SQLite to support that feature.


Datetime (timezone support)
---------------------------
By default, SQLite does not respect the :code:`Datetime(timezone=True)` flag. This means that normally
a :code:`Datetime` column would behave differently from postgres. For example, where postgres
would return timezone-aware :code:`datetime.datetime` objects, SQLite would return naive
:code:`datetime.datetime` (which do **not** behave the same way when doing datetime math).

This does **not** actually store the timezones of the datetime (as is also true for postgres).
It simply matches the timezone-awareness and incoming timezone conversion behavior you see in
postgres.
