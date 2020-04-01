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

import logging
import tempfile
import yaml
from edi.lib.helpers import chown_to_user
from edi.lib.helpers import get_workdir
from edi.lib.configurationparser import remove_passwords


class DocumentationStepRunner():

    def __init__(self, config, raw_input, rendered_output):
        self.config = config
        self.raw_input = raw_input
        self.rendered_output = rendered_output
        self.config_section = 'documentation_steps'

    def run_all(self):
        workdir = get_workdir()

        applied_documentation_steps = []
        with tempfile.TemporaryDirectory(dir=workdir) as tempdir:
            chown_to_user(tempdir)

            for name, path, parameters, in self._get_documentation_steps():
                logging.info(("Running documentation step {} located in "
                              "{} with parameters:\n{}"
                              ).format(name, path,
                                       yaml.dump(remove_passwords(parameters),
                                                 default_flow_style=False)))

                self._run_documentation_step(path, parameters, tempdir)
                applied_documentation_steps.append(name)

        return applied_documentation_steps

    def _get_documentation_steps(self):
        step_list = []
        documentation_step_list = self.config.get_ordered_path_items(self.config_section)
        for name, path, parameters, _ in documentation_step_list:
            step_list.append((name, path, parameters))

        return step_list

    def get_plugin_report(self):
        result = dict()

        documentation_steps = self._get_documentation_steps()

        if documentation_steps:
            result[self.config_section] = []

        for name, path, parameters in documentation_steps:
            plugin_info = {name: {'path': path, 'dictionary': parameters}}

            result[self.config_section].append(plugin_info)

        return result

    def _run_documentation_step(self, path, parameters, tempdir):
        pass
