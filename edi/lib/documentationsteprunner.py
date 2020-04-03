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
import jinja2
import shutil
import traceback
import gzip
import collections
from dateutil import parser
from debian.changelog import Changelog
from edi.lib.helpers import chown_to_user, FatalError
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
        return augmented_parameters

    def run_all(self):
        self.fetch_artifact_setup()

        workdir = get_workdir()
        applied_documentation_steps = []
        with tempfile.TemporaryDirectory(dir=workdir) as tempdir:
            chown_to_user(tempdir)
            temp_output_path = os.path.join(tempdir, os.path.basename(self.rendered_output))
            with open(temp_output_path, encoding="UTF-8", mode="w") as output:
                chown_to_user(temp_output_path)
                for name, path, parameters, in self._get_documentation_steps():
                    augmented_parameters = self.augment_step_parameters(parameters)

                    logging.info(("Running documentation step {} located in "
                                  "{} with parameters:\n{}"
                                  ).format(name, path,
                                           yaml.dump(remove_passwords(augmented_parameters),
                                                     default_flow_style=False)))

                    self._run_documentation_step(path, augmented_parameters, output)
                    applied_documentation_steps.append(name)
                shutil.move(temp_output_path, self.rendered_output)

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

    def _add_changelog(self, package, baseline_date):
        # TODO: evaluate baseline by package
        package_changelog_path = None
        package_name = package.get('package')
        if os.path.isfile(os.path.join(self.raw_input, package_name, 'changelog.Debian.gz')):
            package_changelog_path = os.path.join(self.raw_input, package_name, 'changelog.Debian.gz')
        elif os.path.isfile(os.path.join(self.raw_input, package_name, 'changelog.gz')):
            package_changelog_path = os.path.join(self.raw_input, package_name, 'changelog.gz')
        else:
            logging.warning("No changelog found for package '{}'.".format(package_name))

        if package_changelog_path:
            with gzip.open(package_changelog_path) as fh:
                changelog = Changelog(fh)
                package_dict = dict()
                package_dict['author'] = changelog.author
                package_dict['date'] = changelog.date
                package_dict['version'] = str(changelog.get_version())
                package_dict['package'] = changelog.package

                change_blocks = list()
                for change_block in changelog:
                    if self._parse_date(change_block.date) < baseline_date:
                        break

                    block_dict = dict()
                    block_dict['author'] = change_block.author
                    block_dict['date'] = change_block.date
                    block_dict['version'] = str(change_block.version)
                    block_dict['package'] = change_block.package
                    block_dict['distributions'] = change_block.distributions
                    block_dict['urgency'] = change_block.urgency
                    change_blocks.append(block_dict)

                package_dict['change_blocks'] = change_blocks

                package['changelog'] = package_dict

    @staticmethod
    def _parse_date(date_string):
        try:
            return parser.parse(date_string)
        except ValueError as ve:
            raise FatalError("Failed to parse date string '{}':\n{}".format(date_string, str(ve)))

    def _run_documentation_step(self, template_path, parameters, outfile):
        step_packages = self._get_documentation_step_packages(parameters)

        if not step_packages:
            context = parameters.copy()
            context['edi_doc_first_chunk'] = True
            context['edi_doc_last_chunk'] = True
            self._render_chunk(template_path, context, outfile)
        else:
            add_changelog = parameters.get('edi_doc_include_changelog', False)
            baseline_date = self._parse_date(parameters.get('edi_doc_changelog_baseline',
                                                            'Thu, 01 Jan 1970 00:00:00 +0000'))
            # chunk size is currently 1
            ordered_packages = collections.OrderedDict(sorted(step_packages.items()))
            first_package = next(iter(ordered_packages))
            last_package = next(reversed(ordered_packages))

            for package in ordered_packages.items():
                context = parameters.copy()
                if package[0] == first_package:
                    context['edi_doc_first_chunk'] = True
                else:
                    context['edi_doc_first_chunk'] = False
                if package[0] == last_package:
                    context['edi_doc_last_chunk'] = True
                else:
                    context['edi_doc_last_chunk'] = False

                package_dict = package[1].copy()
                package_dict['package'] = package[0]

                if add_changelog:
                    self._add_changelog(package_dict, baseline_date)

                context['edi_doc_packages'] = [package_dict]

                self._render_chunk(template_path, context, outfile)

    @staticmethod
    def _render_chunk(template_path, context, outfile):
        try:
            template_loader = jinja2.FileSystemLoader(searchpath=os.path.dirname(template_path))
            environment = jinja2.Environment(loader=template_loader)
            template_file = os.path.basename(template_path)
            template = environment.get_template(template_file)
        except jinja2.TemplateError as te:
            raise FatalError("Encountered template error while processing '{}':\n{}".format(template_path,
                                                                                            str(te)))
        try:
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                logging.debug("Rendering chunk with context:")
                logging.debug(yaml.dump(context, default_flow_style=False))
            outfile.write(template.render(context))
        except Exception:
            raise FatalError("Failed to render '{}':\n{}".format(template_path,
                                                                 traceback.format_exc(limit=-1)))
