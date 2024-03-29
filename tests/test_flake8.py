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
from edi.lib.shellhelpers import run
import os
import subprocess


@pytest.mark.requires_flake8
def test_flake8():
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    excluded_paths = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'venv')),
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.git'))
        ]
    cmd = ['flake8', '--exclude', ",".join(excluded_paths), '--max-line-length=120', path]
    result = run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        assert False, "flake8 reported errors!"
