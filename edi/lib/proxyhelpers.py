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
import ast
import logging
import subprocess
from functools import partial

import edi.lib.helpers
from edi.lib.shellhelpers import run, get_environment_variable


def get_gsettings_value(schema, key, default=None):
    cmd = ['gsettings', 'get', schema, key]
    keep_sudo = os.getuid() == 0
    result = run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, sudo=keep_sudo)
    if result.returncode == 0:
        return result.stdout.strip('\n').strip("'")
    else:
        logging.debug('''The command '{}' failed: {}'''.format(cmd, result.stderr))
        return default


class ProxySetup:
    def __init__(self):
        self._has_gsettings = (edi.lib.helpers.which('gsettings') is not None)
        self._proxy_mode = None
        if self._has_gsettings:
            self._proxy_mode = get_gsettings_value('org.gnome.system.proxy', 'mode')
        self._warn_if_auto_mode = True
        self._env_to_getter = {
            'http_proxy': partial(self._get_value, 'http_proxy',
                                  partial(self._gsettings_get_proxy, 'org.gnome.system.proxy.http', 'http')),
            'https_proxy': partial(self._get_value, 'https_proxy',
                                   partial(self._gsettings_get_proxy, 'org.gnome.system.proxy.https', 'http')),
            'ftp_proxy': partial(self._get_value, 'ftp_proxy',
                                 partial(self._gsettings_get_proxy, 'org.gnome.system.proxy.ftp', 'http')),
            'all_proxy': partial(self._get_value, 'all_proxy',
                                 partial(self._gsettings_get_proxy, 'org.gnome.system.proxy.socks', 'socks')),
            'no_proxy': partial(self._get_value, 'no_proxy', self._gsettings_get_ignore_hosts),
        }

    def get(self, environment_variable):
        assert environment_variable in self._env_to_getter.keys()
        return self._env_to_getter[environment_variable]()

    def _get_value(self, environment_variable, gsettings_getter):
        env_value = get_environment_variable(environment_variable, default='')

        if env_value:
            logging.debug('''Retrieved '{}' from environment.'''.format(environment_variable))
            return env_value

        if not self._has_gsettings:
            return ''

        if self._proxy_mode == 'auto' and self._warn_if_auto_mode:
            self._warn_if_auto_mode = False
            logging.warning('Automatic proxy mode is not supported!')

        if self._proxy_mode != 'manual':
            return ''

        gsettings_value = gsettings_getter()
        if gsettings_value:
            logging.debug('''Retrieved '{}' from gsettings.'''.format(environment_variable))
            return gsettings_value
        else:
            return ''

    @staticmethod
    def _gsettings_get_proxy(schema, prefix):
        host = get_gsettings_value(schema, 'host')
        port = get_gsettings_value(schema, 'port')

        if host and port and port != '0':
            return '{}://{}:{}/'.format(prefix, host, port)
        else:
            return ''

    @staticmethod
    def _gsettings_get_ignore_hosts():
        no_proxy = get_gsettings_value('org.gnome.system.proxy', 'ignore-hosts')

        if no_proxy and no_proxy != '@as []':
            return ','.join(ast.literal_eval(no_proxy))
        else:
            return ''
