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

magic_dict = {
    "gz": b'\x1f\x8b\x08',
    "bz2": b'\x42\x5a\x68',
    "xz": b'\xfd\x37\x7a\x58\x5a\x00'
    }

max_len = max(len(magic) for _, magic in magic_dict.items())

def compression_type(filename):
    with open(filename, mode='rb') as f:
        file_start = f.read(max_len)
    for filetype, magic in magic_dict.items():
        print(file_start)
        print(magic)
        if file_start.startswith(magic):
            return filetype
    return "no match"