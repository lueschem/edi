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
from contextlib import contextmanager
from edi.lib.helpers import FatalError
from tests.libtesting.optins import requires_lxc
from edi.lib.lxchelpers import (get_server_image_compression_algorithm,
                                get_file_extension_from_image_compression_algorithm,
                                get_lxd_version, LxdVersion)
from edi.lib.shellhelpers import mockablerun
from tests.libtesting.helpers import get_command, get_sub_command
from tests.libtesting.contextmanagers.mocked_executable import mocked_executable, mocked_lxd_version_check


@requires_lxc
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


@requires_lxc
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


@requires_lxc
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
