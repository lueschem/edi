# -*- coding: utf-8 -*-
# Copyright (C) 2020 Matthias Luescher
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

import os
import logging
from edi.commands.documentation import Documentation
from edi.lib.helpers import print_success, get_artifact_dir
from edi.lib.shellhelpers import safely_remove_artifacts_folder


class Render(Documentation):

    def __init__(self):
        super().__init__()
        self.raw_documentation = None

    @classmethod
    def advertise(cls, subparsers):
        help_text = "render the project documentation"
        description_text = "Render the project documentation."
        parser = subparsers.add_parser(cls._get_short_command_name(),
                                       help=help_text,
                                       description=description_text)
        cls._offer_options(parser, introspection=True, clean=True)
        parser.add_argument('raw_documentation')
        cls._require_config_file(parser)

    @staticmethod
    def _unpack_cli_args(cli_args):
        return [cli_args.raw_documentation, cli_args.config_file]

    def run_cli(self, cli_args):
        self._dispatch(*self._unpack_cli_args(cli_args), run_method=self._get_run_method(cli_args))

    def dry_run(self, raw_documentation, config_file):
        return self._dispatch(raw_documentation, config_file, run_method=self._dry_run)

    def _dry_run(self):
        plugins = {}
        return plugins

    def run(self, raw_documentation, config_file):
        return self._dispatch(raw_documentation, config_file, run_method=self._run)

    def _run(self):
        print("Going to render project documentation to '{}'.".format(self._result()))

        print_success("Rendered project documentation to '{}'.".format(self._result()))
        return self._result()

    def clean_recursive(self, raw_documentation, config_file, depth):
        self.clean_depth = depth
        self._dispatch(raw_documentation, config_file, run_method=self._clean)

    def clean(self, config_file):
        self._dispatch(None, config_file, run_method=self._clean)

    def _clean(self):
        if os.path.isdir(self._result()):
            logging.info("Removing project documentation '{}'.".format(self._result()))
            safely_remove_artifacts_folder(self._result())
            print_success("Removed project documentation '{}'.".format(self._result()))

    def _dispatch(self, raw_documentation, config_file, run_method):
        self._setup_parser(config_file)
        self.raw_documentation = raw_documentation
        return run_method()

    def _result(self):
        # TODO: use get_documentation_name()
        return os.path.join(get_artifact_dir(), "{}_documentation".format(self.config.get_configuration_name()))
