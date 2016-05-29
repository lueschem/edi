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
import collections
from jinja2 import Template
import os
from os.path import dirname, abspath, basename, splitext, isfile, join
import logging
from aptsources.sourceslist import SourceEntry
from edi.lib.helpers import (get_user, get_user_gid, get_user_uid,
                             get_hostname, print_error_and_exit)


class ConfigurationParser():

    # shared data for all configuration parsers
    _configurations = {}

    def dump(self):
        return yaml.dump(self._get_config(), default_flow_style=False)

    def get_project_name(self):
        return self.config_id

    def get_workdir(self):
        # we might want to overwrite it by a config setting
        return os.getcwd()

    def get_distribution(self):
        repository = self._get_bootstrap_item("repository", "")
        return SourceEntry(repository).dist

    def get_architecture(self):
        return self._get_bootstrap_item("architecture", None)

    def get_bootstrap_tool(self):
        return self._get_bootstrap_item("tool", "debootstrap")

    def get_bootstrap_uri(self):
        repository = self._get_bootstrap_item("repository", "")
        return SourceEntry(repository).uri

    def get_bootstrap_repository_key(self):
        return self._get_bootstrap_item("repository_key", None)

    def get_bootstrap_components(self):
        repository = self._get_bootstrap_item("repository", "")
        return SourceEntry(repository).comps

    def get_use_case(self):
        return self._get_global_configuration_item("use_case", "edi_run")

    def get_compression(self):
        return self._get_global_configuration_item("compression", "xz")

    def get_playbooks(self):
        playbooks = self._get_config().get("playbooks", {})
        return collections.OrderedDict(sorted(playbooks.items()))

    def get_edi_plugin_directory(self):
        return abspath(join(dirname(__file__), "../plugins"))

    def get_project_plugin_directory(self):
        return join(self.config_directory, "plugins")

    def __init__(self, base_config_file, running_in_chroot=False):
        self.running_in_chroot = running_in_chroot
        self.config_directory = dirname(abspath(base_config_file.name))
        self.config_id = splitext(basename(base_config_file.name))[0]
        if not ConfigurationParser._configurations.get(self.config_id):
            logging.info(("Using base configuration file '{0}'"
                          ).format(base_config_file.name))
            base_config = self._get_base_config(base_config_file)
            all_config = self._get_overlay_config(base_config_file, "all")
            host_config = self._get_overlay_config(base_config_file,
                                                   get_hostname())
            user_config = self._get_overlay_config(base_config_file,
                                                   get_user())

            merge_1 = self._merge_configurations(base_config, all_config)
            merge_2 = self._merge_configurations(merge_1, host_config)
            merged_config = self._merge_configurations(merge_2, user_config)

            ConfigurationParser._configurations[self.config_id] = merged_config
            logging.info("Merged configuration:\n{0}".format(self.dump()))

    def _get_config(self):
        return ConfigurationParser._configurations.get(self.config_id, {})

    def _parse_jina2_file(self, config_file):
        template = Template(config_file.read())
        return template.render(self._get_jinja2_dictionary())

    def _get_base_config(self, config_file):
        return yaml.load(self._parse_jina2_file(config_file))

    def _get_overlay_config(self, base_config_file, overlay_name):
        filename, file_extension = splitext(base_config_file.name)
        fn = "{0}.{1}{2}".format(filename, overlay_name, file_extension)
        if isfile(fn) and os.access(fn, os.R_OK):
            with open(fn, encoding="UTF-8", mode="r") as config_file:
                logging.info(("Using overlay configuration file '{0}'"
                              ).format(config_file.name))
                return yaml.load(self._parse_jina2_file(config_file))
        else:
            return {}

    def _merge_configurations(self, base, overlay):
        merged_config = {}

        elements = ["global_configuration", "bootstrap"]
        for element in elements:
            merged_config[element
                          ] = self._merge_key_value_node(base, overlay,
                                                         element)

        nested_elements = ["playbooks", "keys"]
        for element in nested_elements:
            merged_config[element
                          ] = self._merge_nested_node(base, overlay,
                                                      element)
        return merged_config

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

    def _merge_nested_node(self, base, overlay, node):
        merged_node = self._merge_key_value_node(base, overlay,
                                                 node)

        for key, _ in merged_node.items():
            base_node = base.get(node, {})
            overlay_node = overlay.get(node, {})
            merged_node[key] = self._merge_key_value_node(base_node,
                                                          overlay_node,
                                                          key)

            element = "parameters"
            base_params = base_node.get(key, {})
            overlay_params = overlay_node.get(key, {})
            merged_params = self._merge_key_value_node(base_params,
                                                       overlay_params,
                                                       element)
            if merged_params:
                merged_node[key][element] = merged_params

        return merged_node

    def _get_bootstrap_item(self, item, default):
        return self._get_config().get("bootstrap", {}
                                      ).get(item, default)

    def _get_global_configuration_item(self, item, default):
        return self._get_config().get("global_configuration", {}
                                      ).get(item, default)

    def _get_jinja2_dictionary(self):
        jinja2_dict = {}
        jinja2_dict["edi_current_user_name"] = get_user()
        jinja2_dict["edi_current_user_uid"] = get_user_uid()
        jinja2_dict["edi_current_user_gid"] = get_user_gid()
        jinja2_dict["edi_host_hostname"] = get_hostname()
        jinja2_dict["edi_running_in_chroot"] = str(self.running_in_chroot)
        jinja2_dict["edi_work_directory"] = self.get_workdir()
        jinja2_dict["edi_config_directory"] = self.config_directory
        jinja2_dict["edi_edi_plugin_directory"
                    ] = self.get_edi_plugin_directory()
        jinja2_dict["edi_project_plugin_directory"
                    ] = self.get_project_plugin_directory()
        logging.info("Jinja2 dictionary:\n{}".format(jinja2_dict))
        return jinja2_dict
