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


from edi.commands.config import Config
from edi.lib.sharedfoldercoordinator import SharedFolderCoordinator
import yaml


class Plugins(Config):

    @classmethod
    def advertise(cls, subparsers):
        help_text = "dump active plugins including their dictionaries"
        description_text = "Dump active plugins including their dictionaries."
        parser = subparsers.add_parser(cls._get_short_command_name(),
                                       help=help_text,
                                       description=description_text)
        cls._require_config_file(parser)

    def run_cli(self, cli_args):
        result = self.run(cli_args.config_file)
        print(result)

    def run(self, config_file):
        self._setup_parser(config_file)

        plugin_types = ['lxc_templates', 'lxc_profiles', 'playbooks']

        result = {}

        for plugin_type in plugin_types:
            plugins = self.config.get_ordered_path_items(plugin_type)

            if plugins:
                result[plugin_type] = []

            for plugin in plugins:
                name, resolved_path, node_dict = plugin

                if plugin_type == 'playbooks':
                    sfc = SharedFolderCoordinator(self.config)
                    node_dict['edi_shared_folder_mountpoints'] = sfc.get_mountpoints()

                plugin_info = {name: {'path': resolved_path, 'dictionary': node_dict}}

                result[plugin_type].append(plugin_info)

        return yaml.dump(result, default_flow_style=False)
