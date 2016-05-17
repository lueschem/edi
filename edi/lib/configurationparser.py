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
from edi.lib.helpers import get_user, get_hostname, print_error_and_exit
import os
import logging
from aptsources.sourceslist import SourceEntry


class ConfigurationParser():

    # shared data for all configuration parsers
    _configurations = {}

    def dump(self):
        return yaml.dump(self._get_config(), default_flow_style=False)

    def get_workdir(self):
        # we might want to overwrite it by a config setting
        return os.getcwd()

    def get_distribution(self):
        repository = self._get_bootstrap_stage_item("repository", "")
        return SourceEntry(repository).dist

    def get_architecture(self):
        return self._get_bootstrap_stage_item("architecture", None)

    def get_bootstrap_uri(self):
        repository = self._get_bootstrap_stage_item("repository", "")
        return SourceEntry(repository).uri

    def get_bootstrap_repository_key(self):
        return self._get_bootstrap_stage_item("repository_key", None)

    def get_bootstrap_compontents(self):
        repository = self._get_bootstrap_stage_item("repository", "")
        return SourceEntry(repository).comps

    def get_use_case(self):
        return self._get_global_configuration_item("use_case", "edi_run")

    def __init__(self, base_config_file):
        self.config_id = base_config_file.name
        if not ConfigurationParser._configurations.get(self.config_id):
            logging.info(("Using base configuration file '{0}'"
                          ).format(base_config_file.name))
            base_config = yaml.load(base_config_file.read())
            host_config = self._get_overlay_config(base_config_file,
                                                   get_hostname())
            user_config = self._get_overlay_config(base_config_file,
                                                   get_user())

            tmp_merge = self._merge_configurations(base_config, host_config)

            merged_config = self._merge_configurations(tmp_merge, user_config)
            ConfigurationParser._configurations[self.config_id] = merged_config
            logging.info("Merged configuration:\n{0}".format(self.dump()))

    def _get_config(self):
        return ConfigurationParser._configurations.get(self.config_id, {})

    def _get_overlay_config(self, base_config_file, overlay_name):
        filename, file_extension = os.path.splitext(base_config_file.name)
        fn = "{0}.{1}{2}".format(filename, overlay_name, file_extension)
        if os.path.isfile(fn) and os.access(fn, os.R_OK):
            with open(fn, encoding="UTF-8", mode="r") as config_file:
                logging.info(("Using overlay configuration file '{0}'"
                              ).format(config_file.name))
                return yaml.load(config_file.read())
        else:
            return {}

    def _merge_configurations(self, base, overlay):
        merged_configuration = {}

        elements = ["global_configuration", "bootstrap_stage"]
        for element in elements:
            merged_configuration[element
                                 ] = self._merge_key_value_node(base, overlay,
                                                                element)

        merged_configuration["configuration_stage"
                             ] = self._merge_configuration_stage(base, overlay)
        return merged_configuration

    def _merge_key_value_node(self, base, overlay, node_name):
        base_node = base.get(node_name, {})
        overlay_node = overlay.get(node_name, {})
        if base_node is None and overlay_node is None:
            return {}
        if base_node is None:
            return overlay_node
        if overlay_node is None:
            return base_node
        return dict(base_node, **overlay_node)

    def _get_identifier(self, element):
        identifier = element.get("identifier", None)
        if identifier is None:
            print_error_and_exit(("Missing identifier for "
                                  "element:\n'{}'"
                                  ).format(element))
        return identifier

    def _merge_configuration_stage(self, base, overlay):
        merged_list = []

        if "configuration_stage" in overlay:
            overlay_list = overlay.get("configuration_stage", [])

            if overlay_list:
                base_dict = {}
                for element in base.get("configuration_stage", []):
                    base_dict[self._get_identifier(element)] = element

                for element in overlay_list:
                    identifier = self._get_identifier(element)
                    base_element = base_dict.get(identifier, {})
                    if base_element:
                        del base_dict[identifier]
                    merged_element = dict(base_element, **element)
                    merged_params = self._merge_key_value_node(base_element,
                                                               element,
                                                               "parameters")
                    if merged_params:
                        merged_element["parameters"] = merged_params
                    merged_list.append(merged_element)

                for _, element in base_dict.items():
                    logging.warning(("Overlay configuration does not use the "
                                     "following configuration stage "
                                     "element:\n{0}").format(element))

        if merged_list:
            return merged_list
        else:
            return base.get("configuration_stage", [])

    def _get_bootstrap_stage_item(self, item, default):
        return self._get_config().get("bootstrap_stage", {}
                                      ).get(item, default)

    def _get_global_configuration_item(self, item, default):
        return self._get_config().get("global_configuration", {}
                                      ).get(item, default)
