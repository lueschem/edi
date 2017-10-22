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


import logging
import yaml
from jinja2 import Template
from edi.commands.lxc import Lxc
from edi.lib.helpers import print_success
from edi.lib.sharedfoldercoordinator import SharedFolderCoordinator
from edi.lib.configurationparser import remove_passwords
from edi.lib.lxchelpers import write_lxc_profile
from edi.lib.yamlhelpers import LiteralString


class Profile(Lxc):

    def __init__(self):
        self.config_section = 'lxc_profiles'

    @classmethod
    def advertise(cls, subparsers):
        help_text = "create the LXD container profiles"
        description_text = "Create the LXD container profiles."
        parser = subparsers.add_parser(cls._get_short_command_name(),
                                       help=help_text,
                                       description=description_text)
        cls._offer_introspection_options(parser)
        cls._require_config_file(parser)
        parser.add_argument("-p", "--include-post-config", action="store_true",
                            help="include profiles that can only be applied after configuration")

    @staticmethod
    def _unpack_cli_args(cli_args):
        return [cli_args.config_file, cli_args.include_post_config]

    def dry_run(self, config_file, include_post_config_profiles=False):
        self._setup_parser(config_file)
        plugins = {}
        plugins.update(self._get_plugin_report(include_post_config_profiles))
        return plugins

    def run_cli(self, cli_args):
        self.run(cli_args.config_file, include_post_config_profiles=cli_args.include_post_config,
                 introspection_method=self._get_introspection_method(cli_args))

    def run(self, config_file, include_post_config_profiles=False, introspection_method=None):
        self._setup_parser(config_file)

        if introspection_method:
            introspection_method()
            return []

        profile_name_list = []

        for profile, name, path, dictionary in self._get_profiles(include_post_config_profiles):
            logging.info(("Creating profile {} located in "
                          "{} with dictionary:\n{}"
                          ).format(name, path,
                                   yaml.dump(remove_passwords(dictionary),
                                             default_flow_style=False)))

            full_name, new_profile = write_lxc_profile(profile)
            if new_profile:
                print_success("Created lxc profile {}.".format(full_name))
            profile_name_list.append(full_name)

        print_success('The following profiles are now available: {}'.format(', '.join(profile_name_list)))
        return profile_name_list

    def _get_profiles(self, include_post_config_profiles):
        collected_profiles = []
        profile_list = self.config.get_ordered_path_items(self.config_section)
        for name, path, dictionary, _ in profile_list:
            with open(path, encoding="UTF-8", mode="r") as profile_file:
                profile = Template(profile_file.read())
                profile_text = profile.render(dictionary)
                collected_profiles.append((profile_text, name, path, dictionary))

        sfc = SharedFolderCoordinator(self.config)
        if include_post_config_profiles:
            collected_profiles.extend(sfc.get_post_config_profiles())
        else:
            collected_profiles.extend(sfc.get_pre_config_profiles())

        return collected_profiles

    def _get_plugin_report(self, include_post_config_profiles):
        result = {}
        profiles = self._get_profiles(include_post_config_profiles)

        if profiles:
            result[self.config_section] = []

        for profile in profiles:
            profile_text, name, path, dictionary = profile

            plugin_info = {name: {'path': path, 'dictionary': dictionary, 'result': LiteralString(profile_text)}}

            result[self.config_section].append(plugin_info)

        return result
