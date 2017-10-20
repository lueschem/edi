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

from edi.commands.lxccommands.lxcconfigure import Configure
import edi
import yaml


def test_config(config_files, capsys):
    # TODO: apply to all introspection aware commands
    parser = edi._setup_command_line_interface()
    cli_args = parser.parse_args(['lxc', 'configure', '--config', 'cname', config_files])

    Configure().run_cli(cli_args)
    out, err = capsys.readouterr()

    assert err == ''
    merged_config = yaml.load(out)
    assert merged_config.get('bootstrap').get('architecture') == 'i386'
