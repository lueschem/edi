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
from edi.lib.shellhelpers import run, require
from edi.lib.lxchelpers import lxc_exec, lxd_install_hint, LxdVersion
import os
import logging
import subprocess
from edi.lib.yamlhelpers import normalize_yaml


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
        if self._suppress_shared_folders():
            return

        host_folders = self._get_folder_list('edi_current_user_host_home_directory', 'folder')
        for folder in host_folders:
            if os.path.exists(folder):
                if not os.path.isdir(folder):
                    raise FatalError('''The location '{}' does '''
                                     '''exist on the host system but it is not a folder that '''
                                     '''can be shared to a container.'''.format(folder))

                else:
                    logging.debug(('''The shared folder '{}' on the host system has already been created.'''
                                   ).format(folder))
            else:
                cmd = ['mkdir', '-p', folder]
                # Use the current user (not root) to create the folder!
                result = run(cmd, check=False, stderr=subprocess.PIPE)
                if result.returncode != 0:
                    raise FatalError(('''The creation of the folder '{}' failed with the message '{}'.'''
                                      ).format(folder, result.stderr))
                else:
                    logging.debug(('''Successfully created the shared folder '{}' on the host system.'''
                                   ).format(folder))

    @require('lxc', lxd_install_hint, LxdVersion.check)
    def verify_container_mountpoints(self, container_name):
        """
        Verify that all mount points exist within the target system.
        If a target mount point is missing, raise a fatal error.
        Hint: It is assumed that the mount points within the target get created during the configuration phase.
        """
        if self._suppress_shared_folders():
            return

        test_cmd = [lxc_exec(), 'exec', container_name, '--', 'true']
        result = run(test_cmd, check=False, stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise FatalError(('''The communication with the container '{}' failed with the message '{}'.'''
                              ).format(container_name, result.stderr))

        mountpoints = self.get_mountpoints()
        for mountpoint in mountpoints:
            cmd = [lxc_exec(), 'exec', container_name, '--', 'test', '-d', mountpoint]
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
        if self._suppress_shared_folders():
            return []

        return self._get_folder_list('edi_current_user_target_home_directory', 'mountpoint')

    def get_pre_config_profiles(self):
        """
        Creates all profiles that can be applied prior to the configuration of the target.
        :return: list of profiles
        """
        if self._suppress_shared_folders():
            return []

        if self._config.get_ordered_raw_items('shared_folders'):
            return [(normalize_yaml(Template(profile_privileged).render({})), 'zzz_privileged', 'builtin', {})]
        else:
            return []

    def get_post_config_profiles(self):
        """
        Creates all profiles that can be applied after the configuration of the target.
        :return: list of profiles
        """
        if self._suppress_shared_folders():
            return []

        shared_folders = self._config.get_ordered_raw_items('shared_folders')
        if shared_folders:
            profiles = self.get_pre_config_profiles()
            template = Template(profile_shared_folder)
            for name, content, node_dict in shared_folders:
                for item in ['folder', 'mountpoint']:
                    node_dict['shared_folder_{}'.format(item)] = self._get_mandatory_item(name, content, item)
                node_dict['shared_folder_name'] = name
                profiles.append((normalize_yaml(template.render(node_dict)),
                                 'zzz_{}'.format(name), 'builtin', node_dict))

            return profiles
        else:
            return []

    def _suppress_shared_folders(self):
        # Do not create shared folders for a distributable image.
        return self._config.create_distributable_image() or self._config.configure_remote_target()

    @staticmethod
    def _get_mandatory_item(folder_name, folder_config, item):
        result = folder_config.get(item, None)

        if not result:
            raise FatalError('''Missing mandatory item '{}' in shared folder '{}'.'''.format(item, folder_name))

        if '/' in result:
            raise FatalError(('''The item '{}' in shared folder '{}' must not contain sub folders.'''
                              ).format(item, folder_name))

        return result

    def _get_folder_list(self, homedir, item):
        shared_folders = self._config.get_ordered_raw_items('shared_folders')
        result = []
        for name, content, node_dict in shared_folders:
            folder = '{}/{}'.format(node_dict[homedir],
                                    self._get_mandatory_item(name, content, item))
            result.append(folder)
        return result
