.PHONY: init set-py3 set-py2 install-deps lint sync-deps publish test clean version bump bump-minor

init:
	bin/pyenv-create-venv pytest-mock-resources

	PYVERSION=2.7.14 bin/pyenv-create-venv pytest-mock-resources-py2

set-py3:
	echo pytest-mock-resources > .python-version

set-py2:
	echo pytest-mock-resources-py2 > .python-version

install-deps:
	pip install -e .[develop]

lint:
	lucha lint
	lucha version diffcheck

sync-deps:
	bin/sync-deps

publish: build
	lucha cicd deploy pypi

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
