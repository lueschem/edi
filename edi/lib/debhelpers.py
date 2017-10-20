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
import os
import subprocess
import tempfile
import re
import debian.deb822
import hashlib
import logging
from aptsources.sourceslist import SourceEntry
from edi.lib.helpers import FatalError
from edi.lib.archivehelpers import decompress
from edi.lib.keyhelpers import fetch_repository_key, build_keyring


class PackageDownloader():
    def __init__(self, repository=None, repository_key=None, architectures=None):
        if not repository:
            raise FatalError('''Missing argument 'repository'.''')
        if not architectures:
            raise FatalError('''Missing (non empty) list 'architectures'.''')
        self._repository = repository
        self._repository_key = repository_key
        self._architectures = architectures
        self._source = SourceEntry(repository)
        self._source.uri = self._source.uri.rstrip('/')
        self._compressions = ['gz', 'bz2', 'xz']
        self._checksum_algorithms = ['SHA512', 'SHA256']  # strongest first

    def _get_release_file_url(self, filename):
        return '{}/dists/{}/{}'.format(self._source.uri, self._source.dist, filename)

    def _fetch_archive_element(self, url):
        return self._fetch_archive_element_impl(url, check=True)

    def _try_fetch_archive_element(self, url):
        return self._fetch_archive_element_impl(url, check=False)

    @staticmethod
    def _fetch_archive_element_impl(url, check=True):
        req = requests.get(url)
        if req.status_code != 200:
            if check:
                raise FatalError(("Unable to fetch archive element '{0}'."
                                  ).format(url))
            else:
                return None

        return req.content

    def _parse_release_file(self, release_file):
        with open(release_file) as file:
            main_content = next(debian.deb822.Release.iter_paragraphs(file))
            section = None
            for algoritm in self._checksum_algorithms:
                section = main_content.get(algoritm)
                if section:
                    break

            if not section:
                raise FatalError(("No valid section ({}) found in release file downloaded from '{}'."
                                  ).format(' or '.join(a for a in self._checksum_algorithms),
                                           self._get_release_file_url('')))

            packages_filter = ['{}/binary-{}/Packages.{}'.format(component, architecture, compression)
                               for component in self._source.comps
                               for architecture in self._architectures
                               for compression in self._compressions]

            package_files = [element for element in section if element.get('name') in packages_filter]

            return package_files

    def _verify_signature(self, homedir, keyring, signed_file, detached_signature=None):
        cmd = ['gpg']
        cmd.extend(['--homedir', homedir])
        cmd.extend(['--weak-digest', 'SHA1'])
        cmd.extend(['--weak-digest', 'RIPEMD160'])
        cmd.extend(['--no-default-keyring', '--keyring', keyring])
        cmd.extend(['--status-fd', '1'])
        cmd.append('--verify')
        if detached_signature:
            cmd.append(detached_signature)
        cmd.append(signed_file)

        output = subprocess.run(cmd, input=None, timeout=None, check=False,
                                universal_newlines=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

        logging.info(output.stdout)

        goodsig = re.search('''^\[GNUPG:\] GOODSIG''', output.stdout, re.MULTILINE)
        validsig = re.search('''^\[GNUPG:\] VALIDSIG''', output.stdout, re.MULTILINE)

        if goodsig and validsig:
            logging.info('Signature check ok!')
        else:
            if detached_signature:
                release_file_url = self._get_release_file_url('Release')
            else:
                release_file_url = self._get_release_file_url('InRelease')

            if output.stderr:
                raise FatalError(("Signature check for '{}' failed with error message '{}'!"
                                  ).format(release_file_url, output.stderr))
            else:
                raise FatalError("Signature check for '{}' failed!".format(release_file_url))

    def _verify_checksum(self, data, item):
        all_algorithms = []
        for algorithm in self._checksum_algorithms:
            checksum = item.get(algorithm, None)
            all_algorithms.append(algorithm)
            if not checksum:
                checksum = item.get(algorithm.lower(), None)
                all_algorithms.append(algorithm.lower())

            if checksum:
                h = hashlib.new(algorithm.lower())
                h.update(data)
                if h.hexdigest() != checksum:
                    raise FatalError(("Checksum mismatch on repository item '\n{}' downloaded from '{}'."
                                      ).format(item, self._source.uri))
                else:
                    return

        raise FatalError(("No checksum ({}) found for '\n{}' downloaded from '{}'."
                          ).format(' or '.join(a for a in all_algorithms),
                                   item, self._source.uri))

    def _find_package_in_package_files(self, package_name, package_files):
        downloaded_package_prefix = []
        for package_file in package_files:
            match = re.match('^(.*)Packages\.*([a-z2]{1,3})$', package_file['name'])
            if not match or not len(match.groups()) <= 2:
                raise FatalError('Error parsing package name string {}.'.format(package_file['name']))

            prefix = match.group(1).replace('/', '_')

            if prefix in downloaded_package_prefix:
                continue

            package_url = '{}/dists/{}/{}'.format(self._source.uri, self._source.dist, package_file['name'])
            package_file_data = self._try_fetch_archive_element(package_url)
            if package_file_data:
                self._verify_checksum(package_file_data, package_file)
                downloaded_package_prefix.append(prefix)
                decompressed_package_data = decompress(package_file_data)

                with tempfile.SpooledTemporaryFile() as f:
                    f.write(decompressed_package_data)
                    f.seek(0)
                    for section in debian.deb822.Packages.iter_paragraphs(f):
                        if section['Package'] == package_name:
                            return section

        return None

    def _download_package(self, package, dest):
        full_name = package['Filename']
        package_name = re.match('.*/(.*deb)', full_name).group(1)
        deb_url = '{}/{}'.format(self._source.uri, full_name)
        package_data = self._fetch_archive_element(deb_url)
        self._verify_checksum(package_data, package)
        package_file = os.path.join(dest, package_name)
        with open(package_file, mode='wb') as f:
            f.write(package_data)
        return package_file

    def download(self, package_name=None, dest='/tmp'):
        if not package_name:
            raise FatalError('Missing argument package_name!')

        with tempfile.TemporaryDirectory() as tempdir:
            inrelease_data = self._try_fetch_archive_element(self._get_release_file_url('InRelease'))
            release_file = os.path.join(tempdir, 'InRelease')
            signature_file = None

            if inrelease_data:
                with open(release_file, mode='wb') as f:
                    f.write(inrelease_data)
            else:
                release_file = os.path.join(tempdir, 'Release')
                signature_file = os.path.join(tempdir, 'Release.gpg')

                release_data = self._fetch_archive_element(self._get_release_file_url('Release'))
                with open(release_file, mode='wb') as f:
                    f.write(release_data)
                if self._repository_key:
                    signature_data = self._fetch_archive_element(self._get_release_file_url('Release.gpg'))
                    with open(signature_file, mode='wb') as f:
                        f.write(signature_data)

            if self._repository_key:
                key_data = fetch_repository_key(self._repository_key)
                keyring = build_keyring(tempdir, 'trusted.gpg', key_data)
                self._verify_signature(tempdir, keyring, release_file, signature_file)
            else:
                logging.warning('Warning: Package {} will get downloaded without verification!'.format(package_name))

            package_files = self._parse_release_file(release_file)
            requested_package = self._find_package_in_package_files(package_name, package_files)
            if not requested_package:
                raise FatalError(("Package '{}' not found in repository '{}'."
                                  ).format(package_name, self._source.uri))
            else:
                result = self._download_package(requested_package, dest)
                return result
