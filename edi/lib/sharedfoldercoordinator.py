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
  shared_folder_{{ shared_folder_name }}_for_{{ "edi_current_user_name" }}:
    path: {{ edi_current_user_target_home_directory }}/{{ shared_folder_mountpoint }}
    source: {{ edi_current_user_host_home_directory }}/{{ shared_folder_folder }}
    type: disk
"""


class SharedFolderCoordinator():

    def __init__(self, config):
        self.config = config

    def create_host_folders(self):
        """
        Make sure that all configured shared folders exist on the host system.
        If a folder is missing, create it!
        """
        pass

    def verify_target_mountpoints(self):
        """
        Verify that all mount points exist within the target system.
        If a target mount point is missing, raise a fatal error.
        Hint: It is assumed that the mount points within the target get created during the configuration phase.
        """
        pass

    def get_pre_config_profiles(self):
        """
        Creates all profiles that can be applied prior to the configuration of the target.
        :return: list of profiles
        """
        pass

    def get_post_config_profiles(self):
        """
        Creates all profiles that can be applied after the configuration of the target.
        :return: list of profiles
        """
        pass
