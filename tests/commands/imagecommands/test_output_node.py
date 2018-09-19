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
import yaml
from edi.commands.imagecommands.create import Create
import edi


def test_output_node(datadir, capsys):
    parser = edi._setup_command_line_interface()
    # without overlay
    cli_args = parser.parse_args(['image', 'create', '--config', os.path.join(str(datadir), 'output-node-base.yml')])
    Create().run_cli(cli_args)
    out, err = capsys.readouterr()
    config = yaml.load(out)
    second_command = config.get('postprocessing_commands').get('120_second_command')
    assert second_command.get('output').get('output1') == 'foo.result'
    assert second_command.get('output').get('output2') == 'bar.result'
    assert second_command.get('parameters').get('bingo') == 'bongo'
    assert second_command.get('parameters').get('message') == 'Foo, bar or baz?'
    assert second_command.get('path') == 'postprocessing_commands/sample_command/some_command'
    assert not err or 'is shallow and may cause errors' in err

    # with overlay
    cli_args = parser.parse_args(['image', 'create', '--config', os.path.join(str(datadir), 'output-node.yml')])
    Create().run_cli(cli_args)
    out, err = capsys.readouterr()
    config = yaml.load(out)
    second_command = config.get('postprocessing_commands').get('120_second_command')
    assert second_command.get('output').get('output1') == 'foo.result'
    assert second_command.get('output').get('output2') == 'baz.result'
    assert second_command.get('parameters').get('bingo') == 'bongo'
    assert second_command.get('parameters').get('message') == 'Foo and baz!'
    assert second_command.get('path') == 'postprocessing_commands/sample_command/custom_command'
    assert not err or 'is shallow and may cause errors' in err
