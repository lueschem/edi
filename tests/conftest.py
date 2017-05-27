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


def pytest_addoption(parser):
    parser.addoption("--all", action="store_true",
                     help="include all tests - even those that rely on lxc, ansible, ...")
    parser.addoption("--lxc", action="store_true",
                     help="include tests that rely on lxc availability")
    parser.addoption("--ansible", action="store_true",
                     help="include tests that rely on ansible availability")
    parser.addoption("--debootstrap", action="store_true",
                     help="include tests that rely on debootstrap availability")
