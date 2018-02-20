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
from codecs import open
from edi.lib.sshkeyhelpers import get_user_ssh_pub_keys
from tests.libtesting.helpers import get_command, get_sub_command
from edi.lib import mockablerun
import subprocess


fake_config = """
cow moo
identityfile ~/bingo
identityfile ~/bongo
identityfile ~/baz
myidentityfile ~/blabla
dog bark
"""


def create_file(tmpdir, file_name):
    file_path = os.path.join(str(tmpdir), file_name)
    with open(file_path, mode='w') as file:
        file.write(file_name)


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

    create_file(tmpdir, 'blabla')
    create_file(tmpdir, 'blabla.pub')

    assert get_user_ssh_pub_keys() == []

    create_file(tmpdir, 'bongo.pub')

    assert get_user_ssh_pub_keys() == []

    create_file(tmpdir, 'baz')

    assert get_user_ssh_pub_keys() == []

    create_file(tmpdir, 'baz.pub')

    pub_keys = get_user_ssh_pub_keys()

    assert len(pub_keys) == 1
    assert str(os.path.join(str(tmpdir), 'baz.pub')) in pub_keys

    create_file(tmpdir, 'bongo')

    pub_keys = get_user_ssh_pub_keys()

    assert len(pub_keys) == 2
    assert str(os.path.join(str(tmpdir), 'baz.pub')) in pub_keys
    assert str(os.path.join(str(tmpdir), 'bongo.pub')) in pub_keys
