Database Cleanup
================

Each postgres (and redshift) fixture creates a new database for every test. By default, that
database is dropped when the fixture's scope ends, including when the test failed.

The template database a fixture creates (:code:`pmr_template_pg_<uuid>`) is dropped as well. Each
pytest process creates its own templates, so each process drops only its own. They are dropped when
the container fixture ends, after every fixture using the container has finished, which for the
default session scoped container is the end of the test session.

Only databases created by PMR are dropped, so a template you name with :code:`createdb_template`
is left alone. The setting is independent of the container cleanup controlled by
:code:`pmr_cleanup_container`.

Any connection still open to a database is terminated before it is dropped. A database which is
already gone is ignored. If a database cannot be dropped, a :code:`DatabaseDropWarning` naming the
database is emitted, and the remaining fixtures are still cleaned up.

Templates left behind by a pytest process that was killed are not dropped.

The behavior can be changed in a number of ways. The first setting found, in the following
order, is used.

* Fixture argument :code:`create_postgres_fixture(cleanup_databases=False)`: Use this option to
  change a single fixture.

* CLI options :code:`pytest --pmr-cleanup-databases` or :code:`pytest --no-pmr-cleanup-databases`:
  Use these options for ad-hoc changes.

* pytest.ini setting :code:`pmr_cleanup_databases = false`: Use this option to change the default
  for all users.

* Default: Databases are dropped.
