# -*- coding: utf-8 -*-
# Copyright (C) 2016 Matthias Luescher
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
from aptsources.sourceslist import SourceEntry
from edi.lib.helpers import print_error_and_exit, chown_to_user
from edi.lib.shellhelpers import run
import logging


def fetch_archive_element(url, tempdir, prefix=''):
    return _fetch_archive_element(url, tempdir, prefix=prefix, check=True)


def try_fetch_archive_element(url, tempdir, prefix=''):
    return _fetch_archive_element(url, tempdir, prefix=prefix, check=False)


def _fetch_archive_element(url, tempdir, prefix='', check=True):
    req = requests.get(url)
    if req.status_code != 200:
        if check:
            print_error_and_exit(("Unable to fetch archive element '{0}'."
                                  ).format(url))
        else:
            return None

    file_path = os.path.join(tempdir, '{0}{1}'.format(prefix, url.rsplit('/', 1)[-1]))

    with open(file_path, mode='w+b') as result_file:
        result_file.write(req.content)

    return file_path


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


def runtest():
    repository = 'deb http://ftp.ch.debian.org/debian/ jessie main'
    repository_key = 'https://ftp-master.debian.org/keys/archive-key-8.asc'
    workdir = os.path.join(os.sep, 'home', 'lueschem', 'workspace', 'edi')
    source = SourceEntry(repository)

    with tempfile.TemporaryDirectory(dir=workdir) as tempdir:
        chown_to_user(tempdir)
        base_url = '{}/dists/{}'.format(source.uri, source.dist)
        release_file = try_fetch_archive_element('{}/InRelease'.format(base_url), tempdir)
        signature_file = None

        if not release_file:
            release_file = fetch_archive_element('{}/Release'.format(base_url), tempdir)
            signature_file = fetch_archive_element('{}/Release.gpg'.format(base_url), tempdir)

        if repository_key:
            from edi.lib.keyhelpers import fetch_repository_key, build_keyring
            key_data = fetch_repository_key(repository_key)
            keyring = build_keyring(tempdir, 'trusted.gpg', key_data)
            if not verify_signature(tempdir, keyring, release_file, signature_file):
                print_error_and_exit('Signature check failed!')

# gpg --homedir /home/lueschem/workspace/edi --weak-digest SHA1 --weak-digest RIPEMD160 --no-default-keyring --status-fd 1 --keyring /home/lueschem/workspace/edi/trusted.gpg --verify /home/lueschem/workspace/edi/Release.gpg /home/lueschem/workspace/edi/Release
