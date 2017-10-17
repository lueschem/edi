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
from edi.commands.lxc import Lxc
from edi.commands.lxccommands.importcmd import Import
from edi.commands.lxccommands.profile import Profile
from edi.lib.helpers import FatalError, print_success
from edi.lib.networkhelpers import is_valid_hostname
from edi.lib.lxchelpers import (is_container_existing, is_container_running, start_container,
                                launch_container, get_container_profiles, stop_container,
                                apply_profiles)


class Launch(Lxc):

    def __init__(self):
        self.container_name = ""

    @classmethod
    def advertise(cls, subparsers):
        help_text = "launch an image using LXC"
        description_text = "Launch an image using LXC."
        parser = subparsers.add_parser(cls._get_short_command_name(),
                                       help=help_text,
                                       description=description_text)
        cls._offer_introspection_options(parser)
        parser.add_argument('container_name')
        cls._require_config_file(parser)

    def run_cli(self, cli_args):
        self.run(cli_args.container_name, cli_args.config_file,
                 introspection_method=self._get_introspection_method(
                     cli_args, ['lxc_templates', 'lxc_profiles']))

    def run(self, container_name, config_file, introspection_method=None):
        self._setup_parser(config_file)
        self.container_name = container_name

        if introspection_method:
            self._print(introspection_method())
            return self._result()

        if not is_valid_hostname(container_name):
            raise FatalError(("The provided container name '{}' "
                              "is not a valid host name."
                              ).format(container_name))

        profiles = Profile().run(config_file)

        if is_container_existing(self._result()):
            logging.info(("Container {0} is already existing. "
                          "Destroy it to regenerate it or reconfigure it."
                          ).format(self._result()))

            current_profiles = get_container_profiles(self._result())
            if not Launch.verify_profiles(profiles, current_profiles):
                # we might end up here if the container got imported
                # from a distributable image
                logging.info(("The profiles of container {0} need to be updated."
                              ).format(self._result()))
                if is_container_running(self._result()):
                    logging.info(("Stopping container {0} to update profiles."
                                  ).format(self._result()))
                    stop_container(self._result())
                apply_profiles(self._result(), profiles)

            if not is_container_running(self._result()):
                logging.info(("Starting existing container {0}."
                              ).format(self._result()))
                start_container(self._result())
                print_success("Started container {}.".format(self._result()))
        else:
            image = Import().run(config_file)
            print("Going to launch container.")
            launch_container(image, self._result(), profiles)
            print_success("Launched container {}.".format(self._result()))

        return self._result()

    @staticmethod
    def verify_profiles(desired_profiles, current_profiles):
        for desired_profile in desired_profiles:
            if desired_profile not in current_profiles:
                return False
        return True

    def _result(self):
        return self.container_name
