#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
from setuptools import setup
from setuptools import find_packages


if sys.argv[-1] == 'publish':
    os.system('python3 setup.py sdist')
    os.system('twine upload dist/*')
    sys.exit()


def readme():
    with open('README.rst') as readme_file:
        return readme_file.read()


def find_version():
    with open('filehandles/__init__.py', 'r') as fd:
        version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                            fd.read(), re.MULTILINE).group(1)
    if not version:
        raise RuntimeError('Cannot find version information')
    return version


REQUIRES = [
    "bz2file >= 0.98"
]


setup(
    name='filehandles',
    version=find_version(),
    author='Andrey Smelter',
    author_email='andrey.smelter@gmail.com',
    description='filehandles is a file handle manager that let you get file handles from different sources.',
    keywords='filehandle handle open file',
    license='BSD',
    url='https://github.com/MoseleyBioinformaticsLab/filehandles',
    packages=find_packages(),
    platforms='any',
    long_description=readme(),
    install_requires=REQUIRES,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)