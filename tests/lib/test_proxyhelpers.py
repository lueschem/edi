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
import subprocess
from contextlib import contextmanager
import edi.lib.helpers
from tests.libtesting.helpers import get_command, get_command_parameter, get_sub_command
from edi.lib.proxyhelpers import get_gsettings_value, ProxySetup
from edi.lib import mockablerun


@contextmanager
def clear_proxy_setup_cache():
    try:
        ProxySetup(clear_cache=True)
        yield
    finally:
        ProxySetup(clear_cache=True)


def with_gsettings(monkeypatch):
    def fake_which_gsettings(*_):
        return os.path.join(os.sep, 'usr', 'bin', 'gsettings')

    monkeypatch.setattr(edi.lib.helpers, 'which', fake_which_gsettings)


def without_gsettings(monkeypatch):
    def fake_which_gsettings(*_):
        return None

    monkeypatch.setattr(edi.lib.helpers, 'which', fake_which_gsettings)


def intercept_proxy_environment(monkeypatch, gsettings_proxy_mode, gsettings_no_proxy,
                                gsettings_proxy_port, env_value_proxy, env_value_no_proxy, env_value_proxy_upper,
                                env_value_no_proxy_upper):
    def intercept_command_run(*popenargs, **kwargs):
        if get_command(popenargs) == 'gsettings':
            schema = get_command_parameter(popenargs, 'get')
            assert schema.startswith('org.gnome.system.proxy')
            key = get_command_parameter(popenargs, schema)
            return_value = 0
            if key == 'mode':
                result = gsettings_proxy_mode
            elif key == 'ignore-hosts':
                result = gsettings_no_proxy
            elif key == 'host':
                result = 'foo:bar@example.com'
            elif key == 'port':
                result = gsettings_proxy_port
            else:
                return_value = 1
                result = ''

            return subprocess.CompletedProcess("fakerun", return_value, stdout=result)
        elif get_command(popenargs) == 'printenv':
            env_var = get_sub_command(popenargs)
            if env_var == 'no_proxy' and env_value_no_proxy:
                return subprocess.CompletedProcess("fakerun", 0, stdout=env_value_no_proxy)
            elif env_var != 'no_proxy' and env_var.endswith('_proxy') and env_value_proxy:
                return subprocess.CompletedProcess("fakerun", 0, stdout=env_value_proxy)
            elif env_var == 'NO_PROXY' and env_value_no_proxy_upper:
                return subprocess.CompletedProcess("fakerun", 0, stdout=env_value_no_proxy_upper)
            elif env_var != 'NO_PROXY' and env_var.endswith('_PROXY') and env_value_proxy_upper:
                return subprocess.CompletedProcess("fakerun", 0, stdout=env_value_proxy_upper)
            else:
                return subprocess.CompletedProcess("fakerun", 1, stdout='')
        else:
            return subprocess.run(*popenargs, **kwargs)

    monkeypatch.setattr(mockablerun, 'run_mockable', intercept_command_run)


def test_get_gsettings_value(monkeypatch):
    intercept_proxy_environment(monkeypatch, 'manual',
                                '''['localhost', '127.0.0.0/8', '::1']''', '3128',
                                '', '', '', '')
    assert get_gsettings_value('org.gnome.system.proxy', 'mode') == 'manual'
    assert get_gsettings_value('org.gnome.system.proxy', 'invalid-key', default='bingo') == 'bingo'


def test_proxy_setup_no_gsettings_no_env(monkeypatch):
    without_gsettings(monkeypatch)
    intercept_proxy_environment(monkeypatch, 'manual',
                                '''['localhost', '127.0.0.0/8', '::1']''', '3128',
                                '', '', '', '')
    with clear_proxy_setup_cache():
        proxy_setup = ProxySetup()
        assert proxy_setup.get('no_proxy', default='') == ''
        assert proxy_setup.get('http_proxy', default='') == ''
        assert proxy_setup.get('https_proxy', default='') == ''
        assert proxy_setup.get('ftp_proxy', default='') == ''
        assert proxy_setup.get('all_proxy', default='') == ''


def test_proxy_setup_gsettings_env(monkeypatch):
    with_gsettings(monkeypatch)
    intercept_proxy_environment(monkeypatch, 'manual',
                                '''['localhost', '127.0.0.0/8', '::1']''', '3128',
                                'protocol://proxy-xy', '1.2.3.4,5.6.7.8,example.com',
                                '', '')
    with clear_proxy_setup_cache():
        proxy_setup = ProxySetup()
        assert proxy_setup.get('no_proxy', default='') == '1.2.3.4,5.6.7.8,example.com'
        assert proxy_setup.get('http_proxy', default='') == 'protocol://proxy-xy'
        assert proxy_setup.get('https_proxy', default='') == 'protocol://proxy-xy'
        assert proxy_setup.get('ftp_proxy', default='') == 'protocol://proxy-xy'
        assert proxy_setup.get('all_proxy', default='') == 'protocol://proxy-xy'


def test_proxy_setup_gsettings_env_upper(monkeypatch):
    with_gsettings(monkeypatch)
    intercept_proxy_environment(monkeypatch, 'manual',
                                '''['localhost', '127.0.0.0/8', '::1']''', '3128',
                                '', '',
                                'protocol://proxy-xy',
                                '1.2.3.4,5.6.7.8,example.com')
    with clear_proxy_setup_cache():
        proxy_setup = ProxySetup()
        assert proxy_setup.get('no_proxy', default='') == '1.2.3.4,5.6.7.8,example.com'
        assert proxy_setup.get('http_proxy', default='') == 'protocol://proxy-xy'
        assert proxy_setup.get('https_proxy', default='') == 'protocol://proxy-xy'
        assert proxy_setup.get('ftp_proxy', default='') == 'protocol://proxy-xy'
        assert proxy_setup.get('all_proxy', default='') == 'protocol://proxy-xy'


def test_proxy_setup_gsettings_no_env(monkeypatch):
    with_gsettings(monkeypatch)
    intercept_proxy_environment(monkeypatch, 'manual',
                                '''['localhost', '127.0.0.0/8', '::1']''', '3128',
                                '', '', '', '')
    with clear_proxy_setup_cache():
        proxy_setup = ProxySetup()
        assert proxy_setup.get('no_proxy', default='') == 'localhost,127.0.0.0/8,::1'
        assert proxy_setup.get('http_proxy', default='') == 'http://foo:bar@example.com:3128/'
        assert proxy_setup.get('https_proxy', default='') == 'http://foo:bar@example.com:3128/'
        assert proxy_setup.get('ftp_proxy', default='') == 'http://foo:bar@example.com:3128/'
        assert proxy_setup.get('all_proxy', default='') == 'socks://foo:bar@example.com:3128/'


def test_proxy_setup_gsettings_auto_no_env(monkeypatch):
    with_gsettings(monkeypatch)
    intercept_proxy_environment(monkeypatch, 'auto',
                                '''['localhost', '127.0.0.0/8', '::1']''', '3128',
                                '', '', '', '')

    with clear_proxy_setup_cache():
        proxy_setup = ProxySetup()
        assert proxy_setup.get('no_proxy', default='') == ''
        assert proxy_setup.get('http_proxy', default='') == ''
        assert proxy_setup.get('https_proxy', default='') == ''
        assert proxy_setup.get('ftp_proxy', default='') == ''
        assert proxy_setup.get('all_proxy', default='') == ''


def test_proxy_setup_gsettings_none_no_env(monkeypatch):
    with_gsettings(monkeypatch)
    intercept_proxy_environment(monkeypatch, 'none',
                                '''['localhost', '127.0.0.0/8', '::1']''', '3128',
                                '', '', '', '')

    with clear_proxy_setup_cache():
        proxy_setup = ProxySetup()
        assert proxy_setup.get('no_proxy', default='') == ''
        assert proxy_setup.get('http_proxy', default='') == ''
        assert proxy_setup.get('https_proxy', default='') == ''
        assert proxy_setup.get('ftp_proxy', default='') == ''
        assert proxy_setup.get('all_proxy', default='') == ''


def test_proxy_setup_gsettings_manual_edge_case_no_env(monkeypatch):
    with_gsettings(monkeypatch)
    intercept_proxy_environment(monkeypatch, 'manual',
                                '@as []', '0',
                                '', '', '', '')

    with clear_proxy_setup_cache():
        proxy_setup = ProxySetup()
        assert proxy_setup.get('no_proxy') is None
        assert proxy_setup.get('http_proxy') is None
        assert proxy_setup.get('https_proxy') is None
        assert proxy_setup.get('ftp_proxy') is None
        assert proxy_setup.get('all_proxy') is None


def test_get_requests_proxy_dict_with_proxy(monkeypatch):
    with_gsettings(monkeypatch)
    intercept_proxy_environment(monkeypatch, 'manual',
                                '''['localhost', '127.0.0.0/8', '::1']''', '3128',
                                '', '', '', '')
    with clear_proxy_setup_cache():
        proxy_dict = ProxySetup().get_requests_dict()
        assert proxy_dict.get('http') == 'http://foo:bar@example.com:3128/'
        assert proxy_dict.get('https') == 'http://foo:bar@example.com:3128/'
        assert proxy_dict.get('no_proxy') == 'localhost,127.0.0.0/8,::1'

        # test cache
        proxy_dict = ProxySetup().get_requests_dict()
        assert proxy_dict.get('http') == 'http://foo:bar@example.com:3128/'


def test_get_requests_proxy_dict_without_proxy(monkeypatch):
    with_gsettings(monkeypatch)
    intercept_proxy_environment(monkeypatch, 'manual',
                                '', '', '', '',
                                '', '')

    with clear_proxy_setup_cache():
        proxy_dict = ProxySetup().get_requests_dict()
        assert proxy_dict.get('http') is None
        assert proxy_dict.get('https') is None
        assert proxy_dict.get('no_proxy') is None


def test_get_environment_with_proxy(monkeypatch):
    with_gsettings(monkeypatch)
    intercept_proxy_environment(monkeypatch, 'manual',
                                '''['localhost', '127.0.0.0/8', '::1']''', '3128',
                                '', '', '', '')

    with clear_proxy_setup_cache():
        env = ProxySetup().get_environment()
        assert env.get('http_proxy') == 'http://foo:bar@example.com:3128/'
        assert env.get('https_proxy') == 'http://foo:bar@example.com:3128/'
        assert env.get('ftp_proxy') == 'http://foo:bar@example.com:3128/'
        assert env.get('all_proxy') == 'socks://foo:bar@example.com:3128/'
        assert env.get('no_proxy') == 'localhost,127.0.0.0/8,::1'


def test_get_environment_without_proxy(monkeypatch):
    with_gsettings(monkeypatch)
    intercept_proxy_environment(monkeypatch, 'manual',
                                '', '', '', '',
                                '', '')

    with clear_proxy_setup_cache():
        env = ProxySetup().get_environment()
        assert env.get('http_proxy') == ''
        assert env.get('https_proxy') == ''
        assert env.get('ftp_proxy') == ''
        assert env.get('all_proxy') == ''
        assert env.get('no_proxy') == ''
