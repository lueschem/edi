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
import subprocess
import yaml
from edi.commands.lxc import Lxc
from edi.commands.lxccommands.importcmd import Import
from edi.commands.lxccommands.profile import Profile
from edi.lib.helpers import print_error_and_exit
from edi.lib.shellhelpers import run
from edi.lib.networkhelpers import is_valid_hostname


class Launch(Lxc):

    @classmethod
    def advertise(cls, subparsers):
        help_text = "launch an edi image using LXC"
        description_text = "Launch an edi image using LXC."
        parser = subparsers.add_parser(cls._get_short_command_name(),
                                       help=help_text,
                                       description=description_text)
        parser.add_argument('container_name')
        cls._require_config_file(parser)

    def run_cli(self, cli_args):
        result = self.run(cli_args.container_name, cli_args.config_file)
        print("Launched container {}.".format(result))

    def run(self, container_name, config_file):
        self._setup_parser(config_file)
        self.container_name = container_name

        if not is_valid_hostname(container_name):
            print_error_and_exit(("The provided container name '{}' "
                                  "is not a valid host name."
                                  ).format(container_name))

        if self._is_container_existing():
            logging.info(("Container {0} is already existing. "
                          "Destroy it to regenerate it or reconfigure it."
                          ).format(self._result()))
            if not self._is_container_running():
                logging.info(("Starting existing container {0}."
                              ).format(self._result()))
                self._start_container()
        else:
            image = Import().run(config_file)
            profiles = Profile().run(config_file)
            self._launch_container(image, profiles)

        return self._result()

    def _result(self):
        return self.container_name

    def _is_container_existing(self):
        cmd = []
        cmd.append("lxc")
        cmd.append("info")
        cmd.append(self._result())
        result = run(cmd, check=False, stderr=subprocess.PIPE)
        return result.returncode == 0

    def _is_container_running(self):
        cmd = []
        cmd.append("lxc")
        cmd.append("list")
        cmd.append("--format=json")
        cmd.append("^{}$".format(self._result()))
        result = run(cmd, stdout=subprocess.PIPE)

        try:
            parsed_result = yaml.load(result.stdout)
            if len(parsed_result) != 1:
                return False
            else:
                status = parsed_result[0].get("status", "")
                if status == "Running":
                    return True
                else:
                    return False
        except yaml.YAMLError as exc:
            print_error_and_exit("Unable to parse lxc output ({}).".format(exc))

    def _launch_container(self, image, profiles):
        cmd = []
        cmd.append("lxc")
        cmd.append("launch")
        cmd.append("local:{}".format(image))
        cmd.append(self._result())
        for profile in profiles:
            cmd.extend(["-p", profile])
        run(cmd)

    def _start_container(self):
        cmd = []
        cmd.append("lxc")
        cmd.append("start")
        cmd.append(self._result())

        run(cmd)
