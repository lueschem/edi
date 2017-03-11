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


from jinja2 import Template
from edi.lib.helpers import get_user
from edi.lib.shellhelpers import get_user_environment_variable
from edi.lib.configurationparser import ConfigurationParser
from edi.lib.sharedfoldercoordinator import SharedFolderCoordinator
from tests.libtesting.fixtures.configfiles import config_files

expected_profile_boilerplates = [
    """
name: privileged
description: Privileged edi lxc container
config:
  security.privileged: "true"
devices: {}
""",
    """
name: shared_folder
config: {}
description: Shared folder for edi lxc container
devices:
  shared_folder_other_folder_for_{{ user }}:
    path: /foo/bar/target_mountpoint
    source: {{ home }}/valid_folder
    type: disk
""",
    """
name: shared_folder
config: {}
description: Shared folder for edi lxc container
devices:
  shared_folder_workspace_for_{{ user }}:
    path: {{ target_home }}/mywork
    source: {{ home }}/work
    type: disk
"""]


def render_expected_profiles():
    user = get_user()
    dict = {'user': get_user(),
            'home': get_user_environment_variable('HOME'),
            'target_home': '/home/{}'.format(user)}
    expected_profiles = []
    for boilerplate in expected_profile_boilerplates:
        template = Template(boilerplate)
        expected_profiles.append(template.render(dict))
    return expected_profiles


def test_pre_config_profiles(config_files):
    expected_profiles = render_expected_profiles()

    with open(config_files, "r") as main_file:
        parser = ConfigurationParser(main_file)

        coordinator = SharedFolderCoordinator(parser)
        profiles = coordinator.get_pre_config_profiles()

        assert len(profiles) == 1

        assert profiles[0] == expected_profiles[0]


def test_post_config_profiles(config_files):
    expected_profiles = render_expected_profiles()

    with open(config_files, "r") as main_file:
        parser = ConfigurationParser(main_file)

        coordinator = SharedFolderCoordinator(parser)
        profiles = coordinator.get_post_config_profiles()

        assert len(profiles) == 3

        for i in range(0, 3):
            assert profiles[i] == expected_profiles[i]
