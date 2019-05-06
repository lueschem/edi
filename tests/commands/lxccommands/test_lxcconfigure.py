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
from edi.lib.shellhelpers import run, get_debian_architecture
from edi.lib.helpers import get_artifact_dir
from edi.lib.configurationparser import get_base_dictionary
from edi.lib.proxyhelpers import ProxySetup
from edi.commands.lxccommands.lxcconfigure import Configure
from edi.commands.clean import Clean
from edi.lib.lxchelpers import lxc_exec
import edi
import yaml
import re
import subprocess
from codecs import open
from shutil import copyfile


def verify_shared_folder(container_name):
    base_dict = get_base_dictionary()
    random_file = get_random_string(20)
    workspace_folder = 'edi-workspace'
    cmd = [lxc_exec(), 'exec', container_name, '--',
           'sudo', '-u', base_dict.get('edi_current_user_name'), 'touch',
           os.path.join(base_dict.get('edi_current_user_target_home_directory'), workspace_folder, random_file)]
    run(cmd)
    shared_file = os.path.join(base_dict.get('edi_current_user_host_home_directory'),
                               workspace_folder, random_file)
    stat = os.stat(shared_file)
    assert stat.st_gid == base_dict.get('edi_current_user_gid')
    assert stat.st_uid == base_dict.get('edi_current_user_uid')
    os.remove(shared_file)


def modify_develop_overlay(project_name):
    overlay_file = os.path.join('configuration', 'overlay', '{}-develop.global.yml'.format(project_name))
    with open(overlay_file, mode='r') as overlay:
        overlay_config = yaml.load(overlay.read())

    base_system_mod = {'playbooks': {
        '100_base_system': {
            'parameters': {
                'create_default_user': True,
                'default_user_name': 'testuser',
                'install_openssh_server': True
            }}}}

    overlay_config.update(base_system_mod)

    with open(overlay_file, mode='w') as overlay:
        overlay.write(yaml.dump(overlay_config))


def prepare_pub_key(datadir):
    os.mkdir('ssh_pub_keys')

    pub_key_file = os.path.join(str(datadir), 'keys', 'test_id_rsa.pub')
    pub_key_file_copy = os.path.join('ssh_pub_keys', 'test_id_rsa.pub')
    copyfile(pub_key_file, pub_key_file_copy)


def get_container_ip_addr(container_name, interface):
    cmd = [lxc_exec(), 'exec', container_name, '--', 'ip', '-4', 'addr', 'show', interface]
    raw_ip_result = run(cmd, stdout=subprocess.PIPE).stdout
    return re.findall(r'^\s*inet\s([0-9\.]*)/.*', raw_ip_result, re.MULTILINE)[0]


@requires_lxc
@requires_ansible
@requires_debootstrap
@requires_sudo
def test_build_stretch_container(capsys, datadir):
    with workspace():
        ProxySetup(clear_cache=True)

        edi_exec = os.path.join(get_project_root(), 'bin', 'edi')
        project_name = 'pytest-{}'.format(get_random_string(6))
        config_command = [edi_exec, 'config', 'init', project_name,
                          'debian-stretch-{}'.format(get_debian_architecture())]
        run(config_command)  # run as non root

        # enable ssh server and create a default user
        modify_develop_overlay(project_name)
        # copy pub key into default pub key folder
        prepare_pub_key(datadir)

        container_name = 'pytest-{}'.format(get_random_string(6))
        parser = edi._setup_command_line_interface()
        cli_args = parser.parse_args(['-v', 'lxc', 'configure', container_name, '{}-develop.yml'.format(project_name)])

        Configure().run_cli(cli_args)
        out, err = capsys.readouterr()
        print(out)
        assert not err

        images = [
            os.path.join(get_artifact_dir(), '{}-develop_edicommand_image_bootstrap.tar.gz'.format(project_name)),
            os.path.join(get_artifact_dir(), '{}-develop_edicommand_lxc_prepare.tar.gz'.format(project_name))
        ]
        for image in images:
            assert os.path.isfile(image)

        lxc_image_list_cmd = [lxc_exec(), 'image', 'list']
        result = run(lxc_image_list_cmd, stdout=subprocess.PIPE)
        assert project_name in result.stdout

        parser = edi._setup_command_line_interface()
        cli_args = parser.parse_args(['-v', 'clean', '{}-develop.yml'.format(project_name)])
        Clean().run_cli(cli_args)

        for image in images:
            assert not os.path.isfile(image)

        result = run(lxc_image_list_cmd, stdout=subprocess.PIPE)
        assert project_name not in result.stdout

        verification_command = [lxc_exec(), 'exec', container_name, '--', 'cat', '/etc/os-release']
        result = run(verification_command, stdout=subprocess.PIPE)
        assert '''VERSION_ID="9"''' in result.stdout
        assert 'ID=debian' in result.stdout

        os.chmod(os.path.join(str(datadir), 'keys'), 0o700)
        os.chmod(os.path.join(str(datadir), 'keys', 'test_id_rsa'), 0o600)
        container_ip = get_container_ip_addr(container_name, 'lxcif0')
        ssh_cmd = ['ssh', '-i', str(os.path.join(str(datadir), 'keys', 'test_id_rsa')),
                   '-o', 'UserKnownHostsFile=/dev/null', '-o', 'StrictHostKeyChecking=no',
                   'testuser@{}'.format(container_ip), 'true']
        # ssh command should work without password due to proper ssh key setup!
        run(ssh_cmd, sudo=True, timeout=5)

        verify_shared_folder(container_name)

        stop_command = [lxc_exec(), 'stop', container_name]
        run(stop_command)

        delete_command = [lxc_exec(), 'delete', container_name]
        run(delete_command)
