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

    def repository_matcher(self, request):
        if request.path_url == '/debian//dists/jessie/Release': #TODO: remove double slash
            return requests_mock.create_response(request, text='foo_response')
        elif request.path_url == '/pool/bar':
            return requests_mock.create_response(request, text='bar_response')
        else:
            return requests_mock.create_response(request, status_code=404)


def test_package_download_without_key(datadir):

    with requests_mock.Mocker() as repository_request_mock:
        repository_mock = RepositoryMock(datadir)
        repository_request_mock.add_matcher(repository_mock.repository_matcher)

        repository = 'deb http://www.example.com/debian/ jessie main contrib'
        repository_key = None  # 'https://www.example.com/keys/archive-key-8.asc'
        package_name = 'foo'
        workdir = os.path.join(str(datadir), 'workdir')
        os.mkdir(workdir)
        architectures = ['all', 'amd64']
        #result = download_package(package_name=package_name, repository=repository,
        #                          repository_key=repository_key,
        #                          architectures=architectures, workdir=workdir)
        #print('Downloaded {}.'.format(result))

        assert requests.get('http://example.com/debian//dists/jessie/Release').text == 'foo_response'
        assert requests.get('http://example.com/pool/bar').text == 'bar_response'
        assert requests.get('http://example.com/pool/baz').status_code == 404

