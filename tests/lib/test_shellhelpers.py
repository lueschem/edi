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


import os
import pytest
import shutil
from edi.lib.shellhelpers import run, safely_remove_artifacts_folder
from tests.libtesting.contextmanagers.workspace import workspace
from tests.libtesting.helpers import get_random_string
from edi.lib.helpers import get_artifact_dir, create_artifact_dir, FatalError, get_user
from tests.libtesting.optins import requires_sudo


def test_artifacts_folder_removal(monkeypatch):
    def fakechown(*_):
        pass

    if get_user() == 'root':  # debuild case
        monkeypatch.setattr(shutil, 'chown', fakechown)

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


@requires_sudo
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
