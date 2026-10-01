Database Cleanup
================

Each postgres (and redshift) fixture creates a new database for every test. By default, that
database is dropped when the fixture's scope ends, including when the test failed.

Only the database created by the fixture is dropped. Template databases and the container are left
alone, and this setting is independent of the container cleanup controlled by
:code:`pmr_cleanup_container`.

Any connection still open to the database is terminated before it is dropped. A database which is
already gone is ignored. If a database cannot be dropped, a :code:`DatabaseDropWarning` naming the
database is emitted, and the remaining fixtures are still cleaned up.

The behavior can be changed in a number of ways. The first setting found, in the following
order, is used.

* Fixture argument :code:`create_postgres_fixture(cleanup_databases=False)`: Use this option to
  change a single fixture.

* CLI options :code:`pytest --pmr-cleanup-databases` or :code:`pytest --no-pmr-cleanup-databases`:
  Use these options for ad-hoc changes.

* pytest.ini setting :code:`pmr_cleanup_databases = false`: Use this option to change the default
  for all users.

* Default: Databases are dropped.
