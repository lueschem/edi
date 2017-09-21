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

from edi.commands.lxc import Lxc
from edi.lib.configurationparser import command_context
from edi.lib.helpers import print_success


class Export(Lxc):

    @classmethod
    def advertise(cls, subparsers):
        help_text = "export an image from the LXD image store"
        description_text = "Export an image from the LXD image store."
        parser = subparsers.add_parser(cls._get_short_command_name(),
                                       help=help_text,
                                       description=description_text)
        cls._require_config_file(parser)

    def run_cli(self, cli_args):
        self.run(cli_args.config_file)

    def run(self, config_file):
        with command_context({'edi_create_distributable_image': True}):
            self._setup_parser(config_file)

            # if self._is_in_image_store():
            #     logging.info(("{0} is already in image store. "
            #                   "Delete it to regenerate it."
            #                   ).format(self._result()))
            #     return self._result()
            #
            # image = LxcImageCommand().run(config_file)
            #
            # print("Going to import lxc image into image store.")
            #
            # self._import_image(image)
            #
            # print_success("Imported lxc image into image store as {}.".format(self._result()))

        return self._result()

    def clean(self, config_file):
        self._setup_parser(config_file)

        # if self._is_in_image_store():
        #     logging.info(("Removing '{}' from image store."
        #                   ).format(self._result()))
        #     self._delete_image()
        #     print_success("Removed {} from image store.".format(self._result()))

    def _result(self):
        return "{}_{}".format(self.config.get_project_name(),
                              self._get_command_file_name_prefix())
