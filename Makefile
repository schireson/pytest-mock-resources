.PHONY: lock install-base install test-base test-parallel test lint format build-package build-docs build publish
.DEFAULT_GOAL := help

# Install
lock:
	poetry lock

install-base:
	poetry install

install:
	poetry install -E postgres -E postgres-async -E redshift -E mongo -E redis -E mysql -E moto

## Test
test-base:
	SQLALCHEMY_WARN_20=1 poetry run coverage run -a -m \
		pytest src tests -vv \
		-m 'not postgres and not redshift and not mongo and not redis and not mysql and not moto'

test-parallel:
	SQLALCHEMY_WARN_20=1 poetry run coverage run -m pytest -n 4 src tests -vv --pmr-multiprocess-safe

test: test-parallel
	SQLALCHEMY_WARN_20=1 poetry run coverage run -a -m pytest src tests -vv
	poetry run coverage report
	poetry run coverage xml

## Lint
lint:
	poetry run ruff --fix src tests || exit 1
	poetry run ruff format -q src tests || exit 1
	poetry run mypy src tests --show-error-codes || exit 1

format:
	poetry run ruff src tests --fix
	poetry run ruff format src tests

## Build
build-package:
	poetry build

build-docs:
	pip install -r docs/requirements.txt
	make -C docs html

build: build-package

publish: build
	poetry publish -u __token__ -p '${PYPI_PASSWORD}' --no-interaction

.PHONY: prerelease
prerelease:
	poetry version prerelease
	git add pyproject.toml
	git commit -m "Release version $$(poetry version --short)"
	git tag $$(poetry version --short)
