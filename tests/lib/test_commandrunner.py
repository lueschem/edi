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

from edi.lib.configurationparser import ConfigurationParser
from edi.lib.commandrunner import CommandRunner
from tests.libtesting.fixtures.configfiles import config_files
from tests.libtesting.contextmanagers.workspace import workspace
from tests.libtesting.helpers import get_command
from edi.lib import mockablerun
import shutil
import subprocess
import os
from codecs import open


def test_run_all(config_files, monkeypatch):
    def intercept_command_run(*popenargs, **kwargs):
        if "command" in get_command(popenargs):
            print(popenargs)
            with open(get_command(popenargs), encoding='utf-8') as f:
                print(f.read())
            return subprocess.run(*popenargs, **kwargs)
        else:
            print("passthrough")
            return subprocess.run(*popenargs, **kwargs)

    monkeypatch.setattr(mockablerun, 'run_mockable', intercept_command_run)

    def fakechown(*_):
        pass

    monkeypatch.setattr(shutil, 'chown', fakechown)

    with workspace() as w:
        with open(config_files, "r") as main_file:
            parser = ConfigurationParser(main_file)

            input_file = os.path.join(w, 'input.txt')
            with open(input_file, mode='w', encoding='utf-8') as i:
                i.write("*input file*\n")

            runner = CommandRunner(parser, 'postprocessing_commands', input_file)

            output = runner.run_all()

            assert str(w) in str(output)

            with open(output, mode='r') as result:
                content = result.read()
                assert "*input file*" in content
                assert "*first step*" in content
                assert "*last step*" in content
                assert "*second step*" not in content
