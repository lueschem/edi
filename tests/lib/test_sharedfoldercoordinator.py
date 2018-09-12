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


from jinja2 import Template
from edi.lib.helpers import get_user, FatalError
from edi.lib.shellhelpers import get_user_home_directory
from edi.lib.configurationparser import ConfigurationParser, command_context
from edi.lib.sharedfoldercoordinator import SharedFolderCoordinator
from tests.libtesting.helpers import get_command, get_sub_command, get_command_parameter
from edi.lib.yamlhelpers import normalize_yaml
import subprocess
from edi.lib import mockablerun
import pytest
import os

expected_profile_boilerplates = [
    """
name: privileged
description: Privileged edi lxc container
config:
  security.privileged: 'true'
devices: {}
""",
    """
name: shared_folder
config: {}
description: Shared folder for edi lxc container
devices:
  shared_folder_other_folder_for_{{ user }}:
    path: /foo/bar/target_mountpoint
    source: {{ home }}/valid_folder
    type: disk
""",
    """
name: shared_folder
config: {}
description: Shared folder for edi lxc container
devices:
  shared_folder_workspace_for_{{ user }}:
    path: {{ target_home }}/mywork
    source: {{ home }}/work
    type: disk
"""]


def render_expected_profiles():
    user = get_user()
    dictionary = {'user': user,
                  'home': get_user_home_directory(user),
                  'target_home': '/home/{}'.format(user)}
    expected_profiles = []
    for boilerplate in expected_profile_boilerplates:
        template = Template(boilerplate)
        expected_profiles.append(normalize_yaml(template.render(dictionary)))
    return expected_profiles


def test_pre_config_profiles(config_files):
    expected_profiles = render_expected_profiles()

    with open(config_files, "r") as main_file:
        parser = ConfigurationParser(main_file)

        coordinator = SharedFolderCoordinator(parser)
        profiles = coordinator.get_pre_config_profiles()

        assert len(profiles) == 1

        assert profiles[0][0] == expected_profiles[0]


def test_post_config_profiles(config_files):
    expected_profiles = render_expected_profiles()

    with open(config_files, "r") as main_file:
        parser = ConfigurationParser(main_file)

        coordinator = SharedFolderCoordinator(parser)
        profiles = coordinator.get_post_config_profiles()

        assert len(profiles) == 3

        for i in range(0, 3):
            assert profiles[i][0] == expected_profiles[i]


def test_get_mountpoints(config_files):
    with open(config_files, "r") as main_file:
        parser = ConfigurationParser(main_file)

        coordinator = SharedFolderCoordinator(parser)
        mountpoints = coordinator.get_mountpoints()
        assert mountpoints[0] == '/foo/bar/target_mountpoint'
        assert len(mountpoints) == 2


def test_verify_container_mountpoints(config_files, monkeypatch):
    with open(config_files, "r") as main_file:
        def fake_lxc_exec_command(*popenargs, **kwargs):
            if get_command(popenargs).endswith('lxc') and get_sub_command(popenargs) == 'exec':
                return subprocess.CompletedProcess("fakerun", 0, '')
            else:
                return subprocess.run(*popenargs, **kwargs)

        monkeypatch.setattr(mockablerun, 'run_mockable', fake_lxc_exec_command)

        parser = ConfigurationParser(main_file)

        coordinator = SharedFolderCoordinator(parser)
        coordinator.verify_container_mountpoints('fake-container')


def test_verify_container_mountpoints_connection_failure(config_files, monkeypatch):
    with open(config_files, "r") as main_file:
        def fake_lxc_exec_command(*popenargs, **kwargs):
            if get_command(popenargs).endswith('lxc') and get_sub_command(popenargs) == 'exec':
                if get_command_parameter(popenargs, '--') == 'true':
                    cmd = ['bash', '-c', '>&2 echo -e "lxc command failed" ; exit 1']
                    return subprocess.run(cmd, **kwargs)
                else:
                    return subprocess.CompletedProcess("fakerun", 0, '')
            else:
                return subprocess.run(*popenargs, **kwargs)

        monkeypatch.setattr(mockablerun, 'run_mockable', fake_lxc_exec_command)

        parser = ConfigurationParser(main_file)

        coordinator = SharedFolderCoordinator(parser)
        with pytest.raises(FatalError) as error:
            coordinator.verify_container_mountpoints('fake-container')
        assert 'fake-container' in error.value.message
        assert 'lxc command failed' in error.value.message


def test_verify_container_mountpoints_failure(config_files, monkeypatch):
    with open(config_files, "r") as main_file:
        def fake_lxc_exec_command(*popenargs, **kwargs):
            if get_command(popenargs).endswith('lxc') and get_sub_command(popenargs) == 'exec':
                if get_command_parameter(popenargs, '--') == 'test':
                    return subprocess.CompletedProcess("failure", 1, 'failure')
                else:
                    return subprocess.CompletedProcess("fakerun", 0, '')
            else:
                return subprocess.run(*popenargs, **kwargs)

        monkeypatch.setattr(mockablerun, 'run_mockable', fake_lxc_exec_command)

        parser = ConfigurationParser(main_file)

        coordinator = SharedFolderCoordinator(parser)
        with pytest.raises(FatalError) as error:
            coordinator.verify_container_mountpoints('fake-container')
        assert 'fake-container' in error.value.message
        assert '/foo/bar/target_mountpoint' in error.value.message


def test_get_mandatory_item():
    with pytest.raises(FatalError) as missing:
        SharedFolderCoordinator._get_mandatory_item('some_folder', {}, 'mountpoint')
    assert 'some_folder' in missing.value.message
    assert 'mountpoint' in missing.value.message

    with pytest.raises(FatalError) as subfolder:
        SharedFolderCoordinator._get_mandatory_item('some_folder', {'mountpoint': 'mount/point'}, 'mountpoint')
    assert 'some_folder' in subfolder.value.message
    assert 'mountpoint' in subfolder.value.message


def test_without_shared_folders(empty_config_file):
    with open(empty_config_file, "r") as main_file:
        parser = ConfigurationParser(main_file)

        coordinator = SharedFolderCoordinator(parser)
        mountpoints = coordinator.get_mountpoints()
        assert isinstance(mountpoints, list)
        assert len(mountpoints) == 0
        pre = coordinator.get_pre_config_profiles()
        assert isinstance(pre, list)
        assert len(pre) == 0
        post = coordinator.get_post_config_profiles()
        assert isinstance(post, list)
        assert len(post) == 0


def test_create_host_folders_folder_exists(config_files, monkeypatch):
    with open(config_files, "r") as main_file:
        parser = ConfigurationParser(main_file)

        coordinator = SharedFolderCoordinator(parser)

        def fake_os_path_isdir(*_):
            return True

        monkeypatch.setattr(os.path, 'isdir', fake_os_path_isdir)

        def fake_os_path_exists(*_):
            return True

        monkeypatch.setattr(os.path, 'exists', fake_os_path_exists)

        coordinator.create_host_folders()  # nothing to do


def test_create_host_folders_not_a_folder(config_files, monkeypatch):
    with open(config_files, "r") as main_file:
        parser = ConfigurationParser(main_file)

        coordinator = SharedFolderCoordinator(parser)

        def fake_os_path_isdir(*_):
            return False

        monkeypatch.setattr(os.path, 'isdir', fake_os_path_isdir)

        def fake_os_path_exists(*_):
            return True

        monkeypatch.setattr(os.path, 'exists', fake_os_path_exists)

        with pytest.raises(FatalError) as error:
            coordinator.create_host_folders()  # exists but not a folder

        assert 'valid_folder' in error.value.message


def test_no_shared_folders_for_distributable_image(config_files, monkeypatch):
    with open(config_files, "r") as main_file:
        with command_context({'edi_create_distributable_image': True}):
            parser = ConfigurationParser(main_file)

            coordinator = SharedFolderCoordinator(parser)

            def fake_os_path_exists(*_):
                return False
            monkeypatch.setattr(os.path, 'exists', fake_os_path_exists)

            def fake_run(*popenargs, **kwargs):
                # We should not run anything!
                assert False

            monkeypatch.setattr(mockablerun, 'run_mockable', fake_run)

            coordinator.create_host_folders()
            coordinator.verify_container_mountpoints('does-not-exist')
            assert coordinator.get_mountpoints() == []
            assert coordinator.get_pre_config_profiles() == []
            assert coordinator.get_post_config_profiles() == []


def test_create_host_folders_successful_create(config_files, monkeypatch):
    with open(config_files, "r") as main_file:
        parser = ConfigurationParser(main_file)

        coordinator = SharedFolderCoordinator(parser)

        def fake_os_path_isdir(*_):
            return False

        monkeypatch.setattr(os.path, 'isdir', fake_os_path_isdir)

        def fake_os_path_exists(*_):
            return False

        monkeypatch.setattr(os.path, 'exists', fake_os_path_exists)

        def fake_mkdir_command(*popenargs, **kwargs):
            if get_command(popenargs) == 'mkdir' and get_sub_command(popenargs) == '-p':
                folder = popenargs[0][-1]
                assert 'valid_folder' in folder or 'work' in folder
                return subprocess.CompletedProcess("fakerun", 0, '')
            else:
                return subprocess.run(*popenargs, **kwargs)

        monkeypatch.setattr(mockablerun, 'run_mockable', fake_mkdir_command)

        coordinator.create_host_folders()  # successful mkdir


def test_create_host_folders_failed_create(config_files, monkeypatch):
    with open(config_files, "r") as main_file:
        parser = ConfigurationParser(main_file)

        coordinator = SharedFolderCoordinator(parser)

        def fake_os_path_isdir(*_):
            return False

        monkeypatch.setattr(os.path, 'isdir', fake_os_path_isdir)

        def fake_os_path_exists(*_):
            return False

        monkeypatch.setattr(os.path, 'exists', fake_os_path_exists)

        def fake_mkdir_command(*popenargs, **kwargs):
            if get_command(popenargs) == 'mkdir' and get_sub_command(popenargs) == '-p':
                cmd = ['bash', '-c', '>&2 echo -e "no permission" ; exit 1']
                return subprocess.run(cmd, **kwargs)
            else:
                return subprocess.run(*popenargs, **kwargs)

        monkeypatch.setattr(mockablerun, 'run_mockable', fake_mkdir_command)

        with pytest.raises(FatalError) as error:
            coordinator.create_host_folders()  # failed mkdir

        assert 'valid_folder' in error.value.message
        assert 'no permission' in error.value.message
