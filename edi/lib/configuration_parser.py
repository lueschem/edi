# -*- coding: utf-8 -*-
# Copyright (C) 2016 Matthias Luescher
#
# Authors:
#  Matthias Luescher
#
# This file is part of edi.
#
# edi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# edi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with edi.  If not, see <http://www.gnu.org/licenses/>.

import yaml
from edi.lib.helpers import get_user, get_hostname
import os
import logging


class ConfigurationParser():

    def __init__(self, base_config_file):
        logging.info(("Using base configuration file '{0}'"
                      ).format(base_config_file.name))
        base_config = yaml.load(base_config_file.read())
        host_config = self.get_overlay_config(base_config_file, get_hostname())
        user_config = self.get_overlay_config(base_config_file, get_user())

        tmp_merge = self.merge_configurations(base_config, host_config)
        self.config = self.merge_configurations(tmp_merge, user_config)

    def get_overlay_config(self, base_config_file, overlay_name):
        filename, file_extension = os.path.splitext(base_config_file.name)
        fn = "{0}.{1}{2}".format(filename, overlay_name, file_extension)
        if os.path.isfile(fn) and os.access(fn, os.R_OK):
            with open(fn, encoding="UTF-8", mode="r") as config_file:
                logging.info(("Using overlay configuration file '{0}'"
                              ).format(config_file.name))
                return yaml.load(config_file.read())
        else:
            return {}

    def dump(self):
        print(yaml.dump(self.config, default_flow_style=False))

    def merge_configurations(self, base, overlay):
        merged_configuration = {}
        merged_configuration["global_config"
                             ] = self.merge_key_value_node(base, overlay,
                                                           "global_config")
        merged_configuration["bootstrap_stage"
                             ] = self.merge_key_value_node(base, overlay,
                                                           "bootstrap_stage")
        merged_configuration["configuration_stage"
                             ] = self.merge_configuration_stage(base, overlay)
        return merged_configuration

    def merge_key_value_node(self, base, overlay, node_name):
        return dict(base.get(node_name, {}),
                    **overlay.get(node_name, {}))

    def merge_configuration_stage(self, base, overlay):
        if "configuration_stage" in overlay:
            base_dict = {}
            for playbook in base.get("configuration_stage", []):
                base_dict[playbook.get("identifier", "missing identifier")
                          ] = playbook

            merged_list = []
            for playbook in overlay.get("configuration_stage", []):
                identifier = playbook.get("identifier",
                                          "missing overlay identifier")
                base_playbook = base_dict.get(identifier, None)
                merged_playbook = dict(base_playbook, **playbook)
                merged_list.append(merged_playbook)

            return merged_list
        else:
            return base.get("configuration_stage", {})
