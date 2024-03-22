# -*- coding: utf-8 -*-
# Copyright (C) 2024 Matthias Luescher
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
import subprocess
import tempfile
import json
import os
import logging
import shutil
from edi.lib.helpers import FatalError, chown_to_user
from edi.lib.podmanhelpers import (get_podman_version, PodmanVersion, is_image_existing, try_delete_image, untag_image,
                                   podman_exec)
from edi.lib.buildahhelpers import create_container, is_container_existing, delete_container, buildah_exec
from contextlib import contextmanager
from edi.lib.shellhelpers import run, mockablerun
from tests.libtesting.helpers import get_command, get_sub_command, get_random_string
from tests.libtesting.contextmanagers.mocked_executable import mocked_executable


@pytest.mark.requires_podman
def test_get_podman_version():
    version = get_podman_version()
    assert '.' in version


@contextmanager
def clear_podman_version_check_cache():
    try:
        PodmanVersion(clear_cache=True)
        yield
    finally:
        PodmanVersion(clear_cache=True)


@pytest.mark.requires_podman
def test_podman_version_check():
    with clear_podman_version_check_cache():
        check_method = PodmanVersion.check
        check_method()


def patch_podman_get_version(monkeypatch, fake_version):
    def fake_podman_version_command(*popenargs, **kwargs):
        if get_command(popenargs).endswith('podman') and get_sub_command(popenargs) == 'version':
            output_json = {
                "Client":
                    {
                        "APIVersion": fake_version,
                        "Version": fake_version,
                        "GoVersion": "go1.21.1",
                        "GitCommit": "",
                        "BuiltTime": "Thu Jan  1 01:00:00 1970",
                        "Built": 0,
                        "OsArch": "linux/amd64",
                        "Os": "linux"
                    }
            }

            return subprocess.CompletedProcess("fakerun", 0,
                                               stdout=json.dumps(output_json))
        else:
            return subprocess.run(*popenargs, **kwargs)

    monkeypatch.setattr(mockablerun, 'run_mockable', fake_podman_version_command)


def test_invalid_podman_version(monkeypatch):
    patch_podman_get_version(monkeypatch, '3.1.2')
    with mocked_executable('podman', '/here/is/no/podman'):
        with clear_podman_version_check_cache():
            check_method = PodmanVersion.check

            with pytest.raises(FatalError) as error:
                check_method()

            assert '3.1.2' in error.value.message
            assert '>=4.3.1' in error.value.message


def test_valid_podman_version(monkeypatch):
    patch_podman_get_version(monkeypatch, '16.1.0+bingo')
    with mocked_executable('podman', '/here/is/no/podman'):
        with clear_podman_version_check_cache():
            PodmanVersion.check()


@pytest.mark.requires_buildah
@pytest.mark.requires_podman
def test_buildah_podman_workflow(datadir):
    work_dir = os.getcwd()
    with tempfile.TemporaryDirectory(dir=work_dir) as tempdir:
        chown_to_user(tempdir)
        demo_rootfs_archive = os.path.join(tempdir, 'demo_rootfs.tar')
        shutil.copyfile(os.path.join(datadir, "demo_rootfs.tar"), demo_rootfs_archive)

        container_name = f'edi-pytest-{get_random_string(6)}'
        assert not is_container_existing(container_name)

        create_container(container_name, demo_rootfs_archive)

        image_name = f'edi-pytest-{get_random_string(6)}:test'.lower()

        cmd = [buildah_exec(), "commit", container_name, image_name]
        run(cmd, log_threshold=logging.INFO)

        cmd = [podman_exec(), "image", "inspect", "--format", "{{.Id}}", image_name]
        image_id = run(cmd, log_threshold=logging.INFO, stdout=subprocess.PIPE).stdout.strip()

        assert is_image_existing(image_name)

        second_container_name = f'edi-pytest-{get_random_string(6)}'

        cmd = [buildah_exec(), "from", "--name", second_container_name, image_name]
        run(cmd, log_threshold=logging.INFO)

        assert not try_delete_image(image_name)
        assert not try_delete_image(image_id)
        untag_image(image_name)
        assert not is_image_existing(image_name)
        assert is_image_existing(image_id)
        delete_container(second_container_name)
        assert try_delete_image(image_id)

        delete_container(container_name)
