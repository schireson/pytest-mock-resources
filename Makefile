.PHONY: init set-py3 set-py2 install-deps lint sync-deps build publish test clean version bump bump-minor up-postgres

init:
	bin/pyenv-create-venv pytest-mock-resources

	PYVERSION=2.7.14 bin/pyenv-create-venv pytest-mock-resources-py2

set-py3:
	echo pytest-mock-resources > .python-version

set-py2:
	echo pytest-mock-resources-py2 > .python-version

install-deps:
	pip install -e .[postgres,develop]

lint:
	lucha lint
	lucha version diffcheck

sync-deps:
	bin/sync-deps

build:
	python setup.py sdist bdist_wheel

publish: build
	lucha cicd publish pypi

test:
	pytest

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

# Use this command to create a detached postgres container.
# This library's tests create and destroy a container during every run. this makes test-start-up slow.
# Test runs will be faster as they will not have to orchestrate any container managament.
up-postgres:
	docker run -d \
		-p 5532:5432 \
		-e POSTGRES_DB=dev \
		-e POSTGRES_USER=user \
		-e POSTGRES_PASSWORD=password \
		postgres
