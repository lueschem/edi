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

import os
import random
import string
import subprocess
import re
from edi.lib.shellhelpers import run, get_user_home_directory
import edi.lib.helpers


def get_user_ssh_pub_keys():
    """
    Search for all ssh public keys of the current user (not the root user when called with sudo).
    :return: A list of ssh public keys. The list will be empty if the tool ssh is not installed.
    """
    if not edi.lib.helpers.which('ssh'):
        return []

    random_host = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    cmd = ['ssh', '-G', random_host]
    ssh_config = run(cmd, stdout=subprocess.PIPE).stdout
    user_home = get_user_home_directory(edi.lib.helpers.get_user())
    identity_files = re.findall(r'^identityfile (.*)$', ssh_config, flags=re.MULTILINE)
    ssh_pub_keys = []
    for file in identity_files:
        expanded_file = re.sub(r'^~', user_home, file)
        expanded_pub_file = '{}.pub'.format(expanded_file)
        if os.path.isfile(expanded_file) and os.path.isfile(expanded_pub_file):
            ssh_pub_keys.append(expanded_pub_file)

    return ssh_pub_keys
