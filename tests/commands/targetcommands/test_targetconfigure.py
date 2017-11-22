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

from edi.commands.targetcommands.targetconfigure import Configure
from tests.libtesting.helpers import get_command, suppress_chown_during_debuild
from tests.libtesting.contextmanagers.workspace import workspace
from tests.libtesting.helpers import get_random_string, get_project_root
from edi.lib.shellhelpers import run
import os
import subprocess
from edi.lib import mockablerun
import edi


def test_target_configure(config_files, monkeypatch, capsys):
    def fakerun(*popenargs, **kwargs):
        if get_command(popenargs) == "ansible-playbook":
            return subprocess.CompletedProcess("fakerun", 0, '')
        else:
            print('Passthrough: {}'.format(get_command(popenargs)))
            return subprocess.run(*popenargs, **kwargs)

    monkeypatch.setattr(mockablerun, 'run_mockable', fakerun)

    suppress_chown_during_debuild(monkeypatch)

    with workspace():
        edi_exec = os.path.join(get_project_root(), 'bin', 'edi')
        project_name = 'pytest-{}'.format(get_random_string(6))
        config_command = [edi_exec, 'config', 'init', project_name, 'debian-jessie-amd64']
        run(config_command)  # run as non root

        parser = edi._setup_command_line_interface()
        cli_args = parser.parse_args(['target', 'configure', 'remote-target', '{}-develop.yml'.format(project_name)])

        Configure().run_cli(cli_args)

        out, err = capsys.readouterr()
        print(out)
        assert not err
