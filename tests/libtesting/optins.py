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


import pytest
import os


requires_lxc = pytest.mark.skipif(
    not (pytest.config.getoption("--lxc") or pytest.config.getoption("--all")),
    reason="requires --lxc option to run"
)


requires_ansible = pytest.mark.skipif(
    not (pytest.config.getoption("--ansible") or pytest.config.getoption("--all")),
    reason="requires --ansible option to run"
)


requires_debootstrap = pytest.mark.skipif(
    not (pytest.config.getoption("--debootstrap") or pytest.config.getoption("--all")),
    reason="requires --debootstrap option to run"
)


requires_sudo = pytest.mark.skipif(
    os.getuid() != 0,
    reason="requires sudo privileges to run"
)
