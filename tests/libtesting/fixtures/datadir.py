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

from pytest import fixture
import os
from edi.lib.helpers import copy_tree


@fixture
def datadir(tmpdir, request):
    '''
    Move data from tests/data/TESTNAME into a temporary directory
    so that the test can modify its data set.
    '''
    test_subdir = os.path.basename(os.path.splitext(request.module.__file__)[0])
    test_data = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                             '..', '..', 'data', test_subdir))

    if os.path.isdir(test_data):
        copy_tree(str(test_data), str(tmpdir))

    return tmpdir