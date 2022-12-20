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


import subprocess
import pytest
from subprocess import CalledProcessError
from contextlib import contextmanager
from edi.lib.helpers import FatalError
from edi.lib.lxchelpers import (get_server_image_compression_algorithm,
                                get_file_extension_from_image_compression_algorithm, lxc_exec,
                                get_lxd_version, LxdVersion, is_bridge_available, create_bridge,
                                is_container_running, get_profile_description, is_profile_existing,
                                write_lxc_profile)
from edi.lib.shellhelpers import mockablerun, run
from tests.libtesting.helpers import get_command, get_sub_command, log_during_run
from tests.libtesting.contextmanagers.mocked_executable import mocked_executable, mocked_lxd_version_check


@pytest.mark.requires_lxc
def test_get_server_image_compression():
    result = get_server_image_compression_algorithm()
    assert result in ['bzip2', 'gzip', 'lzma', 'xz', 'none']


def test_get_server_image_compression_bzip2(monkeypatch):
    with mocked_executable('lxc', '/here/is/no/lxc'):
        with mocked_lxd_version_check():
            def fake_lxc_config_command(*popenargs, **kwargs):
                if get_command(popenargs).endswith('lxc') and get_sub_command(popenargs) == 'config':
                    return subprocess.CompletedProcess("fakerun", 0, stdout='bzip2')
                else:
                    return subprocess.run(*popenargs, **kwargs)

            monkeypatch.setattr(mockablerun, 'run_mockable', fake_lxc_config_command)
            result = get_server_image_compression_algorithm()
            assert result == 'bzip2'


lxc_info_json = """
[
  {
    "name": "debian-bullseye",
    "status": "Stopped"
  },
  {
    "name": "debian-buster",
    "status": "Running"
  }
]
"""


@pytest.mark.parametrize("container_name, lxc_output, expected_result", [
    ("debian-bullseye", lxc_info_json, False),
    ("debian-buster", lxc_info_json, True),
    ("debian", lxc_info_json, False),
    ("debian", "", False),
    ("debian", "[]", False),
])
def test_is_container_running(monkeypatch, container_name, lxc_output, expected_result):
    with mocked_executable('lxc', '/here/is/no/lxc'):
        with mocked_lxd_version_check():
            def fake_lxc_info_command(*popenargs, **kwargs):
                if get_command(popenargs).endswith('lxc') and get_sub_command(popenargs) == 'list':
                    return subprocess.CompletedProcess("fakerun", 0, stdout=lxc_output)
                else:
                    return subprocess.run(*popenargs, **kwargs)

            monkeypatch.setattr(mockablerun, 'run_mockable', fake_lxc_info_command)
            result = is_container_running(container_name)
            assert result == expected_result


@pytest.mark.parametrize("algorithm, expected_extension", [
    ("none", ".tar"),
    ("bzip2", ".tar.bz2"),
    ("gzip", ".tar.gz"),
])
def test_get_file_extension_from_image_compression_algorithm(algorithm, expected_extension):
    extension = get_file_extension_from_image_compression_algorithm(algorithm)
    assert extension == expected_extension


def test_get_file_extension_from_image_compression_algorithm_failure():
    with pytest.raises(FatalError) as e:
        get_file_extension_from_image_compression_algorithm('42')

    assert 'compression algorithm' in str(e)
    assert '42' in str(e)


@pytest.mark.requires_lxc
def test_get_lxd_version():
    version = get_lxd_version()
    assert '.' in version


@contextmanager
def clear_lxd_version_check_cache():
    try:
        LxdVersion(clear_cache=True)
        yield
    finally:
        LxdVersion(clear_cache=True)


@pytest.mark.requires_lxc
def test_lxd_version_check():
    with clear_lxd_version_check_cache():
        check_method = LxdVersion.check
        check_method()


def patch_lxd_get_version(monkeypatch, fake_version):
    def fake_lxd_version_command(*popenargs, **kwargs):
        if get_command(popenargs).endswith('lxd') and get_sub_command(popenargs) == '--version':
            return subprocess.CompletedProcess("fakerun", 0,
                                               stdout='{}\n'.format(fake_version))
        else:
            return subprocess.run(*popenargs, **kwargs)

    monkeypatch.setattr(mockablerun, 'run_mockable', fake_lxd_version_command)


def test_invalid_version(monkeypatch):
    patch_lxd_get_version(monkeypatch, '2.2.0')
    with mocked_executable('lxd', '/here/is/no/lxd'):
        with clear_lxd_version_check_cache():
            check_method = LxdVersion.check

            with pytest.raises(FatalError) as error:
                check_method()

            assert '2.2.0' in error.value.message
            assert '>=3.0.0' in error.value.message
            assert 'xenial-backports' in error.value.message


def test_valid_version(monkeypatch):
    patch_lxd_get_version(monkeypatch, '3.0.0+bingo')
    with mocked_executable('lxd', '/here/is/no/lxd'):
        with clear_lxd_version_check_cache():
            LxdVersion.check()


@pytest.mark.requires_lxc
def test_is_bridge_available():
    bridge_name = "edibrtesttest42"
    assert not is_bridge_available(bridge_name)
    create_bridge(bridge_name)
    assert is_bridge_available(bridge_name)
    with pytest.raises(CalledProcessError):
        create_bridge(bridge_name)
    cmd = [lxc_exec(), "network", "delete", bridge_name]
    run(cmd)
    assert not is_bridge_available(bridge_name)


@pytest.mark.requires_lxc
def test_is_description_empty_on_inexistent_profile():
    assert "" == get_profile_description("this-edi-profile-does-not-exist")


@pytest.mark.requires_lxc
def test_is_description_empty_on_created_profile():
    profile_name = 'this-is-an-unused-edi-pytest-profile'
    if is_profile_existing(profile_name):
        run([lxc_exec(), "profile", "delete", profile_name])

    run([lxc_exec(), "profile", "create", profile_name])
    assert "" == get_profile_description(profile_name)

    run([lxc_exec(), "profile", "delete", profile_name])


@pytest.mark.requires_lxc
@pytest.mark.parametrize("do_log", [True, False])
def test_write_profile(monkeypatch, do_log):
    profile_text = """
    name: this-is-an-unused-edi-pytest-profile
    description: Some description
    config: {}
    devices: {}
    """

    log_during_run(monkeypatch, do_log)

    profile_name, _ = write_lxc_profile(profile_text)
    assert is_profile_existing(profile_name)
    assert "Some description" == get_profile_description(profile_name)
    run([lxc_exec(), "profile", "delete", profile_name])
    assert not is_profile_existing(profile_name)
