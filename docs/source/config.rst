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
