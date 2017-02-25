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
import hashlib
import codecs
import gzip
from tests.libtesting.fixtures.datadir import datadir
from edi.lib.debhelpers import download_package


class RepositoryMock():
    def __init__(self, datadir):
        self.datadir = datadir
        self.repository_items = {
            '/foodist/dists/stable/Release': 'Release',
            '/foodist/dists/stable/main/binary-amd64/Packages.gz': 'binary-amd64_Packages.gz',
            '/foodist/dists/stable/main/binary-all/Packages.gz': 'binary-all_Packages.gz',
            '/foodist/pool/main/foo_1.0_amd64.deb': 'foo_1.0_amd64.deb'
        }

    @staticmethod
    def _replace_all(data, dict):
        for key, value in dict.items():
            data = data.replace(key, value)
        return data

    def update_checksums(self):
        deb_names = ['foo_1.0_amd64.deb']
        checksum_dict = {}
        for deb_name in deb_names:
            deb_path = os.path.join(str(self.datadir), deb_name)
            with open(deb_path, mode='rb') as f:
                data = f.read()
                checksum_dict['__{}_md5__'.format(deb_name)] = hashlib.md5(data).hexdigest()
                checksum_dict['__{}_sha1__'.format(deb_name)] = hashlib.sha1(data).hexdigest()
                checksum_dict['__{}_sha256__'.format(deb_name)] = hashlib.sha256(data).hexdigest()

        package_names = ['binary-all_Packages', 'binary-amd64_Packages']
        for package_name in package_names:
            package_path = os.path.join(str(self.datadir), package_name)
            with codecs.open(package_path, encoding='utf-8', mode='r') as f:
                data = f.read()
                data = self._replace_all(data, checksum_dict)
            with codecs.open(package_path, mode='w', encoding='utf-8') as f:
                f.write(data)
            compressed_package_path =  os.path.join(str(self.datadir), '{}.gz'.format(package_name))
            with open(package_path, mode='rb') as f:
                bdata = f.read()
            with gzip.open(compressed_package_path, mode='wb') as f:
                f.write(bdata)

        package_names = ['binary-all_Packages', 'binary-amd64_Packages',
                         'binary-all_Packages.gz', 'binary-amd64_Packages.gz']

        checksum_dict = {}
        for package_name in package_names:
            package_path = os.path.join(str(self.datadir), package_name)
            with open(package_path, mode='rb') as f:
                data = f.read()
                checksum_dict['__{}_md5__'.format(package_name)] = hashlib.md5(data).hexdigest()
                checksum_dict['__{}_sha1__'.format(package_name)] = hashlib.sha1(data).hexdigest()
                checksum_dict['__{}_sha256__'.format(package_name)] = hashlib.sha256(data).hexdigest()

        release_file = 'Release'
        release_file_path = os.path.join(str(self.datadir), release_file)
        with codecs.open(release_file_path, encoding='utf-8', mode='r') as f:
            data = f.read()
            data = self._replace_all(data, checksum_dict)
        with codecs.open(release_file_path, mode='w', encoding='utf-8') as f:
            f.write(data)


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
        repository_mock.update_checksums()
        repository_request_mock.add_matcher(repository_mock.repository_matcher)

        repository = 'deb http://www.example.com/foodist/ stable main contrib'
        repository_key = None  # 'https://www.example.com/keys/archive-key-8.asc'
        package_name = 'foo'
        architectures = ['all', 'amd64']

        workdir = os.path.join(str(datadir), 'workdir')
        os.mkdir(workdir)
        expected_file = os.path.join(workdir, 'foo_1.0_amd64.deb')
        assert not os.path.isfile(expected_file)

        result = download_package(package_name=package_name, repository=repository,
                                  repository_key=repository_key,
                                  architectures=architectures, workdir=workdir)

        assert os.path.isfile(expected_file)
        assert result == expected_file
