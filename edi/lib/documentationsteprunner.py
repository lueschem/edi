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
import os
from edi.lib.helpers import chown_to_user
from edi.lib.helpers import get_workdir
from edi.lib.configurationparser import remove_passwords


class DocumentationStepRunner():

    def __init__(self, config, raw_input, rendered_output):
        self.config = config
        self.raw_input = raw_input
        self.rendered_output = rendered_output
        self.config_section = 'documentation_steps'
        self.build_setup = dict()
        self.installed_packages = dict()

    def fetch_artifact_setup(self):
        self.build_setup = self._get_build_setup()
        self.installed_packages = self._get_installed_packages()

    def augment_step_parameters(self, parameters):
        augmented_parameters = parameters.copy()
        augmented_parameters['edi_build_setup'] = self.build_setup
        augmented_parameters['edi_doc_packages'] = self._get_documentation_step_packages(parameters)
        return augmented_parameters

    def run_all(self):
        self.fetch_artifact_setup()

        workdir = get_workdir()
        applied_documentation_steps = []
        with tempfile.TemporaryDirectory(dir=workdir) as tempdir:
            chown_to_user(tempdir)

            for name, path, parameters, in self._get_documentation_steps():
                augmented_parameters = self.augment_step_parameters(parameters)

                logging.info(("Running documentation step {} located in "
                              "{} with parameters:\n{}"
                              ).format(name, path,
                                       yaml.dump(remove_passwords(augmented_parameters),
                                                 default_flow_style=False)))

                self._run_documentation_step(path, augmented_parameters, tempdir)
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

        self.fetch_artifact_setup()

        documentation_steps = self._get_documentation_steps()

        if documentation_steps:
            result[self.config_section] = []

        for name, path, parameters in documentation_steps:
            augmented_parameters = self.augment_step_parameters(parameters)
            plugin_info = {name: {'path': path, 'dictionary': augmented_parameters}}
            result[self.config_section].append(plugin_info)

        return result

    def _get_build_setup(self):
        build_info_file = os.path.join(self.raw_input, 'edi', 'build.yml')

        if not os.path.isfile(build_info_file):
            logging.warning("No build setup file found in '{}'.".format(build_info_file))
            return dict()

        logging.debug("Found build setup file '{}'.".format(build_info_file))
        with open(build_info_file, mode='r') as f:
            return yaml.safe_load(f.read())

    def _get_installed_packages(self):
        installed_packages_file = os.path.join(self.raw_input, 'edi', 'packages.yml')

        if not os.path.isfile(installed_packages_file):
            logging.warning("No file describing the installed packages found in '{}'.".format(installed_packages_file))
            return dict()

        logging.debug("Found file describing the installed packages in '{}'.".format(installed_packages_file))
        with open(installed_packages_file, mode='r') as f:
            return yaml.safe_load(f.read())

    def _get_documentation_step_packages(self, parameters):
        installed_packages = set(self.installed_packages.keys())
        include_packages = set(parameters.get('edi_doc_include_packages', installed_packages))
        step_packages = installed_packages.intersection(include_packages)
        exclude_packages = set(parameters.get('edi_doc_exclude_packages', []))
        step_packages = step_packages - exclude_packages
        step_packages_dict = {package: self.installed_packages[package] for package in step_packages}
        return step_packages_dict

    def _run_documentation_step(self, path, parameters, tempdir):
        pass
