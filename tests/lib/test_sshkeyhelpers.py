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
import edi.lib.helpers
from edi.lib.sshkeyhelpers import get_user_ssh_pub_keys
from tests.libtesting.helpers import get_command, get_sub_command
from edi.lib import mockablerun
import subprocess


fake_config = """
cow moo
identitiyfile ~/bingo
identitiyfile ~/bongo
identitiyfile ~/baz
myidentitifile ~/bingo
dog bark
"""


def fake_ssh_environment(monkeypatch, tmpdir):
    def fake_which_ssh(*_):
        return os.path.join(os.sep, 'usr', 'bin', 'ssh')

    monkeypatch.setattr(edi.lib.helpers, 'which', fake_which_ssh)

    def intercept_command_run(*popenargs, **kwargs):
        if get_command(popenargs) == 'ssh' and get_sub_command(popenargs) == '-G':
            return subprocess.CompletedProcess("fakerun", 0, stdout=fake_config)
        elif get_command(popenargs) == "printenv" and get_sub_command(popenargs) == "HOME":
            return subprocess.CompletedProcess("fakerun", 0, stdout=str(tmpdir))
        else:
            return subprocess.run(*popenargs, **kwargs)

    monkeypatch.setattr(mockablerun, 'run_mockable', intercept_command_run)


def test_ssh_identity_files_no_ssh(monkeypatch):
    def fake_which_no_ssh(*_):
        return None

    monkeypatch.setattr(edi.lib.helpers, 'which', fake_which_no_ssh)

    assert get_user_ssh_pub_keys() == []


def test_ssh_identity_files(monkeypatch, tmpdir):
    fake_ssh_environment(monkeypatch, tmpdir)

    assert get_user_ssh_pub_keys() == []
