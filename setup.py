# coding: utf-8

from __future__ import division, absolute_import, print_function, unicode_literals

from setuptools import setup, find_packages


VERSION = '1.2.0'


setup_kwargs = dict(
    name='data_logging',
    version=VERSION,
    description="Common library for logging from python in machine-readable form",
    packages=find_packages(),
    author="HoverHell",
    author_email="hoverhell@gmail.com",
)


if __name__ == "__main__":
    setup(**setup_kwargs)
