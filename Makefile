.PHONY: init set-py3 set-py2 install-deps lint sync-deps build test clean bump bump-minor

init:
	bin/pyenv-create-venv pytest-dockerdb

	PYVERSION=2.7.14 bin/pyenv-create-venv pytest-dockerdb-py2

set-py3:
	echo pytest-dockerdb > .python-version

set-py2:
	echo pytest-dockerdb-py2 > .python-version

install-deps:
	pip install -e .[develop]

lint:
	bin/lint
	bin/diffcheck

sync-deps:
	bin/sync-deps

build:
	python setup.py sdist bdist_wheel

publish: build
	bin/publish

test:
	pytest -m "not functional"

clean:
	rm -rf `find . -type d -name ".pytest_cache"`
	rm -rf `find . -type d -name "*.eggs"`
	rm -rf `find . -type d -name "*.egg-info"`
	rm -rf `find . -type d -name "__pycache__"`
	rm -rf `find . -type f -name "*.pyc"`
	rm -rf `find . -type f -name "*.pyo"`

	rm -f junit_results.xml .coverage
	rm -rf build dist coverage .mypy_cache .eggs

version:
	python setup.py -V

bump:
	# For an arbitrary or additive change.
	bumpversion patch

bump-minor:
	# For a backwards incompatible change.
	bumpversion minor
