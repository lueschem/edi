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
import subprocess

import pytest
import yaml

import edi
from edi.commands.imagecommands.bootstrap import Bootstrap
from edi.commands.imagecommands.create import Create
from edi.commands.lxccommands.export import Export
from edi.commands.lxccommands.lxcprepare import Prepare
from edi.commands.lxccommands.importcmd import Import
from edi.commands.lxccommands.launch import Launch
from edi.commands.lxccommands.lxcconfigure import Configure
from edi.commands.lxccommands.profile import Profile
from edi.commands.lxccommands.publish import Publish
from edi.commands.lxccommands.stop import Stop
from edi.commands.targetcommands.targetconfigure import Configure as TargetConfigure
from edi.commands.projectcommands.prepare import Prepare as ProjectPrepare
from edi.commands.projectcommands.configure import Configure as ProjectConfigure
from edi.commands.projectcommands.make import Make
from edi.lib.shellhelpers import mockablerun


@pytest.mark.parametrize("command, command_args", [
    (Bootstrap, ['image', 'bootstrap', '--dictionary']),
    (Prepare, ['lxc', 'prepare', '--dictionary']),
    (Create, ['image', 'create', '--dictionary']),
    (Export, ['lxc', 'export', '--dictionary']),
    (Import, ['lxc', 'import', '--dictionary']),
    (Launch, ['lxc', 'launch', '--dictionary', 'cname']),
    (Configure, ['lxc', 'configure', '--dictionary', 'cname']),
    (Profile, ['lxc', 'profile', '--dictionary']),
    (Publish, ['lxc', 'publish', '--dictionary']),
    (Stop, ['lxc', 'stop', '--dictionary']),
    (TargetConfigure, ['target', 'configure', '--dictionary', '1.2.3.4']),
    (ProjectPrepare, ['project', 'prepare', '--dictionary']),
    (ProjectConfigure, ['project', 'configure', '--dictionary']),
    (Make, ['project', 'make', '--dictionary']),
])
def test_dictionary(monkeypatch, config_files, capsys, command, command_args):
    def fake_lxc_config_command(*popenargs, **kwargs):
        if 'images.compression_algorithm' in popenargs[0]:
            return subprocess.CompletedProcess("fakerun", 0, '')
        else:
            return subprocess.run(*popenargs, **kwargs)

    monkeypatch.setattr(mockablerun, 'run_mockable', fake_lxc_config_command)

    parser = edi._setup_command_line_interface()
    command_args.append(config_files)
    cli_args = parser.parse_args(command_args)

    command().run_cli(cli_args)
    out, err = capsys.readouterr()

    assert err == ''
    dictionary = yaml.safe_load(out)
    assert dictionary.get('edi_project_directory') == os.path.dirname(config_files)
    assert dictionary.get('edi_project_plugin_directory') == os.path.join(os.path.dirname(config_files), 'plugins')
