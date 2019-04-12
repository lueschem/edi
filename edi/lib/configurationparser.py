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

import yaml
import collections
import copy
import hashlib
from jinja2 import Template
import os
from contextlib import contextmanager
from os.path import dirname, abspath, basename, splitext, isfile, join
import logging
from edi.lib.helpers import (get_user, get_user_gid, get_user_uid, get_workdir,
                             get_hostname, get_edi_plugin_directory, FatalError)
from edi.lib.proxyhelpers import ProxySetup
from edi.lib.sshkeyhelpers import get_user_ssh_pub_keys
from edi.lib.versionhelpers import get_edi_version, get_stripped_version
from edi.lib.shellhelpers import get_user_home_directory
from edi.lib.lxchelpers import get_lxd_version
from packaging.version import Version
from edi.lib.urlhelpers import obfuscate_url_password
from edi.lib.yamlhelpers import annotated_yaml_load


def remove_passwords(dictionary):
    obfuscated_dictionary = {}

    url_items = ["edi_host_http_proxy", "edi_host_https_proxy",
                 "edi_host_ftp_proxy", "edi_host_socks_proxy"]

    for key, value in dictionary.items():
        if key in url_items:
            obfuscated_dictionary[key] = obfuscate_url_password(value)
        else:
            obfuscated_dictionary[key] = value

    return obfuscated_dictionary


def get_base_dictionary():
    base_dict = {}
    current_user_name = get_user()
    base_dict["edi_current_user_name"] = current_user_name
    base_dict["edi_current_user_ssh_pub_keys"] = get_user_ssh_pub_keys()
    base_dict["edi_current_user_uid"] = get_user_uid()
    base_dict["edi_current_user_gid"] = get_user_gid()
    base_dict["edi_current_user_host_home_directory"] = get_user_home_directory(current_user_name)
    base_dict["edi_current_user_target_home_directory"] = "/home/{}".format(current_user_name)
    base_dict["edi_host_hostname"] = get_hostname()
    base_dict["edi_edi_plugin_directory"] = get_edi_plugin_directory()
    proxy_setup = ProxySetup()
    base_dict["edi_host_http_proxy"] = proxy_setup.get('http_proxy', default='')
    base_dict["edi_host_https_proxy"] = proxy_setup.get('https_proxy', default='')
    base_dict["edi_host_ftp_proxy"] = proxy_setup.get('ftp_proxy', default='')
    base_dict["edi_host_socks_proxy"] = proxy_setup.get('all_proxy', default='')
    base_dict["edi_host_no_proxy"] = proxy_setup.get('no_proxy', default='')
    base_dict["edi_lxd_version"] = get_lxd_version()
    return base_dict


@contextmanager
def command_context(dictionary):
    backup = copy.deepcopy(ConfigurationParser.command_context)
    ConfigurationParser.command_context.update(dictionary)
    try:
        yield
    finally:
        ConfigurationParser.command_context = backup


class ConfigurationParser:

    # shared data for all configuration parsers
    _configurations = {}

    # use the command_context contextmanager to manage dictionary
    command_context = {
        'edi_create_distributable_image': False,
        'edi_configure_remote_target': False,
    }

    @staticmethod
    def create_distributable_image():
        return ConfigurationParser.command_context.get('edi_create_distributable_image')

    @staticmethod
    def configure_remote_target():
        return ConfigurationParser.command_context.get('edi_configure_remote_target')

    def get_context_suffix(self):
        if self.create_distributable_image():
            return '_di'
        else:
            return ''

    def dump(self):
        return yaml.dump(self._get_config(), default_flow_style=False)

    def get_config(self):
        return self._get_config()

    def get_load_time_dictionary(self):
        return self._get_load_time_dictionary()

    def get_plugins(self, plugin_section):
        result = {}

        plugins = self.get_ordered_path_items(plugin_section)

        if plugins:
            result[plugin_section] = []

        for plugin in plugins:
            name, resolved_path, node_dict, _ = plugin

            plugin_info = {name: {'path': resolved_path, 'dictionary': node_dict}}

            result[plugin_section].append(plugin_info)

        return result

    def get_configuration_name(self):
        return self.config_id

    def get_bootstrap_repository(self):
        return self._get_bootstrap_item("repository", None)

    def get_bootstrap_architecture(self):
        architecture = self._get_bootstrap_item("architecture", None)
        if not architecture:
            raise FatalError('''Missing mandatory element 'architecture' in section 'bootstrap'.''')
        return architecture

    def get_bootstrap_tool(self):
        return self._get_bootstrap_item("tool", "debootstrap")

    def get_bootstrap_repository_key(self):
        return self._get_bootstrap_item("repository_key", None)

    def get_qemu_repository(self):
        return self._get_qemu_item("repository", None)

    def get_qemu_package_name(self):
        return self._get_qemu_item("package", "qemu-user-static")

    def get_qemu_repository_key(self):
        return self._get_qemu_item("repository_key", None)

    def get_compression(self):
        return self._get_general_item("edi_compression", "xz")

    def get_lxc_stop_timeout(self):
        timeout = self._get_general_item("edi_lxc_stop_timeout", 120)
        if type(timeout) != int:
            raise FatalError('''The value of 'edi_lxc_stop_timeout' must be an integer.''')
        return timeout

    def get_general_parameters(self):
        return self._get_general_item("parameters", {})

    def get_ordered_path_items(self, section):
        citems = self._get_config().get(section, {})
        ordered_items = collections.OrderedDict(sorted(citems.items()))
        item_list = []
        for name, content in ordered_items.items():
            if not content.get("skip", False):
                path = content.get("path", None)
                if not path:
                    raise FatalError(("Missing path item in section '{}' for '{}'."
                                      ).format(section, name))
                resolved_path = self._resolve_path(path)
                node_dict = self._get_node_dictionary(content)
                node_dict['edi_current_plugin_directory'] = str(dirname(resolved_path))

                item_list.append((name, resolved_path, node_dict, content))
            else:
                logging.debug("Skipping named item '{}' from section '{}'.".format(name, section))

        return item_list

    def get_ordered_raw_items(self, section):
        citems = self._get_config().get(section, {})
        ordered_items = collections.OrderedDict(sorted(citems.items()))
        item_list = []
        for name, content in ordered_items.items():
            if not content.get("skip", False):
                node_dict = self._get_node_dictionary(content)
                item_list.append((name, content, node_dict))
            else:
                logging.debug("Skipping named item '{}' from section '{}'.".format(name, section))

        return item_list

    def get_project_directory_hash(self):
        return hashlib.sha256(str(self.project_directory).encode()).hexdigest()[:8]

    def get_project_plugin_directory(self):
        return join(self.project_directory, "plugins")

    def __init__(self, base_config_file):
        self.base_config_file = base_config_file
        self.project_directory = dirname(abspath(base_config_file.name))
        self.config_id = splitext(basename(base_config_file.name))[0]
        if not ConfigurationParser._configurations.get(self.config_id):
            logging.info(("Load time dictionary:\n{}"
                          ).format(yaml.dump(remove_passwords(self._get_load_time_dictionary()),
                                             default_flow_style=False)))
            logging.info(("Using base configuration file '{0}'"
                          ).format(base_config_file.name))
            base_config = self._get_base_config(base_config_file)
            global_config = self._get_overlay_config(base_config_file,
                                                     "global")
            hostname = get_hostname()
            system_config = self._get_overlay_config(base_config_file, hostname)
            user = get_user()
            if user == hostname:
                user = '{}.user'.format(user)
                logging.warning(("User name and host name are equal! Going to search user overlay file "
                                 "with '.user' postfix."))
            user_config = self._get_overlay_config(base_config_file, user)

            merge_1 = self._merge_configurations(base_config, global_config)
            merge_2 = self._merge_configurations(merge_1, system_config)
            merged_config = self._merge_configurations(merge_2, user_config)

            ConfigurationParser._configurations[self.config_id] = merged_config
            logging.info("Merged configuration:\n{0}".format(self.dump()))

            self._verify_version_compatibility()

    def get_base_config_file(self):
        """
        Returns the base config file that can be passed in for a next command.
        :return: The base config file
        """
        return self.base_config_file

    def _verify_version_compatibility(self):
        current_version = get_edi_version()
        required_version = str(self._get_general_item('edi_required_minimal_edi_version', current_version))
        if Version(get_stripped_version(current_version)) < Version(get_stripped_version(required_version)):
            raise FatalError(('The current configuration requires a newer version of edi (>={}).\n'
                              'Please update your edi installation!'
                              ).format(get_stripped_version(required_version)))

    def _get_config(self):
        return ConfigurationParser._configurations.get(self.config_id, {})

    def _parse_jina2_file(self, config_file):
        template = Template(config_file.read())
        return template.render(self._get_load_time_dictionary())

    def _get_base_config(self, config_file):
        return annotated_yaml_load(self._parse_jina2_file(config_file), config_file.name) or {}

    def _get_overlay_config(self, base_config_file, overlay_name):
        fname, extension = splitext(basename(base_config_file.name))
        directory = dirname(base_config_file.name)
        overlay_file = "{0}.{1}{2}".format(fname, overlay_name,
                                           extension)
        overlay = join(directory, "configuration", "overlay",
                       overlay_file)
        if isfile(overlay) and os.access(overlay, os.R_OK):
            with open(overlay, encoding="UTF-8", mode="r") as config_file:
                logging.info(("Using overlay configuration file '{0}'"
                              ).format(config_file.name))
                return annotated_yaml_load(self._parse_jina2_file(config_file), config_file.name) or {}
        else:
            return {}

    def _merge_configurations(self, base, overlay):
        merged_config = {}

        elements = ["general", "bootstrap", "qemu"]
        for element in elements:
            merged_config[element
                          ] = self._merge_key_value_node(base, overlay,
                                                         element)

        general_base = base.get("general", {})
        general_overlay = overlay.get("general", {})
        if general_base and general_overlay:
            merged_config["general"]["parameters"] = self._merge_key_value_node(general_base,
                                                                                general_overlay,
                                                                                "parameters")

        nested_elements = ["playbooks", "postprocessing_commands", "lxc_templates",
                           "lxc_profiles", "shared_folders"]
        for element in nested_elements:
            merged_config[element
                          ] = self._merge_nested_node(base, overlay,
                                                      element)
        return merged_config

    @staticmethod
    def _merge_key_value_node(base, overlay, node_name):
        base_node = base.get(node_name, {})
        overlay_node = overlay.get(node_name, {})
        if base_node is None and overlay_node is None:
            return {}
        if base_node is None:
            return overlay_node
        if overlay_node is None:
            return base_node
        return dict(base_node, **overlay_node)

    def _merge_nested_node(self, base, overlay, node):
        merged_node = self._merge_key_value_node(base, overlay,
                                                 node)

        for key, _ in merged_node.items():
            base_node = base.get(node, {})
            overlay_node = overlay.get(node, {})
            merged_node[key] = self._merge_key_value_node(base_node,
                                                          overlay_node,
                                                          key)

            for element in ["parameters", "output"]:
                base_items = base_node.get(key, {})
                overlay_items = overlay_node.get(key, {})
                merged_items = self._merge_key_value_node(base_items,
                                                          overlay_items,
                                                          element)
                if merged_items:
                    merged_node[key][element] = merged_items

        return merged_node

    def _get_bootstrap_item(self, item, default):
        return self._get_config().get("bootstrap", {}
                                      ).get(item, default)

    def _get_qemu_item(self, item, default):
        return self._get_config().get("qemu", {}
                                      ).get(item, default)

    def _get_general_item(self, item, default):
        return self._get_config().get("general", {}
                                      ).get(item, default)

    def _get_load_time_dictionary(self):
        load_dict = get_base_dictionary()
        load_dict["edi_work_directory"] = get_workdir()
        load_dict["edi_project_directory"] = self.project_directory
        load_dict["edi_project_plugin_directory"] = self.get_project_plugin_directory()
        load_dict['edi_log_level'] = logging.getLevelName(logging.getLogger().getEffectiveLevel())
        load_dict['edi_configuration_name'] = self.get_configuration_name()
        load_dict.update(ConfigurationParser.command_context)
        return load_dict

    def _get_node_dictionary(self, node):
        node_dict = self._get_load_time_dictionary()

        node_dict["edi_lxc_network_interface_name"] = self._get_general_item("edi_lxc_network_interface_name",
                                                                             "lxcif0")
        node_dict["edi_config_management_user_name"] = self._get_general_item("edi_config_management_user_name",
                                                                              "edicfgmgmt")
        node_dict['edi_bootstrap_architecture'] = self.get_bootstrap_architecture()

        general_parameters = self.get_general_parameters()
        if general_parameters:
            node_dict = dict(node_dict, **general_parameters)

        parameters = node.get("parameters", None)

        if parameters:
            return dict(node_dict, **parameters)

        return node_dict

    def _resolve_path(self, path):
        if os.path.isabs(path):
            if not os.path.isfile(path):
                raise FatalError(("'{}' does not exist."
                                  ).format(path))
            return path
        else:
            locations = [self.get_project_plugin_directory(), get_edi_plugin_directory()]

            for location in locations:
                abspath = os.path.join(location, path)
                if os.path.isfile(abspath):
                    return abspath

            raise FatalError(("'{0}' not found in the "
                              "following locations:\n{1}"
                              ).format(path, "\n".join(locations)))
