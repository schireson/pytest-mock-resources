.PHONY: init set-py3 set-py2 install-deps lint sync-deps build build-docs publish publish-docs test clean version bump bump-minor up-postgres

init:
	bin/pyenv-create-venv pytest-mock-resources

	PYVERSION=2.7.14 bin/pyenv-create-venv pytest-mock-resources-py2

set-py3:
	echo pytest-mock-resources > .python-version

set-py2:
	echo pytest-mock-resources-py2 > .python-version

install-deps:
	pip install -e .[mongo,postgres,develop] --no-use-pep517

install-deps-without-extras:
	pip install -e .[develop] --no-use-pep517

lint:
	lucha lint
	lucha version diffcheck

sync-deps:
	bin/sync-deps

build:
	python setup.py sdist bdist_wheel

publish: build
	lucha cicd publish pypi

build-docs:
	lucha build docs

publish-docs: build-docs
	lucha publish docs --latest

cicd-publish-docs: build-docs
	lucha aws whitelist-s3-bucket-policy --bucket docs.schireson.com --profile docs \
	-- lucha publish docs --package pytest_mock_resources --profile docs --latest

test:
	pytest -n 4

test-without-extras:
	pytest -n 4 -m 'not postgres and not redshift and not mongo'

clean:
	lucha env clean

version:
	lucha version get

bump:
	# For an arbitrary or additive change.
	lucha version bump

bump-minor:
	# For a backwards incompatible change.
	lucha version bump --minor
