# -*- coding: utf-8 -*-
# Copyright (C) 2016 Matthias Luescher
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
from tests.libtesting.helpers import get_command, get_command_parameter, get_sub_command
import os
import shutil
import subprocess
import requests_mock
from edi.lib import mockablerun


_ADAPTIVE = -42


def test_bootstrap(config_files, monkeypatch):
    with open(config_files, "r") as main_file:
        def fakegetuid():
            return 0

        monkeypatch.setattr(os, 'getuid', fakegetuid)

        def fakechown(*_):
            pass

        monkeypatch.setattr(shutil, 'chown', fakechown)

        def fakerun(*popenargs, **kwargs):
            if get_command(popenargs) == "chroot":
                rootfs_path = get_command_parameter(popenargs, "chroot")
                if not os.path.exists(rootfs_path):
                    os.mkdir(rootfs_path)
            elif get_command(popenargs) == "debootstrap":
                rootfs_path = popenargs[0][-2]
                apt_dir = os.path.join(rootfs_path, 'etc', 'apt')
                os.makedirs(apt_dir)
                pass
            elif get_command(popenargs) == "tar":
                archive = get_command_parameter(popenargs, '-acf')
                with open(archive, mode="w") as fakearchive:
                    fakearchive.write("fake archive")
            elif popenargs[0][-2] == "dpkg" and popenargs[0][-1] == "--print-architecture":
                return subprocess.CompletedProcess("fakerun", 0, 'amd64')
            elif get_command(popenargs).endswith("lxd") and get_sub_command(popenargs) == "--version":
                return subprocess.CompletedProcess("fakerun", 0, '2.18')
            elif get_command(popenargs) == "ssh" and get_sub_command(popenargs) == "-G":
                return subprocess.CompletedProcess("fakerun", 0, 'ssh config')
            elif get_command(popenargs) == "printenv":
                return subprocess.CompletedProcess("fakerun", 0, '')
            elif get_command(popenargs) == 'getent' and get_sub_command(popenargs) == 'passwd':
                return subprocess.CompletedProcess("fakerun", 0,
                                                   stdout='john:x:1000:1000:John Doe,,,:/no/such/directory:/bin/bash\n')
            else:
                print('Passthrough: {}'.format(get_command(popenargs)))
                return subprocess.run(*popenargs, **kwargs)

            return subprocess.CompletedProcess("fakerun", 0, '')

        monkeypatch.setattr(mockablerun, 'run_mockable', fakerun)

        monkeypatch.chdir(os.path.dirname(config_files))

        bootstrap_cmd = Bootstrap()
        with requests_mock.Mocker() as m:
            m.get('https://ftp-master.debian.org/keys/archive-key-8.asc', text='key file mockup')
            bootstrap_cmd.run(main_file)

        expected_result = bootstrap_cmd._result()
        assert os.path.exists(expected_result)

        previous_result_text = "previous result"
        with open(expected_result, mode="w") as previous_result:
            previous_result.write(previous_result_text)
        bootstrap_cmd2 = Bootstrap()
        bootstrap_cmd2.run(main_file)
        with open(expected_result, mode="r") as same_result:
            assert same_result.read() == previous_result_text
