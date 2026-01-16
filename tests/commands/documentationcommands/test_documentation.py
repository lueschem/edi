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

import os
import pytest
import edi
from filecmp import cmp
from edi.commands.documentationcommands.render import Render
from edi.lib.helpers import FatalError
from edi.lib.shellhelpers import run
from edi.lib.buildahhelpers import buildah_exec
from tests.libtesting.helpers import get_project_root


@pytest.mark.filterwarnings("ignore:Unexpected line")
@pytest.mark.filterwarnings("ignore:Found eof")
def test_documentation_all(datadir):
    parser = edi._setup_command_line_interface()
    raw_input = os.path.join(str(datadir), 'raw_input')
    cli_args = parser.parse_args(['--log', 'WARNING', 'documentation', 'render', raw_input, str(datadir),
                                  os.path.join(str(datadir), 'all.yml')])

    Render().run_cli(cli_args)

    output_files = ['changelog.rst', 'index.rst', 'setup.rst', 'versions.rst']

    for file in output_files:
        generated = os.path.join(str(datadir), file)
        reference = os.path.join(str(datadir), 'expected', 'all', file)
        assert os.path.isfile(generated)
        assert cmp(generated, reference)

    with pytest.raises(FatalError) as error:
        Render().run_cli(cli_args)

    assert 'already exists' in error.value.message

    cli_args = parser.parse_args(['documentation', 'render', '--clean', raw_input, str(datadir),
                                  os.path.join(str(datadir), 'all.yml')])

    Render().run_cli(cli_args)

    for file in output_files:
        generated = os.path.join(str(datadir), file)
        assert not os.path.isfile(generated)


@pytest.mark.filterwarnings("ignore:Unexpected line")
@pytest.mark.filterwarnings("ignore:Found eof")
@pytest.mark.requires_buildah
def test_documentation_in_user_namespace(datadir):
    changelog_file = os.path.join(str(datadir), 'changelog.rst')
    assert not os.path.isfile(changelog_file)
    edi_exec = os.path.join(get_project_root(), 'bin', 'edi')
    raw_input = os.path.join(str(datadir), 'raw_input')
    cmd = [buildah_exec(), 'unshare', '--', edi_exec, 'documentation', 'render', raw_input, str(datadir),
           os.path.join(str(datadir), 'all.yml')]
    run(cmd)
    assert os.path.isfile(changelog_file)
