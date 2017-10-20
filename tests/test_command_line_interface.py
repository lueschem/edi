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

import edi


def test_command_line_interface_setup(empty_config_file):
    parser = edi._setup_command_line_interface()
    assert 'embedded development infrastructure' in parser.description
    args = parser.parse_args(['-v', 'lxc', 'configure', 'some-container', empty_config_file])
    assert args.command_name == 'lxc'
    assert str(args.config_file.name) == str(empty_config_file)
    assert args.container_name == 'some-container'
    assert args.sub_command_name == 'configure'
    assert args.verbose is True
