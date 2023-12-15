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
import json
from contextlib import contextmanager
from edi.lib.helpers import FatalError
from edi.lib.buildahhelpers import is_container_existing, get_buildah_version, BuildahVersion
from edi.lib.shellhelpers import mockablerun
from tests.libtesting.helpers import get_command, get_sub_command
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
