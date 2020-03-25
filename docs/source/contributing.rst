Contributing
============

Prerequisites
-------------

If you are not already familiar with Poetry_, this is a poetry project, so you'll need this!

Getting Setup
-------------

See the :code:`Makefile` for common commands, but for some basic setup:

.. code-block:: bash

    # Installs the package with all the extras
    make install

And you'll want to make sure you can run the tests and linters successfully:

.. code-block:: bash

    # Runs CI-level tests, with coverage reports
    make test lint


Tests
~~~~~

A feature of the package is that it doesn't stop you from running tests in parallel, such as
by using :code:`pytest-xdist`. As such :code:`make test` runs the tests in a few different modes.

In general, you can simply run `pytest`, or e.x. `pytest tests/fixture/database/test_udf.py` to
run specific subsets of the tests.


Docs
~~~~

First, install the docs requirements with :code:`pip install -r docs/requirements.txt`,
then use :code:`sphinx` as normal. i.e.

.. code-block:: bash

   cd docs
   make html  # one-time build of the docs
   # or
   make livehtml  # Starts a webserver with livereload of changes


Need help
---------

Submit an issue!

.. _Poetry: https://poetry.eustace.io/
