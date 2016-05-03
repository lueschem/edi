#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (C) 2016 Matthias Lüscher
#
# Authors:
#  Matthias Lüscher
#
# This file is part of edi.
#
# edi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# edi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with edi.  If not, see <http://www.gnu.org/licenses/>.

# setup.py according to
# http://python-packaging-user-guide.readthedocs.io/en/latest/distributing/

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='edi',

    use_scm_version=True,
    setup_requires=['setuptools_scm'],

    description='Embedded Development Infrastructure - edi',
    long_description=long_description,

    url='https://gitlab.com/lueschem/edi',

    # Author details
    author='Matthias Luescher',
    author_email='lueschem@gmail.com',

    # Choose your license
    license='GPLv3+',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',

        'Programming Language :: Python :: 3.5',
    ],

    keywords='embedded Linux container toolchain',

    packages=find_packages(exclude=['docs', 'debian', 'bin', '.git']),

    install_requires=['ansible'],

    extras_require={
    #    'dev': ['check-manifest'],
    #    'test': ['coverage'],
    },

    package_data={
    #    'sample': ['package_data.dat'],
    },

    #data_files=[('my_data', ['data/data_file'])],

    entry_points={
        'console_scripts': [
            'edi=edi:main',
        ],
    },
)
