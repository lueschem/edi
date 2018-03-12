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

import pytest
from edi.lib.archivehelpers import decompress


@pytest.mark.parametrize('algorithm, compressed_data', [
    ('bz2', (b'BZh91AY&SY\xa9t*,\x00\x00\x01\xd9\x80\x00\x10\x00\x02\x10\x00\x13$\x00\x10 \x00"\x06'
             b'\x9a=B\x0c\x98\x8cB\x1f\x07\x8b\xb9"\x9c(HT\xba\x15\x16\x00')),
    ('gz', (b'\x1f\x8b\x08\x08G\x1d\xa2X\x00\x03gz-file\x00K\xaf\xd2M\xcb\xccI\xe5\x02\x00\x9a\x91'
            b'\xe8\xa5\x08\x00\x00\x00')),
    ('xz', (b'\xfd7zXZ\x00\x00\x04\xe6\xd6\xb4F\x02\x00!\x01\x16\x00\x00\x00t/\xe5\xa3\x01\x00\x07'
            b'xz-file\n\x00a\xb8\xbd\x0c\x91\xea\xb0F\x00\x01 \x08\xbb\x19\xd9\xbb\x1f\xb6\xf3}\x01'
            b'\x00\x00\x00\x00\x04YZ')),
    ('zstd', b'(\xb5/\xfd$\nQ\x00\x00zstd-file\n^;\x1b\xc7')
])
def test_decompression(algorithm, compressed_data):
    expected_data = '{0}-file\n'.format(algorithm)
    data = decompress(compressed_data).decode('utf-8')
    assert data == expected_data
