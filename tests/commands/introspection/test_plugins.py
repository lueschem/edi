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
from edi.commands.lxccommands.export import Export
from edi.commands.lxccommands.importcmd import Import
from edi.commands.lxccommands.launch import Launch
from edi.commands.lxccommands.lxcconfigure import Configure
from edi.commands.lxccommands.profile import Profile
from edi.commands.lxccommands.publish import Publish
from edi.commands.lxccommands.stop import Stop
from edi.commands.qemucommands.fetch import Fetch
from edi.commands.targetcommands.targetconfigure import Configure as TargetConfigure
import edi
import yaml
import os
import pytest


@pytest.mark.parametrize("command, command_args, has_templates, has_profiles, has_playbooks", [
    (Bootstrap, ['image', 'bootstrap', '--plugins'], False, False, False),
    (Lxc, ['image', 'lxc', '--plugins'], True, False, False),
    (Export, ['lxc', 'export', '--plugins'], True, True, True),
    (Import, ['lxc', 'import', '--plugins'], True, False, False),
    (Launch, ['lxc', 'launch', '--plugins', 'cname'], True, True, False),
    (Configure, ['lxc', 'configure', '--plugins', 'cname'], True, True, True),
    (Profile, ['lxc', 'profile', '--plugins'], False, True, False),
    (Publish, ['lxc', 'publish', '--plugins'], True, True, True),
    (Stop, ['lxc', 'stop', '--plugins'], True, True, True),
    (Fetch, ['qemu', 'fetch', '--plugins'], False, False, False),
    (TargetConfigure, ['target', 'configure', '--plugins', '1.2.3.4'], False, False, True),
])
def test_plugins(config_files, capsys, command, command_args, has_templates, has_profiles, has_playbooks):
    # TODO: apply to all introspection aware commands
    parser = edi._setup_command_line_interface()
    command_args.append(config_files)
    cli_args = parser.parse_args(command_args)

    command().run_cli(cli_args)
    out, err = capsys.readouterr()

    assert err == ''
    result = yaml.load(out)

    if has_templates:
        assert result.get('lxc_templates')
    else:
        assert not result.get('lxc_templates')

    if has_profiles:
        assert result.get('lxc_profiles')
    else:
        assert not result.get('lxc_profiles')

    if has_playbooks:
        assert len(result.get('playbooks')) == 3
        base_system = result.get('playbooks')[0].get('10_base_system')
        assert 'plugins/playbooks/foo.yml' in base_system.get('path')
        assert base_system.get('dictionary').get('kernel_package') == 'linux-image-amd64-rt'
        assert base_system.get('dictionary').get('edi_config_directory') == os.path.dirname(config_files)
    else:
        assert not result.get('playbooks')
