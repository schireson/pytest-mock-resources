.PHONY: lock install-base install test-base test-parallel test lint format build-package build-docs build publish
.DEFAULT_GOAL := help

# Install
lock:
	poetry lock

install-base:
	poetry install

install: install-base
	poetry install -E postgres -E postgres-async -E redshift -E mongo -E redis -E mysql

## Test
test-base:
	coverage run -a -m \
		py.test src tests -vv \
		-m 'not postgres and not redshift and not mongo and not redis and not mysql'

test-parallel:
	coverage run -m py.test -n 4 src tests -vv

test: test-parallel
	coverage run -a -m py.test src tests -vv
	coverage report
	coverage xml

## Lint
lint:
	flake8 src tests
	isort --check-only --diff src tests
	pydocstyle src tests
	black --check src tests
	mypy src tests

format:
	isort --recursive src tests
	black src tests

## Build
build-package:
	poetry build

build-docs:
	pip install -r docs/requirements.txt
	make -C docs html

build: build-package build-docs

publish: build
	poetry publish -u __token__ -p '${PYPI_PASSWORD}' --no-interaction
