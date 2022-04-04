.. _template-database:

Template Databases
==================

.. note::

   This feature was added in v2.4.0 and **currently only supports Postgres**.

   The `template_database` fixture keyword argument, and :class:``StaticStatements``
   did not exist prior to this version.

By default, the supported fixtures attempt to amortize the cost of performing fixture
setup through the creation of database templates
(`postgres <postgres_template_database>`_).
If, for whatever reason, this feature does not interact well with your test setup,
you can disable the behavior by setting ``template_database=False``.

With this feature enabled, all actions considered to be "safe" to statically
will performed exactly once per test session, in a template database.
This amortizes their initial cost and offloads the majority of the work to postgres
itself. Then all "dynamic" actions will be performed on a per-test-database basis.

Consider the following fixture

.. code-block:: python

   from models import Base, Example
   from pytest_mock_resources import create_postgres_fixture, StaticStatements, Statements, Rows

   def some_setup(engine):
       # some complex logic, not able to be performed as a `Statements`

   pg = create_postgres_fixture(
       Base,
       Rows(Example(id=1)),
       StaticStatements('INSERT INTO foo () values ()'),
       Statements('INSERT INTO foo () values ()'),
       some_setup,
   )


Each of the arguments given to ``create_postgres_fixture`` above are "actions" performed
in the given order. Typically (in particular for non-postgres fixtures, today),
all of the steps would be performed on a completely empty database prior to the
engine/session being handed to the test function.

Static Actions
--------------
Static actions are actions which are safe to be executed exactly once, because they
have predictable semantics which both safely be executed once per test session,
as well as happen in a completely separate transactiona and database, from the
one handed to the test.

Static actions include:

* ``MetaData``: ``Base`` in the above example is an alias to ``Base.metadata``;
  i.e. a :class:`sqlalchemy.MetaData` object that creates all objects defined on the metadata.
* ``Rows``: Rows only work in the context of a session, and essentially define a set of 
  ``INSERT`` statements to be run.
* ``StaticStatements``: Are exactly like a :class:`Statements` object. The subclass
  is simply a sentinel to signify that the user asserts their statement is "safe"
  to be executed as one of these static actions.


Dynamic Actions
---------------
Dynamic actions have unpredictable semantics, and as such the library cannot
safely amortize their cost.

Dynamic actions include:

* ``Statements``: A statement can be any arbitrary SQL, which therefore means we cannot
  know whether it will react negatively with the test, if executed in a separate
  transaction. If you're executing typical ``CREATE``/``INSERT`` statements,
  prefer ``StaticStatements``.

* Functions: Obviously a function can do anything it wants, and therefore must be
  dynamic.


.. admonition:: warning

   It is important to consider action ordering when using dynamic actions. Upon
   encountering a dynamic action in a list of ordered actions, all subsequent
   actions will be executed as though they were dynamic (i.e. per-test-database).

   You should therefore prefer to group all static actions before dynamic ones
   whereever possible to ensure you get the most optimal amortization of actions.

   For example:

   .. code-block:: python

      pg = create_postgres_fixture(
          Statements('CREATE TABLE ...'),
          Base,
      )

   This will execute all setup dynamically because it encountered a dynamic action
   (``Statements`` in this case) first. Ideally the above actions would be reversed,
   or that the ``Statements`` be swapped for a ``StaticStatements``.


.. _postgres_template_database: https://www.postgresql.org/docs/current/manage-ag-templatedbs.html
