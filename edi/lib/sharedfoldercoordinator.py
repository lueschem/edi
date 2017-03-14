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


from jinja2 import Template
from edi.lib.helpers import FatalError
from edi.lib.shellhelpers import run


profile_privileged = """
name: privileged
description: Privileged edi lxc container
config:
  security.privileged: "true"
devices: {}
"""


profile_shared_folder = """
name: shared_folder
config: {}
description: Shared folder for edi lxc container
devices:
  shared_folder_{{ shared_folder_name }}_for_{{ edi_current_user_name }}:
    path: {{ edi_current_user_target_home_directory }}/{{ shared_folder_mountpoint }}
    source: {{ edi_current_user_host_home_directory }}/{{ shared_folder_folder }}
    type: disk
"""


class SharedFolderCoordinator():

    def __init__(self, config):
        self._config = config

    def create_host_folders(self):
        """
        Make sure that all configured shared folders exist on the host system.
        If a folder is missing, create it!
        """
        pass

    def verify_container_mountpoints(self, container_name):
        """
        Verify that all mount points exist within the target system.
        If a target mount point is missing, raise a fatal error.
        Hint: It is assumed that the mount points within the target get created during the configuration phase.
        """
        test_cmd = ['lxc', 'exec', container_name, '--', 'true']
        if run(test_cmd, check=False).returncode != 0:
            raise FatalError('''Failed to communicate with container '{}'.'''.format(container_name))

        mountpoints = self.get_mountpoints()
        for mountpoint in mountpoints:
            cmd = ['lxc', 'exec', container_name, '--', 'test', '-d', mountpoint]
            if run(cmd, check=False).returncode != 0:
                raise FatalError(('''Please make sure that '{}' is valid mount point in the container '{}'.\n'''
                                  '''Hint: Use an appropriate playbook that generates those mount points\n'''
                                  '''      by using the variable 'edi_shared_folder_mountpoints'.''')
                                 .format(mountpoint, container_name))

    def get_mountpoints(self):
        """
        Get a list of mount points.
        :return: a list of mountpoints
        """
        return self._get_folder_list('edi_current_user_target_home_directory', 'mountpoint')

    def get_pre_config_profiles(self):
        """
        Creates all profiles that can be applied prior to the configuration of the target.
        :return: list of profiles
        """
        if self._config.get_ordered_raw_items('shared_folders'):
            return [Template(profile_privileged).render({})]
        else:
            return []

    def get_post_config_profiles(self):
        """
        Creates all profiles that can be applied after the configuration of the target.
        :return: list of profiles
        """
        shared_folders = self._config.get_ordered_raw_items('shared_folders')
        if shared_folders:
            profiles = [Template(profile_privileged).render({})]
            template = Template(profile_shared_folder)
            for name, content, dict in shared_folders:
                for item in ['folder', 'mountpoint']:
                    dict['shared_folder_{}'.format(item)] = self._get_mandatory_item(name, content, item)
                dict['shared_folder_name'] = name
                profiles.append(template.render(dict))

            return profiles
        else:
            return []

    @staticmethod
    def _get_mandatory_item(folder_name, folder_config, item):
        result = folder_config.get(item, None)
        if '/' in result:
            raise FatalError(('''The item '{}' in shared folder '{}' must not contain sub folders.'''
                              ).format(item, folder_name))
        if not result:
            raise FatalError('''Missing mandatory item '{}' in shared folder '{}'.'''.format(item, folder_name))
        return result

    def _get_folder_list(self, homedir, item):
        shared_folders = self._config.get_ordered_raw_items('shared_folders')
        result = []
        for name, content, dict in shared_folders:
            folder = '{}/{}'.format(dict[homedir],
                                    self._get_mandatory_item(name, content, item))
            result.append(folder)
        return result
