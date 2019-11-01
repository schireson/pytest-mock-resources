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

For Mongo:

.. code-block:: bash

    $ pmr mongo
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


Testing from WITHIN a container
-------------------------------

Add the following mount to your :code:`docker run` command which will allow :code:`pytest` to
communicate with your host machine's docker CLI:

.. code-block:: bash

    docker run -v /var/run/docker.sock:/var/run/docker.sock [..other options] <IMAGE>


.. _MacOs: https://docs.docker.com/docker-for-mac/install/
.. _Nix: https://docs.docker.com/install/
.. _Windows: https://docs.docker.com/docker-for-windows/install/
