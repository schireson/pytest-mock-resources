## Contributing Pre-Requisites

* [Lucha](https://github.com/schireson/lucha/) must be globally installed (preferably via pipx) to run most MakeFile commands.

## Running the tests

* Running the unit tests: `pytest` or `make test`
* Running the linters: `make lint`

## Changing the dependencies

### Adding a new dependency

Add the requirements to the relevant package's `deps/requirements.in` or `deps/dev-requirements.in`
then (inside the package's folder) run:

    make sync-deps

### Synchronizing your virtualenv with the requirements

    make init

### Updating an existing dependency

    pip-compile --upgrade-package docker
