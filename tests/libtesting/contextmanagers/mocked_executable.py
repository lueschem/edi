# -*- coding: utf-8 -*-
# Copyright (C) 2018 Matthias Luescher
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
from contextlib import contextmanager
from edi.lib.shellhelpers import Executables


@contextmanager
def mocked_executable(executable, mock=str(os.path.join(os.sep, 'bin', 'true'))):
    """
    Mocks away an executable that gets fetched using the Executables class.
    :param executable: The executable to be mocked.
    :param mock: The replacement for the mocked executable.
    :return: The mock.
    """
    Executables._cache[executable] = mock

    try:
        yield mock
    finally:
        del Executables._cache[executable]
