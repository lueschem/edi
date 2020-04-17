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
from edi.commands.qemucommands.fetch import Fetch
from edi.commands.documentationcommands.render import Render
from edi.commands.targetcommands.targetconfigure import Configure as TargetConfigure
from edi.lib.shellhelpers import mockablerun
from tests.libtesting.contextmanagers.mocked_executable import mocked_executable, mocked_lxd_version_check


@pytest.mark.parametrize(("command, command_args, has_templates, "
                          "has_profiles, has_playbooks, has_postprocessing_commands, check_errors"), [
    (Bootstrap, ['image', 'bootstrap', '--plugins'], False, False, False, False, True),
    (Prepare, ['lxc', 'prepare', '--plugins'], True, False, False, False, True),
    (Create, ['image', 'create', '--plugins'], True, True, True, True, True),
    (Export, ['lxc', 'export', '--plugins'], True, True, True, False, True),
    (Import, ['lxc', 'import', '--plugins'], True, False, False, False, True),
    (Launch, ['lxc', 'launch', '--plugins', 'cname'], True, True, False, False, True),
    (Configure, ['lxc', 'configure', '--plugins', 'cname'], True, True, True, False, True),
    (Profile, ['lxc', 'profile', '--plugins'], False, True, False, False, True),
    (Publish, ['lxc', 'publish', '--plugins'], True, True, True, False, True),
    (Stop, ['lxc', 'stop', '--plugins'], True, True, True, False, True),
    (Fetch, ['qemu', 'fetch', '--plugins'], False, False, False, False, True),
    (TargetConfigure, ['target', 'configure', '--plugins', '1.2.3.4'], False, False, True, False, True),
    (Render, ['documentation', 'render', '--plugins', './', './'], False, False, False, False, False),
])
def test_plugins(monkeypatch, config_files, capsys, command, command_args, has_templates,
                 has_profiles, has_playbooks, has_postprocessing_commands, check_errors):
    with mocked_executable('lxc'):
        with mocked_lxd_version_check():
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

            if check_errors:
                assert err == ''
            result = yaml.safe_load(out)

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
                assert base_system.get('dictionary').get('edi_project_directory') == os.path.dirname(config_files)
                assert base_system.get('dictionary').get("param1") == "keep"
                assert base_system.get('dictionary').get("param2") == "overwritten"
                assert base_system.get('dictionary').get("param3") == "customized"
            else:
                assert not result.get('playbooks')

            if has_postprocessing_commands:
                assert result.get('postprocessing_commands')
            else:
                assert not result.get('postprocessing_commands')
