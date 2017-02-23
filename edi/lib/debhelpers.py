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
from aptsources.sourceslist import SourceEntry
from edi.lib.helpers import print_error_and_exit, chown_to_user
from edi.lib.shellhelpers import run
from edi.lib.archivehelpers import decompress
import logging


def fetch_archive_element(url):
    return _fetch_archive_element(url, check=True)


def try_fetch_archive_element(url):
    return _fetch_archive_element(url, check=False)


def _fetch_archive_element(url, check=True):
    req = requests.get(url)
    if req.status_code != 200:
        if check:
            print_error_and_exit(("Unable to fetch archive element '{0}'."
                                  ).format(url))
        else:
            return None

    return req.content


def _parse_release_file(release_file, architectures, components, compressions):
    with open(release_file) as file:
        main_content = next(debian.deb822.Release.iter_paragraphs(file))
        section = main_content.get('SHA512')
        if not section:
            section = main_content.get('SHA256')

        if not section:
            # TODO: Improve hints within error handling.
            print_error_and_exit('Neither SHA512 nor SHA256 section found in release file.')

        packages_filter = ['{}/binary-{}/Packages.{}'.format(component, architecture, compression)
                           for component in components
                           for architecture in architectures
                           for compression in compressions]

        package_files = [ element for element in section if element.get('name') in packages_filter ]

        return package_files


def verify_signature(homedir, keyring, signed_file, detached_signature=None):
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

    output = run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)

    logging.info(output.stdout)

    goodsig = re.search('''^\[GNUPG:\] GOODSIG''', output.stdout, re.MULTILINE)
    validsig =  re.search('''^\[GNUPG:\] VALIDSIG''', output.stdout, re.MULTILINE)

    if goodsig and validsig:
        logging.info('Signature check ok!')
        return True
    else:
        logging.info('Signature check failed!')
        return False


def _verify_checksum(data, item, checksum_algorithms):
    for algorithm in checksum_algorithms:
        checksum = item.get(algorithm, None)
        if checksum:
            h = hashlib.new(algorithm.lower())
            h.update(data)
            if h.hexdigest() != checksum:
                print_error_and_exit('Checksum mismatch on repository item.')
            else:
                return

    print_error_and_exit('No checksum found for {}.'.format(package_item['name']))


def _find_package_in_package_files(uri, distribution, package_name, package_files):
    downloaded_package_prefix = []
    for package_file in package_files:
        match = re.match('^(.*)Packages\.*([a-z2]{1,3})$', package_file['name'])
        if not match or not len(match.groups()) <= 2:
            print_error_and_exit('Error parsing package name string {}.'.format(package_file['name']))

        prefix = match.group(1).replace('/', '_')

        if prefix in downloaded_package_prefix:
            continue

        package_url = '{}/dists/{}/{}'.format(uri, distribution, package_file['name'])
        package_file_data = try_fetch_archive_element(package_url)
        if package_file_data:
            _verify_checksum(package_file_data, package_file, ['sha512', 'sha256'])
            downloaded_package_prefix.append(prefix)
            decompressed_package_data = decompress(package_file_data)

            with tempfile.SpooledTemporaryFile() as f:
                f.write(decompressed_package_data)
                f.seek(0)
                for section in debian.deb822.Packages.iter_paragraphs(f):
                    if section['Package'] == package_name:
                        return section

    return None


def _download_package(uri, package, directory):
    full_name = package['Filename']
    package_name = re.match('.*/(.*deb)', full_name).group(1)
    deb_url = '{}/{}'.format(uri, full_name)
    package_data = fetch_archive_element(deb_url)
    _verify_checksum(package_data, package, ['SHA512', 'SHA256'])
    package_file = os.path.join(directory, package_name)
    with open(package_file, mode='wb') as f:
        f.write(package_data)
    return package_file


def download_package(package_name='', repository='', repository_key=None,
                     architectures=[], workdir='/tmp'):
    source = SourceEntry(repository)

    with tempfile.TemporaryDirectory(dir=workdir) as tempdir:
        base_url = '{}/dists/{}'.format(source.uri, source.dist)
        inrelease_data = try_fetch_archive_element('{}/InRelease'.format(base_url))
        release_file = os.path.join(tempdir, 'InRelease')
        signature_file = None

        if inrelease_data:
            with open(release_file, mode='wb') as f:
                f.write(inrelease_data)
        else:
            release_file = os.path.join(tempdir, 'Release')
            signature_file = os.path.join(tempdir, 'Release.gpg')

            release_data = fetch_archive_element('{}/Release'.format(base_url))
            with open(release_file, mode='wb') as f:
                f.write(release_data)
            if repository_key:
                signature_data = fetch_archive_element('{}/Release.gpg'.format(base_url))
                with open(signature_file, mode='wb') as f:
                    f.write(signature_data)

        if repository_key:
            from edi.lib.keyhelpers import fetch_repository_key, build_keyring
            key_data = fetch_repository_key(repository_key)
            keyring = build_keyring(tempdir, 'trusted.gpg', key_data)
            if not verify_signature(tempdir, keyring, release_file, signature_file):
                print_error_and_exit('Signature check failed!')
        else:
            logging.warning('Warning: Package {} will get downloaded without verification!'.format(package_name))

        package_files = _parse_release_file(release_file, architectures, source.comps, ['gz', 'bz2', 'xz'])
        requested_package = _find_package_in_package_files(source.uri, source.dist, package_name, package_files)
        if not requested_package:
            print_error_and_exit('Package {} not found.'.format(package_name))
        else:
            result = _download_package(source.uri, requested_package, workdir)
            return result
