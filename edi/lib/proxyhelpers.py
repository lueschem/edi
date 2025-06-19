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
    # On Ubuntu the following command will cause some output on stderr.
    # This could be avoided by running the command as root but with this attempt
    # we would fail to retrieve the correct gsettings values on Debian.
    result = run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode == 0:
        return result.stdout.strip('\n').strip("'")
    else:
        logging.debug('''The command '{}' failed: {}'''.format(cmd, result.stderr))
        return default


class ProxySetup:
    _cache = dict()
    _warn_if_auto_mode = True

    def __init__(self, clear_cache=False):
        if clear_cache:
            ProxySetup._cache = dict()
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

    def get(self, environment_variable, default=None):
        assert environment_variable in self._env_to_getter

        if environment_variable in ProxySetup._cache:
            result = ProxySetup._cache.get(environment_variable)
        else:
            result = self._env_to_getter[environment_variable]()
            ProxySetup._cache[environment_variable] = result

        if result:
            return result
        else:
            return default

    def get_requests_dict(self):
        proxy_dict = {
            'http': self.get('http_proxy', default=None),
            'https': self.get('https_proxy', default=None),
            'no_proxy': self.get('no_proxy', default=None),
        }
        return proxy_dict

    def get_environment(self):
        env_with_proxy = os.environ.copy()
        for item in self._env_to_getter.keys():
            env_with_proxy[item] = self.get(item, '')
        return env_with_proxy

    def _get_value(self, environment_variable, gsettings_getter):
        env_value = get_environment_variable(environment_variable, default='')

        if not env_value:
            env_value = get_environment_variable(environment_variable.upper(), default='')

        if env_value:
            logging.debug('''Retrieved '{}' from environment.'''.format(environment_variable))
            return env_value

        if not self._has_gsettings():
            return None

        if self._proxy_mode() == 'auto' and ProxySetup._warn_if_auto_mode:
            ProxySetup._warn_if_auto_mode = False
            logging.warning('Automatic proxy mode is not supported!')

        if self._proxy_mode() != 'manual':
            return None

        gsettings_value = gsettings_getter()
        if gsettings_value:
            logging.debug('''Retrieved '{}' from gsettings.'''.format(environment_variable))
            return gsettings_value
        else:
            return None

    @staticmethod
    def _gsettings_get_proxy(schema, prefix):
        host = get_gsettings_value(schema, 'host')
        port = get_gsettings_value(schema, 'port')

        if host and port and port != '0':
            return '{}://{}:{}/'.format(prefix, host, port)
        else:
            return None

    @staticmethod
    def _gsettings_get_ignore_hosts():
        no_proxy = get_gsettings_value('org.gnome.system.proxy', 'ignore-hosts')

        if no_proxy and no_proxy != '@as []':
            return ','.join(ast.literal_eval(no_proxy))
        else:
            return None

    @staticmethod
    def _has_gsettings():
        key = 'has-gsettings'
        if key not in ProxySetup._cache:
            result = (edi.lib.helpers.which('gsettings') is not None)
            ProxySetup._cache[key] = result

        return ProxySetup._cache.get(key)

    @staticmethod
    def _proxy_mode():
        key = 'gsettings-proxy-mode'
        if key not in ProxySetup._cache:
            result = get_gsettings_value('org.gnome.system.proxy', 'mode')
            ProxySetup._cache[key] = result

        return ProxySetup._cache.get(key)
