CI Service Support
==================

Depending on the CI service, access to docker-related fixtures may be different than it would be
locally. As such, below is an outline of how to support those fixtures within specific CI services.

CircleCi
--------
CircleCI 2.0+ default jobs do not have access to a docker directly, but instead interact with
a remote docker.

As such, you will need to include the a step in your job to setup remote docker like so:

.. code-block:: yaml
    
    steps:
      - setup_remote_docker
      - checkout
      ...


Furthermore, you should start the service ahead of time using their mechanism of choice:

For 2.0 jobs

.. code-block:: yaml

    jobs:
      <YOUR JOB NAME>:
          docker:
          - image: <YOUR IMAGE>
          - image: <SERVICE IMAGE>
    

For 2.1+ jobs

.. code-block:: yaml

    version: 2.1

    executors:
      foo:
        docker:
          - image: <YOUR IMAGE>
          - image: <SERVICE IMAGE>
        
    jobs:
      test:
        executor: foo


Postgres/Redshift
~~~~~~~~~~~~~~~~~

Specifically for postgres/redshift, the :code:`- image: <SERVICE IMAGE>` portion should look like

.. code-block:: yaml

    - image: postgres:9.6.10-alpine  # or whatever image/tag you'd like
      environment:
        POSTGRES_DB: dev
        POSTGRES_USER: user
        POSTGRES_PASSWORD: password


You will receive a `ContainerCheckFailed: Unable to connect to [...] Postgres test container` error in CI if the above is not added to you job config.

Mongo
~~~~~

Specifically for mongo, the :code:`- image: <SERVICE IMAGE>` portion should look like

.. code-block:: yaml

    - image: circleci/mongo:3.6.12   # or whatever image/tag you'd like
      command: "mongod --journal"

You will receive a `ContainerCheckFailed: Unable to connect to [...] Mongo test container` error in CI if the above is not added to you job config.


GitLab
------
For :code:`pytest-mock-resources` to work on GitLab use of :code:`dind` service is required.
Below is a sample configuration:

.. code-block:: yaml

    services:
      - docker:dind

    variables:
      DOCKER_TLS_CERTDIR: ''

    stages:
      - testing

    testing-job:
      image: python:3.6.8-slim # Use a python version that matches your project
      stage: testing
      variables:
        DOCKER_HOST: tcp://docker:2375
        PYTEST_MOCK_RESOURCES_HOST: docker
      before_script:
        - apt-get update && apt-get install -y wget libpq-dev gcc
        - wget -O get-docker.sh https://get.docker.com
        - chmod +x get-docker.sh && ./get-docker.sh
      script:
        - pip install -r requirements.txt
        - pytest -x tests

