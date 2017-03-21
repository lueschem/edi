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
from edi.lib.helpers import get_edi_plugin_directory, copy_tree
from edi.lib.configurationhelpers import ConfigurationTemplate


def test_configuration_rendering(tmpdir):
    source = os.path.join(get_edi_plugin_directory(), 'config_templates', 'project_tree')
    assert os.path.isdir(source)
    assert not os.listdir(str(tmpdir)) # target should be empty

    copy_tree(source, str(tmpdir))
    template_link = os.path.join(str(tmpdir), 'PROJECTNAME-develop.yml')
    assert os.path.isfile(template_link)
    assert os.path.islink(template_link)

    template = ConfigurationTemplate(str(tmpdir))
    result = template.render({'edi_project_name': 'test-project'})
    print('\n'.join(result))

    assert False