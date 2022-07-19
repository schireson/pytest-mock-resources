.PHONY: lock install-base install test-base test-parallel test lint format build-package build-docs build publish
.DEFAULT_GOAL := help

# Install
lock:
	poetry lock

install-base:
	poetry install

install:
	poetry install -E postgres -E postgres-async -E redshift -E mongo -E redis -E mysql

## Test
test-base:
	SQLALCHEMY_WARN_20=1 coverage run -a -m \
		py.test src tests -vv \
		-m 'not postgres and not redshift and not mongo and not redis and not mysql'

test-parallel:
	SQLALCHEMY_WARN_20=1 coverage run -m py.test -n 4 src tests -vv --pmr-multiprocess-safe

test: test-parallel
	SQLALCHEMY_WARN_20=1 coverage run -a -m py.test src tests -vv
	coverage report
	coverage xml

## Lint
lint:
	flake8 src tests || exit 1
	isort --check-only --diff src tests || exit 1
	pydocstyle src tests || exit 1
	black --check src tests || exit 1
	mypy src tests || exit 1

format:
	isort src tests
	black src tests

## Build
build-package:
	poetry build

build-docs:
	pip install -r docs/requirements.txt
	make -C docs html

build: build-package

publish: build
	poetry publish -u __token__ -p '${PYPI_PASSWORD}' --no-interaction
