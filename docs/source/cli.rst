CLI
===

As you start writing tests, you might notice that there's a small delay after
invoking the tests before they execute. Which can get particularly annoying
if you're only running a small subset of your tests at a time. This delay is
because the default execution mode will kill all the containers that were
started by the test suite each time it's executed.

However, some containers have a larger startup cost than others; Mongo and presto,
in particular have significant startup costs up to 30s! Even Postgres,
has ~ 1-2 seconds startup time; which you'll pay each time you invoke :code:`pytest`.

Pytest Mock Resources ships with a small CLI utility ``pmr``, which can be
used to help amortize the cost of container startup between test runs. With it,
you can pre-create the container against which the tests will connect.

For Redshift and Postgres:

.. code-block:: bash

    $ pmr postgres
    711f5d5a86896bb4eb76813af4fb6616aee0eff817cdec6ebaf4daa0e9995441
    # or specify the image
    PMR_POSTGRES_IMAGE=postgres:11 pmr postgres
    711f5d5a86896bb4eb76813af4fb6616aee0eff817cdec6ebaf4daa0e9995441

For Mongo:

.. code-block:: bash

    $ pmr mongo
    711f5d5a86896bb4eb76813af4fb6616aee0eff817cdec6ebaf4daa0e9995441
    # or specify the image
    PMR_MONGO_IMAGE=mongo:5.0 pmr mongo
    711f5d5a86896bb4eb76813af4fb6616aee0eff817cdec6ebaf4daa0e9995441

For MySQL:

.. code-block:: bash

    $ pmr mysql
    711f5d5a86896bb4eb76813af4fb6616aee0eff817cdec6ebaf4daa0e9995441
    # or specify the image
    PMR_MYSQL_IMAGE=postgres:8.0 pmr mysql
    711f5d5a86896bb4eb76813af4fb6616aee0eff817cdec6ebaf4daa0e9995441

You can check on the instance's state via:

.. code-block:: bash

    $ docker ps
    CONTAINER ID        IMAGE                    COMMAND                  CREATED             STATUS              PORTS                    NAMES
    711f5d5a8689        postgres:9.6.10-alpine   "docker-entrypoint.s…"   16 seconds ago      Up 15 seconds       0.0.0.0:5532->5432/tcp   determined_euclid

You can terminate the instance whenever you want via:

.. code-block:: bash

    $ pmr --stop postgres
    711f5d5a86896bb4eb76813af4fb6616aee0eff817cdec6ebaf4daa0e9995441

