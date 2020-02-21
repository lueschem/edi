# -*- coding: utf-8 -*-
# Copyright (C) 2020 Matthias Luescher
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


from tests.libtesting.contextmanagers.workspace import workspace
from edi.commands.clean import Clean
from tests.libtesting.helpers import suppress_chown_during_debuild
import pytest


@pytest.mark.requires_lxc
def test_clean_empty_config(empty_config_file, monkeypatch):
    suppress_chown_during_debuild(monkeypatch)
    with workspace():
        with open(empty_config_file, "r") as main_file:
            clean_cmd = Clean()
            clean_cmd.run(main_file)
