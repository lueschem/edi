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
import gnupg
import os
from edi.lib.helpers import FatalError


def fetch_repository_key(key_url):
    if key_url:
        key_req = requests.get(key_url)
        if key_req.status_code != 200:
            raise FatalError(("Unable to fetch repository key '{0}'"
                              ).format(key_url))

        return key_req.text
    else:
        return None


def build_keyring(tempdir, keyring_file, key_data):
    if key_data:
        keyring_file_path = os.path.join(tempdir, keyring_file)
        gpg = gnupg.GPG(gnupghome=tempdir, keyring=keyring_file_path)
        gpg.encoding = 'utf-8'
        gpg.import_keys(key_data)
        return keyring_file_path
    else:
        return None
