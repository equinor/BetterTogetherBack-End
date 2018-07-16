#!/usr/bin/env python

from setuptools import setup

_requirements = []
with open('requirements.txt', 'r') as f:
    _requirements = [line.strip() for line in f]

setup(
    name='BetterTogetherBack-End',
    packages=[
        'backend',
    ],
    author='Software Innovation Bergen, Summer Students',
    description="Back end for BetterTogether",
    install_requires=_requirements,
    test_suite='tests',
)
