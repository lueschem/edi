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


from tests.libtesting.optins import requires_lxc, requires_ansible, requires_debootstrap, requires_sudo
from tests.libtesting.contextmanagers.workspace import workspace
import os
from tests.libtesting.helpers import get_random_string, get_project_root
from edi.lib.shellhelpers import run
from edi.commands.lxccommands.lxcconfigure import Configure
from edi.commands.clean import Clean
import edi
import subprocess


@requires_lxc
@requires_ansible
@requires_debootstrap
@requires_sudo
def test_build_stretch_container(capsys):
    print(os.getcwd())
    with workspace() as workspace_dir:
        edi_exec = os.path.join(get_project_root(), 'bin', 'edi')
        project_name = 'pytest-{}'.format(get_random_string(6))
        config_command = [edi_exec, 'config', 'init', project_name, 'debian-stretch-amd64']
        run(config_command)

        container_name = 'pytest-{}'.format(get_random_string(6))
        parser = edi._setup_command_line_interface()
        cli_args = parser.parse_args(['-v', 'lxc', 'configure', container_name, '{}-develop.yml'.format(project_name)])

        Configure().run_cli(cli_args)
        out, err = capsys.readouterr()
        print(out)
        assert not err

        images = [
            '{}-develop_edicommand_image_bootstrap.tar.gz'.format(project_name),
            '{}-develop_edicommand_image_lxc.tar.gz'.format(project_name)
        ]
        for image in images:
            assert os.path.isfile(image)

        lxc_image_list_cmd = ['lxc', 'image', 'list']
        result = run(lxc_image_list_cmd, stdout=subprocess.PIPE)
        assert project_name in result.stdout

        parser = edi._setup_command_line_interface()
        cli_args = parser.parse_args(['-v', 'clean', '{}-develop.yml'.format(project_name)])
        Clean().run_cli(cli_args)

        for image in images:
            assert not os.path.isfile(image)

        result = run(lxc_image_list_cmd, stdout=subprocess.PIPE)
        assert project_name not in result.stdout

        verification_command = ['lxc', 'exec', container_name, '--', 'cat', '/etc/os-release']
        result = run(verification_command, stdout=subprocess.PIPE)
        assert '''VERSION_ID="9"''' in result.stdout
        assert 'ID=debian' in result.stdout

        stop_command = ['lxc', 'stop', container_name]
        run(stop_command)

        delete_command = ['lxc', 'delete', container_name]
        run(delete_command)
