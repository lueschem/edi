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
from tests.libtesting.fixtures.configfiles import config_files
import os
import shutil
import subprocess
import requests_mock


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
            print(popenargs)
            if popenargs[0][0] == "chroot":
                rootfspath = popenargs[0][1]
                if not os.path.exists(rootfspath):
                    os.mkdir(rootfspath)
            elif popenargs[0][0] == "tar":
                archive = popenargs[0][-1]
                with open(archive, mode="w") as fakearchive:
                    fakearchive.write("fake archive")
            return subprocess.CompletedProcess("fakerun", 0)
        monkeypatch.setattr(subprocess, 'run', fakerun)

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
