# -*- coding: utf-8 -*-
# Copyright (C) 2018 Matthias Luescher
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
import logging
import subprocess
from edi.lib.helpers import which
from edi.lib.shellhelpers import run, get_environment_variable


def get_proxy_setup(protocol):
    protocol_to_env = {
        'http': 'http_proxy',
        'https': 'https_proxy',
        'ftp': 'ftp_proxy',
        'socks': 'all_proxy',
        'no': 'no_proxy'
    }
    assert protocol in protocol_to_env.keys()

    result = get_environment_variable(protocol_to_env[protocol], default='')

    return result


def has_gsettings():
    return which('gsettings') is not None


def get_gsettings_value(schema, key, default=None):
    cmd = ['gsettings', 'get', schema, key]
    keep_sudo = os.getuid() == 0
    result = run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, sudo=keep_sudo)
    if result.returncode == 0:
        return result.stdout.strip('\n').strip("'")
    else:
        logging.debug('''The command '{}' failed: {}'''.format(cmd, result.stderr))
        return default
