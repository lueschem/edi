# -*- coding: utf-8 -*-
# Copyright (C) 2017 Matthias Luescher
#
# Authors:
#  Matthias Luescher
#
# This file is part of edi.
#
# edi is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# edi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with edi.  If not, see <http://www.gnu.org/licenses/>.

import requests
import requests_mock
import os
from tests.libtesting.fixtures.datadir import datadir
from edi.lib.debhelpers import download_package


class RepositoryMock():
    def __init__(self, datadir):
        self.datadir = datadir
        self.repository_items = {
            '/foodist/dists/stable/Release': 'Release',
            '/foodist/dists/stable/main/binary-amd64/Packages.gz': 'binary-amd64_Packages.gz',
            '/foodist/dists/stable/main/binary-all/Packages.gz': 'binary-all_Packages.gz',
            '/foodist/pool/main/foo_1.0.0_amd64.deb': 'foo_1.0_amd64.deb'
        }

    def repository_matcher(self, request):
        print('Requesting {}.'.format(request.path_url))
        for key, value in self.repository_items.items():
            if request.path_url == key:
                print('Sending {}.'.format(value))
                return self._send_response(request, value)

        print('Sending 404.')
        return requests_mock.create_response(request, status_code=404)

    def _send_response(self, request, filename):
        file_path = os.path.join(str(self.datadir), filename)
        with open(file_path, mode='rb') as f:
            return requests_mock.create_response(request, content=f.read())


def test_package_download_without_key(datadir):
    with requests_mock.Mocker() as repository_request_mock:
        repository_mock = RepositoryMock(datadir)
        repository_request_mock.add_matcher(repository_mock.repository_matcher)

        repository = 'deb http://www.example.com/foodist/ stable main contrib'
        repository_key = None  # 'https://www.example.com/keys/archive-key-8.asc'
        package_name = 'foo'
        workdir = os.path.join(str(datadir), 'workdir')
        os.mkdir(workdir)
        architectures = ['all', 'amd64']
        result = download_package(package_name=package_name, repository=repository,
                                  repository_key=repository_key,
                                  architectures=architectures, workdir=workdir)
        print('Downloaded {}.'.format(result))
