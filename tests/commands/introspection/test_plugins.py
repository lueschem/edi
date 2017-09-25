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

from tests.libtesting.fixtures.configfiles import config_files
from edi.commands.lxccommands.lxcconfigure import Configure
import edi
import yaml
import os


def test_dictionary(config_files, capsys):
    parser = edi._setup_command_line_interface()
    cli_args = parser.parse_args(['lxc', 'configure', '--plugins', 'cname', config_files])

    Configure().run_cli(cli_args)
    out, err = capsys.readouterr()

    assert err == ''
    result = yaml.load(out)
    assert len(result.get('playbooks')) == 3
    base_system = result.get('playbooks')[0].get('10_base_system')
    assert 'plugins/playbooks/foo.yml' in base_system.get('path')
    assert base_system.get('dictionary').get('kernel_package') == 'linux-image-amd64-rt'
    assert base_system.get('dictionary').get('edi_config_directory') == os.path.dirname(config_files)
