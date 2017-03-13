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

from edi.lib.configurationparser import ConfigurationParser
from edi.lib.playbookrunner import PlaybookRunner
from tests.libtesting.fixtures.configfiles import config_files
from edi.lib import mockablerun
import shutil
import subprocess
from codecs import open
import yaml


def get_parameter(command, option):
    option_index = command.index(option)
    return command[option_index + 1]


def verify_inventory(file):
    with open(file, encoding='utf-8') as f:
        assert 'fake-container' in f.read()


def verify_extra_vars(file):
    print(file)
    with open(file, encoding='utf-8') as f:
        extra_vars = yaml.load(f)
        assert extra_vars['edi_config_management_user_name'] == 'edicfgmgmt'
        mountpoints = extra_vars['edi_shared_folder_mountpoints']
        assert len(mountpoints) == 2
        assert mountpoints[0] == '/foo/bar/target_mountpoint'


def test_lxd_connection(config_files, monkeypatch):
    def fake_ansible_playbook_run(*popenargs, **kwargs):
        command = popenargs[0]
        if command[0] == 'ansible-playbook':
            assert 'lxd' == get_parameter(command, '--connection')
            verify_inventory(get_parameter(command, '--inventory'))
            verify_extra_vars(get_parameter(command, '--extra-vars').lstrip('@'))
            # TODO: verify --user for ssh connection
            return subprocess.CompletedProcess("fakerun", 0, '')
        else:
            return subprocess.run(*popenargs, **kwargs)

    monkeypatch.setattr(mockablerun, 'run_mockable', fake_ansible_playbook_run)

    def fakechown(*_):
        pass

    monkeypatch.setattr(shutil, 'chown', fakechown)

    with open(config_files, "r") as main_file:
        parser = ConfigurationParser(main_file)
        runner = PlaybookRunner(parser, "fake-container", "lxd")

        runner.run_all()
