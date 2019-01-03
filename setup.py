#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import find_packages, setup
import sys

if sys.version_info[0] == 3:
    dev_reqs = 'deps/dev-requirements.txt'
else:
    dev_reqs = 'deps/dev-requirements-py2.txt'


def parse_requirements(filename):
    with open(filename) as f:
        lineiter = (line.strip() for line in f)
        return [
            line.replace(' \\', '').strip()
            for line in lineiter
            if (
                line and
                not line.startswith("#") and
                not line.startswith("-e") and
                not line.startswith("--")
            )
        ]


INSTALL_REQUIREMENTS = parse_requirements('deps/requirements.in')

SETUP_REQUIREMENTS = [
    'pytest-runner',
]

setup(
    name='pytest-dockerdb',
    version='0.1.1',
    url='https://github.com/schireson/schireson-pytest-dockerdb',
    maintainer_email='omar@schireson.com',
    maintainer='Omar Khan',
    description='Pytest plugin for easily instantiating reproduceable Dockerized DB instances for local and CI testing.',
    license='Apache Software License 2.0',

    include_package_data=True,
    install_requires=INSTALL_REQUIREMENTS,
    package_dir={'': 'src'},
    packages=find_packages(where='src', exclude=['tests']),
    python_requires=">2.6, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*, <4",
    setup_requires=SETUP_REQUIREMENTS,
    zip_safe=False,

    test_suite='tests',
    extras_require={
        'develop': parse_requirements(dev_reqs),
    },
    entry_points={
        'pytest11': [
            'dockerdb = pytest_dockerdb',
        ],
    },
)
