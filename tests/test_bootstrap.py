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
from tests.fixtures.configfiles import config_files
import os
import subprocess
import shutil


_ADAPTIVE = -42


def test_bootstrap(config_files, monkeypatch):
    with open(config_files, "r") as main_file:
        def fakeroot():
            return 0
        monkeypatch.setattr(os, 'getuid', fakeroot)

        def fakerun(*popenargs, **kwargs):
            print(popenargs)
            if popenargs[0][0] == "chroot":
                rootfspath = popenargs[0][1]
                if not os.path.exists(rootfspath):
                    os.mkdir(rootfspath)
            elif popenargs[0][0] == "tar":
                archive = popenargs[0][-1]
                open(archive, mode="w").close()
            return subprocess.CompletedProcess("fakerun", 0)
        monkeypatch.setattr(subprocess, 'run', fakerun)

        monkeypatch.chdir(os.path.dirname(config_files))

        #def fakelistdir(*args, **kwargs):
        #    return ["foo", "bar"]
        #monkeypatch.setattr(os, 'listdir', fakelistdir)

        Bootstrap().run(main_file)
