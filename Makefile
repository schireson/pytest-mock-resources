.PHONY: lock install-base install test-base test-parallel test lint format build-package build-docs build publish
.DEFAULT_GOAL := help

# Install
lock:
	uv lock

install-base:
	uv sync

install:
	uv sync --extra postgres --extra postgres-async --extra redshift --extra mongo --extra redis --extra mysql --extra moto

## Test
test-base:
	SQLALCHEMY_WARN_20=1 coverage run -a -m \
		pytest src tests -vv \
		-m 'not postgres and not redshift and not mongo and not redis and not mysql and not moto'

test-parallel:
	SQLALCHEMY_WARN_20=1 coverage run -m pytest -n 4 src tests -vv --pmr-multiprocess-safe

test: test-parallel
	SQLALCHEMY_WARN_20=1 coverage run -a -m pytest src tests -vv
	coverage report
	coverage xml

## Lint
lint:
	ruff --fix src tests || exit 1
	ruff format -q src tests || exit 1
	mypy src tests --show-error-codes || exit 1

format:
	ruff src tests --fix
	ruff format src tests

## Build
build-package:
	uv build

build-docs:
	uv sync --group docs
	uv run make -C docs html

build: build-package

publish: build
	uv publish --token '${PYPI_PASSWORD}'
