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

import logging
import os
from edi.commands.lxc import Lxc
from edi.lib.configurationparser import command_context
from edi.lib.lxchelpers import (export_image, get_file_extension_from_image_compression_algorithm,
                                get_server_image_compression_algorithm)
from edi.commands.lxccommands.publish import Publish
from edi.lib.helpers import print_success


class Export(Lxc):

    @classmethod
    def advertise(cls, subparsers):
        help_text = "export an image from the LXD image store"
        description_text = "Export an image from the LXD image store."
        parser = subparsers.add_parser(cls._get_short_command_name(),
                                       help=help_text,
                                       description=description_text)
        cls._offer_introspection_options(parser)
        cls._require_config_file(parser)

    def run_cli(self, cli_args):
        self.run(cli_args.config_file, introspection_method=self._get_introspection_method(
            cli_args, ['lxc_templates', 'lxc_profiles', 'playbooks']))

    def run(self, config_file, introspection_method=None):
        with command_context({'edi_create_distributable_image': True}):
            self._setup_parser(config_file)

            if introspection_method:
                print(introspection_method())
                return self._result()

            if os.path.isfile(self._result()):
                logging.info(("{0} is already there. "
                              "Delete it to regenerate it."
                              ).format(self._result()))
                return self._result()

            image_name = Publish().run(config_file)

            print("Going to export lxc image from image store.")

            export_image(image_name, self._image_without_extension())

            if (os.path.isfile(self._image_without_extension()) and
                    not os.path.isfile(self._result())):
                # Workaround for https://github.com/lxc/lxd/issues/3869
                logging.info("Fixing file extension of exported image.")
                os.rename(self._image_without_extension(), self._result())

            print_success("Exported lxc image as {}.".format(self._result()))

        return self._result()

    def clean(self, config_file):
        self._setup_parser(config_file)

        if os.path.isfile(self._result()):
            logging.info("Removing '{}'.".format(self._result()))
            os.remove(self._result())
            print_success("Removed lxc image {}.".format(self._result()))

    def _result_base_name(self):
        return "{0}_{1}".format(self.config.get_project_name(),
                                self._get_command_file_name_prefix())

    def _image_without_extension(self):
        return os.path.join(self.config.get_workdir(), self._result_base_name())

    def _result(self):
        algorithm = get_server_image_compression_algorithm()
        extension = get_file_extension_from_image_compression_algorithm(algorithm)
        archive = "{}{}".format(self._result_base_name(), extension)
        return os.path.join(self.config.get_workdir(), archive)
