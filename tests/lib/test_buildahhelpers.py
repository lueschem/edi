# -*- coding: utf-8 -*-
# Copyright (C) 2023 Matthias Luescher
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


import subprocess
import pytest
import shutil
import json
import os
import tempfile
from contextlib import contextmanager
from edi.lib.artifact import Artifact, ArtifactType
from edi.lib.helpers import FatalError, chown_to_user
from edi.lib.buildahhelpers import (is_container_existing, get_buildah_version, BuildahVersion, create_container,
                                    run_buildah_unshare, delete_container, extract_container_rootfs)
from edi.lib.shellhelpers import mockablerun
from tests.libtesting.helpers import get_command, get_sub_command, get_random_string
from tests.libtesting.contextmanagers.mocked_executable import mocked_executable, mocked_buildah_version_check


@pytest.mark.parametrize("container_name, inspect_result, expected_result", [
    ("debian-bullseye", 125, False),
    ("debian-buster", 0, True),
    ("", 125, False),
])
def test_is_buildah_container_existing(monkeypatch, container_name, inspect_result, expected_result):
    with mocked_executable('buildah', '/here/is/no/buildah'):
        with mocked_buildah_version_check():
            def fake_buildah_inspect_command(*popenargs, **kwargs):
                if get_command(popenargs).endswith('buildah') and get_sub_command(popenargs) == 'inspect':
                    return subprocess.CompletedProcess("fakerun", inspect_result, stdout="")
                else:
                    return subprocess.run(*popenargs, **kwargs)

            monkeypatch.setattr(mockablerun, 'run_mockable', fake_buildah_inspect_command)
            result = is_container_existing(container_name)
            assert result == expected_result


@pytest.mark.requires_buildah
def test_get_buildah_version():
    version = get_buildah_version()
    assert '.' in version


@contextmanager
def clear_buildah_version_check_cache():
    try:
        BuildahVersion(clear_cache=True)
        yield
    finally:
        BuildahVersion(clear_cache=True)


@pytest.mark.requires_buildah
def test_buildah_version_check():
    with clear_buildah_version_check_cache():
        check_method = BuildahVersion.check
        check_method()


def patch_buildah_get_version(monkeypatch, fake_version):
    def fake_buildah_version_command(*popenargs, **kwargs):
        if get_command(popenargs).endswith('buildah') and get_sub_command(popenargs) == 'version':
            output_json = {
                "version": fake_version,
                "goVersion": "go1.17",
                "imageSpec": "1.0.1",
                "runtimeSpec": "1.0.2-dev",
                "cniSpec": "0.4.0",
                "libcniVersion": "",
                "imageVersion": "5.16.0",
                "gitCommit": "",
                "built": "Thu Jan  1 01:00:00 1970",
                "osArch": "linux/amd64",
                "buildPlatform": "linux/amd64"
            }

            return subprocess.CompletedProcess("fakerun", 0,
                                               stdout=json.dumps(output_json))
        else:
            return subprocess.run(*popenargs, **kwargs)

    monkeypatch.setattr(mockablerun, 'run_mockable', fake_buildah_version_command)


def test_invalid_version(monkeypatch):
    patch_buildah_get_version(monkeypatch, '1.1.0')
    with mocked_executable('buildah', '/here/is/no/buildah'):
        with clear_buildah_version_check_cache():
            check_method = BuildahVersion.check

            with pytest.raises(FatalError) as error:
                check_method()

            assert '1.1.0' in error.value.message
            assert '>=1.23.1' in error.value.message


def test_valid_buildah_version(monkeypatch):
    patch_buildah_get_version(monkeypatch, '2.0.0+bingo')
    with mocked_executable('buildah', '/here/is/no/buildah'):
        with clear_buildah_version_check_cache():
            BuildahVersion.check()


@pytest.mark.requires_buildah
def test_buildah_container_creation(datadir):
    container_name = f'edi-pytest-{get_random_string(6)}'
    assert not is_container_existing(container_name)

    work_dir = os.getcwd()
    with tempfile.TemporaryDirectory(dir=work_dir) as archive_dir:
        chown_to_user(archive_dir)
        demo_rootfs_archive = os.path.join(archive_dir, 'demo_rootfs.tar')
        shutil.copyfile(os.path.join(datadir, "demo_rootfs.tar"), demo_rootfs_archive)

        create_container(container_name, Artifact(name='xy', location=demo_rootfs_archive, type=ArtifactType.PATH))
        assert is_container_existing(container_name)

        with pytest.raises(FatalError) as error:
            create_container(container_name, Artifact(name='xy', location=demo_rootfs_archive, type=ArtifactType.PATH))

        assert 'already exists' in error.value.message
        assert container_name in error.value.message

        result = run_buildah_unshare(container_name, r'cat ${container_root}/rootfs_test')
        assert "nothing here" in result.stdout

        delete_container(container_name)

        assert not is_container_existing(container_name)


@pytest.mark.requires_buildah
def test_buildah_rootfs_extraction(datadir):
    container_name = f'edi-pytest-{get_random_string(6)}'
    assert not is_container_existing(container_name)

    work_dir = os.getcwd()
    with tempfile.TemporaryDirectory(dir=work_dir) as tempdir:
        chown_to_user(tempdir)
        demo_rootfs_archive = os.path.join(tempdir, 'demo_rootfs.tar')
        shutil.copyfile(os.path.join(datadir, "demo_rootfs.tar"), demo_rootfs_archive)

        extracted_rootfs_archive = os.path.join(tempdir, 'extracted_rootfs.tar')

        assert not os.path.isfile(extracted_rootfs_archive)

        with pytest.raises(FatalError) as error:
            extract_container_rootfs(container_name, extracted_rootfs_archive)

        assert 'does not exist' in error.value.message
        assert container_name in error.value.message

        create_container(container_name, Artifact(name='xy', location=demo_rootfs_archive, type=ArtifactType.PATH))

        extract_container_rootfs(container_name, extracted_rootfs_archive)

        with pytest.raises(FatalError) as error:
            extract_container_rootfs(container_name, extracted_rootfs_archive)

        assert 'already exists' in error.value.message
        assert str(extracted_rootfs_archive) in error.value.message

        assert os.path.isfile(extracted_rootfs_archive)

        delete_container(container_name)


@pytest.mark.requires_buildah
def test_buildah_container_creation_failure():
    with pytest.raises(FatalError) as error:
        create_container("some-stupid-container-name",
                         Artifact(name='xy', location="/path/to/wrong_rootfs_archive.tar", type=ArtifactType.PATH))

    assert 'does not exist' in error.value.message
    assert 'wrong_rootfs_archive.tar' in error.value.message
