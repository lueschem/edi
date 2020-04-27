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
import pytest
import tempfile
from edi.lib.shellhelpers import (run, safely_remove_artifacts_folder, gpg_agent, require,
                                  Executables, get_user_home_directory, mockablerun, mount_aware_tempdir)
from tests.libtesting.contextmanagers.workspace import workspace
from tests.libtesting.helpers import (get_random_string, suppress_chown_during_debuild, get_command,
                                      get_sub_command, get_command_parameter)
from edi.lib.helpers import get_artifact_dir, create_artifact_dir, FatalError
import subprocess


def test_get_user_home_directory(monkeypatch):
    def fake_getent_passwd(*popenargs, **kwargs):
        if get_command(popenargs) == 'getent' and get_sub_command(popenargs) == 'passwd' and \
                get_command_parameter(popenargs, 'passwd') == 'john':
            return subprocess.CompletedProcess("fakerun", 0,
                                               stdout='john:x:1000:1000:John Doe,,,:/home/john:/bin/bash\n')
        else:
            return subprocess.run(*popenargs, **kwargs)

    monkeypatch.setattr(mockablerun, 'run_mockable', fake_getent_passwd)
    assert get_user_home_directory('john') == '/home/john'


def test_artifacts_folder_removal(monkeypatch):
    suppress_chown_during_debuild(monkeypatch)

    with workspace() as workdir:
        create_artifact_dir()
        artifacts_dir = get_artifact_dir()
        assert str(workdir) in str(artifacts_dir)
        random_dir_name = get_random_string(20)
        abs_dir_name = os.path.join(artifacts_dir, random_dir_name)
        run(['mkdir', '-p', abs_dir_name])
        assert os.path.isdir(abs_dir_name)
        safely_remove_artifacts_folder(abs_dir_name)
        assert not os.path.isdir(abs_dir_name)


@pytest.mark.requires_sudo
def test_artifacts_folder_removal_as_sudo():
    with workspace() as workdir:
        create_artifact_dir()
        artifacts_dir = get_artifact_dir()
        assert str(workdir) in str(artifacts_dir)
        random_dir_name = get_random_string(20)
        abs_dir_name = os.path.join(artifacts_dir, random_dir_name)
        mount_folder = os.path.join(workdir, get_random_string(20))
        mount_point = os.path.join(abs_dir_name, 'mnt')

        for folder in [abs_dir_name, mount_folder, mount_point]:
            run(['mkdir', '-p', folder])
            assert os.path.isdir(folder)

        run(['mount', '--bind', mount_folder, mount_point], sudo=True)

        with pytest.raises(FatalError) as error:
            safely_remove_artifacts_folder(abs_dir_name, sudo=True)
        assert abs_dir_name in error.value.message

        run(['umount', mount_point], sudo=True)
        safely_remove_artifacts_folder(abs_dir_name, sudo=True)

        assert not os.path.isdir(abs_dir_name)


def test_gpg_agent(tmpdir):
    fake_socket = os.path.join(str(tmpdir), 'S.gpg-agent.fake')
    with gpg_agent(str(tmpdir)):
        assert not os.path.isfile(fake_socket)
        with open(fake_socket, mode='w') as file:
            file.write('fake socket')
        assert os.path.isfile(fake_socket)

    assert not os.path.isfile(fake_socket)


def test_executables():
    executables = Executables(clear_cache=True)
    assert executables.has('ls') is True
    assert executables.get('true') == '/bin/true' or executables.get('true') == '/usr/bin/true'
    assert executables.has('does-really-not-exist') is False
    assert executables.get('does-not-exist-at-all') is None
    assert executables.has('ls') is True  # cache
    assert executables.has('does-really-not-exist') is False


@require('ls', 'some command')
def some_decorated_function(arg1, arg2):
    print('{} + {})'.format(arg1, arg2))
    return arg1 + arg2


@require('does-really-not-exist', 'other command')
def other_decorated_function(arg1, arg2):
    print('{} + {})'.format(arg1, arg2))
    return arg1 + arg2


def _failing_check():
    raise FatalError("check failed")


@require('ls', 'some command', _failing_check)
def decorated_function_with_failing_check():
    pass


class SomeClass:
    def __init__(self):
        self.some_name = "foo"
        self.other_name = "bar"

    @require('ls')
    def do_this(self, directory):
        return 'ls {}'.format(directory)

    @require('does-really-not-exist')
    def do_that(self, message):
        return 'does-really-not-exist {}'.format(message)


def test_require():
    assert some_decorated_function(40, 2) == 42
    with pytest.raises(FatalError) as error:
        other_decorated_function(40, 2)
    assert 'other command' in error.value.message
    sc = SomeClass()
    assert sc.do_this('foo') == 'ls foo'
    with pytest.raises(FatalError) as error:
        sc.do_that('Hello world!')

    assert 'apt or snap' in error.value.message
    assert 'does-really-not-exist' in error.value.message


def test_require_with_failing_check():
    with pytest.raises(FatalError) as error:
        decorated_function_with_failing_check()

    assert 'check failed' in error.value.message


@pytest.mark.requires_sudo
def test_mount_aware_tempdir():
    work_dir = os.getcwd()
    with mount_aware_tempdir(work_dir) as tempdir:
        assert os.path.isdir(work_dir)
        assert os.path.isdir(tempdir)

    assert os.path.isdir(work_dir)
    assert not os.path.isdir(tempdir)


@pytest.mark.requires_sudo
def test_mount_aware_tempdir_remove_mount():
    work_dir = os.getcwd()
    with tempfile.TemporaryDirectory(dir=work_dir) as mount_target:
        mount_target_content = os.path.join(mount_target, 'keep_me')
        run(['mkdir', '-p', mount_target_content], sudo=True)
        assert os.path.isdir(mount_target_content)

        with mount_aware_tempdir(work_dir, log_warning=True) as tempdir:
            assert os.path.isdir(tempdir)
            mount_point = os.path.join(tempdir, 'mount_point')
            run(['mkdir', '-p', mount_point], sudo=True)
            assert not os.path.isdir(os.path.join(tempdir, 'mount_point', 'keep_me'))
            run(['mount', '--bind', mount_target, mount_point], sudo=True)
            assert os.path.isdir(os.path.join(tempdir, 'mount_point', 'keep_me'))

        assert not os.path.isdir(tempdir)
        assert os.path.isdir(mount_target_content)

    assert not os.path.isdir(mount_target_content)
