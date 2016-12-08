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
import hashlib
import subprocess
from jinja2 import Template
from edi.commands.lxc import Lxc
from edi.lib.shellhelpers import run
from edi.lib.helpers import print_success


class Profile(Lxc):

    @classmethod
    def advertise(cls, subparsers):
        help_text = "create the configured LXD container profiles"
        description_text = "Create the configured LXD container profiles."
        parser = subparsers.add_parser(cls._get_short_command_name(),
                                       help=help_text,
                                       description=description_text)
        cls._require_config_file(parser)

    def run_cli(self, cli_args):
        result = self.run(cli_args.config_file)

    def run(self, config_file):
        self._setup_parser(config_file)

        profile_list = self.config.get_ordered_items("lxc_profiles")
        profile_name_list = []
        for name, path, dictionary in profile_list:
            logging.info(("Creating profile {} located in "
                          "{} with dictionary:\n{}"
                          ).format(name, path,
                                   yaml.dump(dictionary,
                                             default_flow_style=False)))

            with open(path, encoding="UTF-8", mode="r") as profile_file:
                profile = Template(profile_file.read())
                profile_text = profile.render(dictionary)
                profile_yaml = yaml.load(profile_text)
                profile_hash = hashlib.sha256(profile_text.encode()
                                              ).hexdigest()[:20]
                profile_name = profile_yaml.get("name", "anonymous")
                ext_profile_name = "{}_{}".format(profile_name,
                                                  profile_hash)
                profile_name_list.append(ext_profile_name)
                profile_yaml["name"] = ext_profile_name
                profile_content = yaml.dump(profile_yaml,
                                            default_flow_style=False)
                self._write_lxc_profile(ext_profile_name,
                                        profile_content)

        return profile_name_list

    def _is_profile_existing(self, name):
        cmd = []
        cmd.append("lxc")
        cmd.append("profile")
        cmd.append("show")
        cmd.append(name)
        result = run(cmd, check=False, stderr=subprocess.PIPE)
        return result.returncode == 0

    def _write_lxc_profile(self, name, content):
        if not self._is_profile_existing(name):
            create_cmd = []
            create_cmd.append("lxc")
            create_cmd.append("profile")
            create_cmd.append("create")
            create_cmd.append(name)
            run(create_cmd)
            print_success("Created lxc profile {}.".format(name))

        edit_cmd = []
        edit_cmd.append("lxc")
        edit_cmd.append("profile")
        edit_cmd.append("edit")
        edit_cmd.append(name)
        run(edit_cmd, input=content)
