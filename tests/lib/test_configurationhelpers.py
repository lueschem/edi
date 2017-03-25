# -*- coding: utf-8 -*-
# Copyright (C) 2016 Matthias Luescher
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
from edi.lib.helpers import get_edi_plugin_directory, copy_tree
from edi.lib.configurationhelpers import ConfigurationTemplate
from edi.lib.configurationparser import ConfigurationParser
from edi.lib.helpers import FatalError
from codecs import open


def test_configuration_rendering(tmpdir):
    source = os.path.join(get_edi_plugin_directory(), 'config_templates', 'project_tree')
    assert os.path.isdir(source)
    assert not os.listdir(str(tmpdir)) # target should be empty

    copy_tree(source, str(tmpdir))
    template_link = os.path.join(str(tmpdir), 'PROJECTNAME-develop.yml.edilink')
    assert os.path.isfile(template_link)

    template = ConfigurationTemplate(str(tmpdir))
    result = template.render({'edi_project_name': 'test-project'})
    assert 'PROJECTNAME' not in ''.join(result)
    assert 'plugins/playbooks/sample_playbook/roles/sample_role/tasks/main.yml' in ''.join(result)

    assert not os.path.isfile(template_link)

    test_project_dev = os.path.join(str(tmpdir), 'test-project-develop.yml')
    assert os.path.isfile(test_project_dev)
    assert os.path.islink(test_project_dev)
    gitignore = os.path.join(str(tmpdir), '.gitignore')
    assert os.path.isfile(gitignore)

    with open(test_project_dev, mode='r', encoding='UTF-8') as config_file:
        cp = ConfigurationParser(config_file)
        assert cp.get_bootstrap_architecture() == 'amd64'


def test_configuration_rendering_failure(tmpdir):
    template = ConfigurationTemplate(str(tmpdir))
    with pytest.raises(FatalError) as error:
        template.render({})

    assert 'edi_project_name' in error.value.message
