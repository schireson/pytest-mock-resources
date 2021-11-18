Docker
======

In order to run tests which interact with **most** fixture types (sqlite being an example of one
such exception). Docker needs to be available and running:

Make sure you have docker installed:

* MacOs_
* Nix_
* Windows_


Once you have docker installed, :code:`pytest` will automatically up and down any necessary docker
containers so you don't have to, by default all containers will be spun up/down per :code:`pytest`
invocation.

Startup Lag
-----------

The default execution mode will kill all the containers that were started by the test suite each
time it's executed.

However, some containers have a larger startup cost than others; Mongo and presto, in particular
have significant startup costs that don't play well with rapid development. Even postgres though,
has ~ 1-2 seconds delay each time you run :code:`pytest` which can quickly become annoying.

To circumvent this cost, :code:`pytest-mock-resources` ships with a small CLI tool called
:code:`pmr`, which simply starts a single persistent container per fixture type (though
redshift/postgres share one), which avoids that cost!

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

    $ docker stop 711f5d5a8689  # where 711f5d5a8689 is the `CONTAINER ID` from `docker ps`
    711f5d5a86896bb4eb76813af4fb6616aee0eff817cdec6ebaf4daa0e9995441


.. _docker-config-label:

Config
------

In order to support various projects and environments in which tests might be run, each docker-based
fixture has the ability to customize its default configuration.

The precedence of the available config mechanisms follow the order:

* Environment variables
* Fixture Configuration
* Default Configuration


Environment Variables
~~~~~~~~~~~~~~~~~~~~~

In general we would only recommend use of the environment variable config for temporary
changes to a value, or for configuration that is specific to the environment in which it is being run.

A common use case for this mechanism is local port conflicts. When a container is started up,
we bind to a pre-specified port for that resource kind. We (attempt to) avoid conflicts
by binding to a non-standard port for that resource by default, but conflicts can still happen

All configuration options for the given resource are available under env vars named in the pattern:

.. code-block:: bash

   PMR_{RESOURCE}_{CONFIG}
   # e.x.
   export PMR_POSTGRES_PORT=54321

Resource is the name of the resource, i.e. POSTGRES, MONGO, REDIS, etc

CONFIG is the name of the config name. Every container will support at **least**: IMAGE, HOST, PORT, and CI_PORT.


Fixture Configuration
~~~~~~~~~~~~~~~~~~~~~

In general, we recommend fixture configuration for persistent configuration that is an attribute
of the project itself, rather than the environment in which the project is being run.

The most common example of this will be :code:`image`. If you're running postgres:8.0.0 in production,
you should not be testing with our default image version! Other resource-specific configurations,
such as :code:`root_database`, might also be typical uses of this mechanism.

Here, the pattern is by defining a fixture in the following pattern:

.. code-block:: python

   @pytest.fixture(scope='session')
   def pmr_{resource}_config():
       return {Resource}Config(...options...)

I.e. :code:`pmr_postgres_config`, returning a :class:`PostgresConfig` type. might look like

.. code-block:: python
   :caption: conftest.py

   import pytest
   from pytest_mock_resources import PostgresConfig

   @pytest.fixture(scope='session')
   def pmr_postgres_config():
       return PostgresConfig(image='postgres:11.0.0')

Default Configuration
~~~~~~~~~~~~~~~~~~~~~

Default configuration uses the same mechanism (i.e. fixture configuration) as you might, to
pre-specify the default options, so that the plugin can usually be used as-is with no
configuration.

The configuration defaults should not be assumed to be static/part of the API (and typically
changes should be irrelevant to most users).

See the :ref:`api` docs for details on the current defaults.


Testing from WITHIN a container
-------------------------------

Add the following mount to your :code:`docker run` command which will allow :code:`pytest` to
communicate with your host machine's docker CLI:

.. code-block:: bash

    docker run -v /var/run/docker.sock:/var/run/docker.sock [..other options] <IMAGE>


.. _MacOs: https://docs.docker.com/docker-for-mac/install/
.. _Nix: https://docs.docker.com/install/
.. _Windows: https://docs.docker.com/docker-for-windows/install/
