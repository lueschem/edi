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
from tests.libtesting.optins import requires_lxc
from edi.lib.lxchelpers import get_server_image_compression_algorithm
from edi.lib.shellhelpers import mockablerun
from tests.libtesting.helpers import get_command, get_sub_command


@requires_lxc
def test_get_server_image_compression():
    result = get_server_image_compression_algorithm()
    assert result in ['bzip2', 'gzip', 'lzma', 'xz', 'none']


def test_get_server_image_compression_bzip2(monkeypatch):
    def fake_lxc_config_command(*popenargs, **kwargs):
        if get_command(popenargs) == 'lxc' and get_sub_command(popenargs) == 'config':
            return subprocess.CompletedProcess("fakerun", 0, stdout='bzip2')
        else:
            return subprocess.run(*popenargs, **kwargs)

    monkeypatch.setattr(mockablerun, 'run_mockable', fake_lxc_config_command)
    result = get_server_image_compression_algorithm()
    assert result is 'bzip2'
