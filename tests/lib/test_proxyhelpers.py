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
import edi.lib.helpers
from tests.libtesting.helpers import get_command, get_command_parameter
from edi.lib.proxyhelpers import get_gsettings_value
from edi.lib import mockablerun


def with_gsettings(monkeypatch):
    def fake_which_gsettings(*_):
        return os.path.join(os.sep, 'usr', 'bin', 'gsettings')

    monkeypatch.setattr(edi.lib.helpers, 'which', fake_which_gsettings)


def without_gsettings(monkeypatch):
    def fake_which_gsettings(*_):
        return None

    monkeypatch.setattr(edi.lib.helpers, 'which', fake_which_gsettings)


def intercept_gsettings(monkeypatch, mode):
    def intercept_command_run(*popenargs, **kwargs):
        if get_command(popenargs) == 'gsettings':
            schema = get_command_parameter(popenargs, 'get')
            assert schema.startswith('org.gnome.system.proxy')
            key = get_command_parameter(popenargs, schema)
            return_value = 0
            if key == 'mode':
                result = mode
            elif key == 'ignore-hosts':
                result = '''['localhost', '127.0.0.0/8', '::1']'''
            elif key == 'host':
                result = 'foo:bar@example.com'
            elif key == 'port':
                result = '3128'
            else:
                return_value = 1
                result = ''

            return subprocess.CompletedProcess("fakerun", return_value, stdout=result)
        else:
            return subprocess.run(*popenargs, **kwargs)

    monkeypatch.setattr(mockablerun, 'run_mockable', intercept_command_run)


def test_get_gsettings_value(monkeypatch):
    intercept_gsettings(monkeypatch, 'manual')
    assert get_gsettings_value('org.gnome.system.proxy', 'mode') == 'manual'
    assert get_gsettings_value('org.gnome.system.proxy', 'invalid-key', default='bingo') == 'bingo'
