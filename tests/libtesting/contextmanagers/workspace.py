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


from contextlib import contextmanager
import tempfile
import os
from edi.lib.helpers import chown_to_user
from tests.libtesting.helpers import get_project_root


@contextmanager
def workspace():
    """
    Provides a workspace folder within the project root and changes into it.
    The workspace folder can be used to perform tests.
    """
    with tempfile.TemporaryDirectory(dir=get_project_root(), prefix="tmp-pytest-") as workspace_dir:
        chown_to_user(workspace_dir)
        current_cwd = os.getcwd()
        os.chdir(workspace_dir)

        try:
            yield workspace_dir
        finally:
            os.chdir(current_cwd)
