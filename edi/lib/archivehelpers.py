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

import zlib
import bz2
import lzma
from functools import partial
from edi.lib.helpers import FatalError


def _gz_decompress(data):
    return zlib.decompress(data, 16+zlib.MAX_WBITS)


decompressor_from_magic = [
    (b'\x1f\x8b\x08', partial(_gz_decompress)), # gz
    (b'\x42\x5a\x68', partial(bz2.decompress)), # bz2
    (b'\xfd\x37\x7a\x58\x5a\x00', partial(lzma.decompress)), # xz
    ]


def decompress(data):
    for item in decompressor_from_magic:
        if data.startswith(item[0]):
            return item[1](data)
    raise FatalError("Unknown compression type!")
