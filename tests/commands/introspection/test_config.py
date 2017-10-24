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

from edi.commands.imagecommands.bootstrap import Bootstrap
from edi.commands.imagecommands.imagelxc import Lxc
from edi.commands.imagecommands.create import Create
from edi.commands.lxccommands.export import Export
from edi.commands.lxccommands.importcmd import Import
from edi.commands.lxccommands.launch import Launch
from edi.commands.lxccommands.lxcconfigure import Configure
from edi.commands.lxccommands.profile import Profile
from edi.commands.lxccommands.publish import Publish
from edi.commands.lxccommands.stop import Stop
from edi.commands.qemucommands.fetch import Fetch
from edi.commands.targetcommands.targetconfigure import Configure as TargetConfigure
from edi.lib.shellhelpers import mockablerun
import edi
import yaml
import pytest
import subprocess


@pytest.mark.parametrize("command, command_args", [
    (Bootstrap, ['image', 'bootstrap', '--config']),
    (Lxc, ['image', 'lxc', '--config']),
    (Create, ['image', 'create', '--config']),
    (Export, ['lxc', 'export', '--config']),
    (Import, ['lxc', 'import', '--config']),
    (Launch, ['lxc', 'launch', '--config', 'cname']),
    (Configure, ['lxc', 'configure', '--config', 'cname']),
    (Profile, ['lxc', 'profile', '--config']),
    (Publish, ['lxc', 'publish', '--config']),
    (Stop, ['lxc', 'stop', '--config']),
    (Fetch, ['qemu', 'fetch', '--config']),
    (TargetConfigure, ['target', 'configure', '--config', '1.2.3.4']),
])
def test_config(monkeypatch, config_files, capsys, command, command_args):
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
    merged_config = yaml.load(out)
    assert merged_config.get('bootstrap').get('architecture') == 'i386'
