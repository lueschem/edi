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
from edi.commands.imagecommands.imagelxc import Lxc as LxcImageCommand
from edi.lib.helpers import print_success
from edi.lib.lxchelpers import is_in_image_store, import_image, delete_image


class Import(Lxc):

    @classmethod
    def advertise(cls, subparsers):
        help_text = "import an image into the LXD image store"
        description_text = "Import an image into the LXD image store."
        parser = subparsers.add_parser(cls._get_short_command_name(),
                                       help=help_text,
                                       description=description_text)
        cls._offer_introspection_options(parser)
        cls._require_config_file(parser)

    def run_cli(self, cli_args):
        self._dispatch(*self._unpack_cli_args(cli_args), run_method=self._get_run_method(cli_args))

    def dry_run(self, config_file):
        return self._dispatch(config_file, run_method=self._dry_run)

    def _dry_run(self):
        return LxcImageCommand().dry_run(self.config.get_base_config_file())

    def run(self, config_file):
        return self._dispatch(config_file, run_method=self._run)

    def _run(self):
        if is_in_image_store(self._result()):
            logging.info(("{0} is already in image store. "
                          "Delete it to regenerate it."
                          ).format(self._result()))
            return self._result()

        image = LxcImageCommand().run(self.config.get_base_config_file())

        print("Going to import lxc image into image store.")

        import_image(image, self._result())

        print_success("Imported lxc image into image store as {}.".format(self._result()))

        return self._result()

    def clean(self, config_file):
        self._dispatch(config_file, run_method=self._clean)

    def _clean(self):
        if is_in_image_store(self._result()):
            logging.info(("Removing '{}' from image store."
                          ).format(self._result()))
            delete_image(self._result())
            print_success("Removed {} from image store.".format(self._result()))

    def _dispatch(self, config_file, run_method):
        self._setup_parser(config_file)
        return run_method()

    def _result(self):
        return "{}_{}".format(self.config.get_project_name(),
                              self._get_command_file_name_prefix())
