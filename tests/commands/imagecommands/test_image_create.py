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


import pytest
from tests.libtesting.contextmanagers.workspace import workspace
import os
from tests.libtesting.helpers import get_random_string, get_project_root, suppress_chown_during_debuild
from edi.lib.shellhelpers import run, get_debian_architecture
from edi.lib.lxchelpers import (get_server_image_compression_algorithm, lxc_exec,
                                get_file_extension_from_image_compression_algorithm)
from edi.commands.imagecommands.create import Create
from edi.lib.helpers import get_artifact_dir
import edi
import subprocess


@pytest.mark.requires_lxc
@pytest.mark.requires_ansible
@pytest.mark.requires_debootstrap
@pytest.mark.requires_sudo
def test_create_buster_image(capsys):
    print(os.getcwd())
    with workspace():
        edi_exec = os.path.join(get_project_root(), 'bin', 'edi')
        project_name = 'pytest-{}'.format(get_random_string(6))
        config_command = [edi_exec, 'config', 'init', project_name,
                          'debian-buster-{}'.format(get_debian_architecture())]
        run(config_command)  # run as non root

        parser = edi._setup_command_line_interface()
        cli_args = parser.parse_args(['image', 'create', '{}-develop.yml'.format(project_name)])

        Create().run_cli(cli_args)
        out, err = capsys.readouterr()
        print(out)
        assert not err

        lxc_compression_algo = get_server_image_compression_algorithm()
        lxc_export_extension = get_file_extension_from_image_compression_algorithm(lxc_compression_algo)

        images = [
            os.path.join(get_artifact_dir(), '{}-develop_edicommand_image_bootstrap_di.tar.gz'.format(project_name)),
            os.path.join(get_artifact_dir(), '{}-develop_edicommand_lxc_prepare_di.tar.gz'.format(project_name)),
            os.path.join(get_artifact_dir(), '{}-develop_edicommand_lxc_export{}'.format(project_name,
                                                                                         lxc_export_extension)),
            os.path.join(get_artifact_dir(), '{}-develop.result'.format(project_name)),
        ]
        for image in images:
            assert os.path.isfile(image)

        image_store_items = [
            "{}-develop_edicommand_lxc_import_di".format(project_name),
            "{}-develop_edicommand_lxc_publish".format(project_name)
        ]
        lxc_image_list_cmd = [lxc_exec(), 'image', 'list']
        result = run(lxc_image_list_cmd, stdout=subprocess.PIPE)
        for image_store_item in image_store_items:
            assert image_store_item in result.stdout

        parser = edi._setup_command_line_interface()
        cli_args = parser.parse_args(['image', 'create', '--clean', '{}-develop.yml'.format(project_name)])
        Create().run_cli(cli_args)

        parser = edi._setup_command_line_interface()
        cli_args = parser.parse_args(['image', 'create', '--recursive-clean', '8',
                                      '{}-develop.yml'.format(project_name)])
        Create().run_cli(cli_args)

        for image in images:
            assert not os.path.isfile(image)

        result = run(lxc_image_list_cmd, stdout=subprocess.PIPE)
        for image_store_item in image_store_items:
            assert image_store_item not in result.stdout


def test_empty_configuration(empty_config_file, monkeypatch):
    with open(empty_config_file, "r") as main_file:
        suppress_chown_during_debuild(monkeypatch)

        create_cmd = Create()
        result = create_cmd.run(main_file)
        assert result == []

        result = create_cmd.dry_run(main_file)
        assert result == {}

        create_cmd.clean_recursive(main_file, 100)
