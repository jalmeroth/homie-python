#!/usr/bin/env python
"""Provide a setup routine."""
from setuptools import setup

version = "0.4.1"

setup(
    name="homie",
    packages=["homie"],
    version=version,
    description="Implementation of the Homie IoT convention",
    author="Jan Almeroth",
    author_email="homie-python@almeroth.com",
    url="https://github.com/jalmeroth/homie-python",
    download_url=(
        "https://github.com/jalmeroth/homie-python/tarball/" +
        version),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Home Automation"
    ],
    install_requires=[
        'paho-mqtt>=1.3.0',
        'netifaces>=0.10.6'
    ]
)
