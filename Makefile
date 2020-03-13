.PHONY: lock install-base install test-base test-parallel test lint format build-package build-docs build publish
.DEFAULT_GOAL := help

# Install
lock:
	poetry lock

install-base:
	poetry install

install: install-base
	poetry install -E postgres -E redshift -E mongo -E redis -E docs

## Test
test-base:
	poetry run coverage run -a -m \
		py.test src tests -vv \
		-m 'not postgres and not redshift and not mongo and not redis'

test-parallel:
	poetry run coverage run -a -m \
		py.test -n 4 src tests -vv

test: test-parallel
	poetry run coverage run -a -m \
		py.test src tests -vv
	poetry run coverage report
	poetry run coverage xml

## Lint
lint:
	poetry run flake8 src tests
	poetry run isort --check-only --recursive src tests
	poetry run pydocstyle src tests
	poetry run black --check src tests
	poetry run mypy src tests

format:
	poetry run isort --recursive src tests
	poetry run black src tests

## Build
build-package:
	poetry build

build-docs:
	poetry run make -C docs html

build: build-package build-docs

publish: build
	poetry publish -u __token__ -p '${PYPI_PASSWORD}' --no-interaction
