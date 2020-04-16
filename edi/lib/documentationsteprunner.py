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
import re
import jinja2
import shutil
import traceback
import gzip
from dateutil import parser
from debian.changelog import Changelog
from debian.debian_support import Version
from edi.lib.helpers import print_success, FatalError
from edi.lib.helpers import get_workdir
from edi.lib.configurationparser import remove_passwords


class ChangesAnnotator():
    def __init__(self, package):
        self._pattern_lookup = [
            # level 0: author, empty line or fallback
            [('author', r'^[ ]{2}\[[ ]*', self._trim_author, []),
             ('empty_line', r'^$', self._nop, []),
             ('list_item', r'.*', self._report_parser_warning, [])],
            # level 1: list item, list item continuation or empty line
            [('list_item', r'^[ ]{2}[*+-] ', self._trim_list_item, []),
             ('list_item_continuation', r'^[ ]{2,4}[^[]', self._trim_list_item_continuation,
              ['list_item', 'list_item_continuation'])],
            # level 2: sub list item, sub list item continuation or empty line
            [('sub_list_item', r'^[ ]{3,4}[*+-] ', ChangesAnnotator._trim_list_item, []),
             ('sub_list_item_continuation', r'^[ ]{5,6}', ChangesAnnotator._trim_list_item_continuation,
              ['sub_list_item', 'sub_list_item_continuation'])],
            # level 3: sub sub list item, sub sub list item continuation or empty line
            [('sub_sub_list_item', r'^[ ]{6}[*+-] ', self._trim_list_item, []),
             ('sub_sub_list_item_continuation', r'^[ ]{8}', ChangesAnnotator._trim_list_item_continuation,
              ['sub_sub_list_item', 'sub_sub_list_item_continuation'])],
            # level 5: sentinel
            [],
        ]
        self._current_level = 0
        self._package = package

    def annotate(self, changes):
        annotated_changes = list()
        self._current_level = 0

        for change in changes:
            match_found = False
            for level in range(self._current_level + 1, -1, -1):
                for annotation, expression, modification, compatibility in self._pattern_lookup[level]:
                    if re.match(expression, change):
                        match_found = True
                        self._current_level = level
                        current_change = modification(change)

                        if annotated_changes and annotated_changes[-1][0] in compatibility:
                            previous_annotation, previous_change = annotated_changes[-1]
                            annotated_changes[-1] = (previous_annotation, " ".join([previous_change, current_change]))
                        else:
                            annotated_changes.append((annotation, current_change))
                        break

                    if level == self._current_level + 1:
                        break

                if match_found:
                    break

        return annotated_changes

    @staticmethod
    def _trim_author(text):
        return re.sub(r'^[ ]*\[(.*)\]$', r'\1', text).strip()

    @staticmethod
    def _trim_list_item(text):
        return re.sub(r'^[ ]*[*+-] (.*)$', r'\1', text)

    @staticmethod
    def _trim_list_item_continuation(text):
        return text.strip()

    @staticmethod
    def _nop(text):
        return text

    def _report_parser_warning(self, text):
        logging.warning("For package '{}': Failed to parse '{}' at level {}!".format(
            self._package, text, self._current_level))
        return text


class DocumentationStepRunner():
    def __init__(self, config, raw_input, rendered_output):
        self.config = config
        self.raw_input = raw_input
        self.rendered_output = rendered_output
        self.config_section = 'documentation_steps'
        self.build_setup = dict()
        self.installed_packages = list()
        self.baseline_versions = dict()

    def fetch_artifact_setup(self):
        self.build_setup = self._get_build_setup()
        self.installed_packages = self._get_installed_packages()
        self.baseline_versions = self._get_baseline_versions()

    def augment_step_parameters(self, parameters):
        augmented_parameters = parameters.copy()
        augmented_parameters['edi_build_setup'] = self.build_setup
        return augmented_parameters

    def check_for_absence_of_output_files(self):
        for name, _, _, raw_node in self._get_documentation_steps():
            file = self._get_output_file(name, raw_node)

            file_path = os.path.join(self.rendered_output, file)
            if os.path.exists(file_path):
                raise FatalError("Output file '{}' already exists.".format(file_path))

    def run_all(self):
        self.fetch_artifact_setup()

        workdir = get_workdir()
        applied_documentation_steps = []
        with tempfile.TemporaryDirectory(dir=workdir) as tempdir:
            temp_output_file_paths = set()
            for name, path, parameters, raw_node in self._get_documentation_steps():
                output_file = self._get_output_file(name, raw_node)
                temp_output_path = os.path.join(tempdir, output_file)
                temp_output_file_paths.add(temp_output_path)
                with open(temp_output_path, encoding="UTF-8", mode="a") as output:
                    augmented_parameters = self.augment_step_parameters(parameters)

                    logging.info(("Running documentation step {} located in "
                                  "{} with parameters:\n{}\n"
                                  "Writing output to {}."
                                  ).format(name, path,
                                           yaml.dump(remove_passwords(augmented_parameters),
                                                     default_flow_style=False),
                                           os.path.join(self.rendered_output, output_file)))

                    self._run_documentation_step(path, augmented_parameters, output)
                    applied_documentation_steps.append(name)

            for temp_output_file_path in temp_output_file_paths:
                shutil.move(temp_output_file_path, os.path.join(self.rendered_output,
                                                                os.path.basename(temp_output_file_path)))

        return applied_documentation_steps

    def clean(self):
        for name, _, _, raw_node in self._get_documentation_steps():
            file = self._get_output_file(name, raw_node)

            file_path = os.path.join(self.rendered_output, file)
            if os.path.exists(file_path):
                logging.info("Removing '{}'.".format(file_path))
                try:
                    os.remove(file_path)
                except Exception as e:
                    raise FatalError("Failed to delete {}:\n{}".format(file_path, e))

                print_success("Removed documentation file {}.".format(file_path))

    def _get_documentation_steps(self):
        step_list = []
        documentation_step_list = self.config.get_ordered_path_items(self.config_section)
        for name, path, parameters, raw_node in documentation_step_list:
            step_list.append((name, path, parameters, raw_node))

        return step_list

    def get_plugin_report(self):
        result = dict()

        self.fetch_artifact_setup()

        documentation_steps = self._get_documentation_steps()

        if documentation_steps:
            result[self.config_section] = []

        for name, path, parameters, raw_node in documentation_steps:
            augmented_parameters = self.augment_step_parameters(parameters)
            plugin_info = {name: {'path': path, 'dictionary': augmented_parameters,
                                  'output': raw_node.get('output', {})}}
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
            return list()

        logging.debug("Found file describing the installed packages in '{}'.".format(installed_packages_file))
        with open(installed_packages_file, mode='r') as f:
            installed_packages = yaml.safe_load(f.read())
            if not isinstance(installed_packages, list):
                raise FatalError("'{}' should contain a list of installed packages.".format(installed_packages_file))
            return installed_packages

    def _get_baseline_versions(self):
        baseline_file = os.path.join(self.raw_input, 'edi', 'packages-baseline.yml')

        if not os.path.isfile(baseline_file):
            logging.info("No file describing the packages baseline found in '{}'.".format(baseline_file))
            return dict()

        logging.debug("Found file describing the packages baseline in '{}'.".format(baseline_file))
        with open(baseline_file, mode='r') as f:
            baseline_packages = yaml.safe_load(f.read())
            if not isinstance(baseline_packages, list):
                raise FatalError("'{}' should contain a list of baseline packages.".format(baseline_packages))
            return {self._get_package_value('package', package_dict): self._get_package_value('version', package_dict)
                    for package_dict in baseline_packages}

    @staticmethod
    def _get_package_value(key, package_dict):
        value = package_dict.get(key)
        if not value:
            raise FatalError("Missing '{}' key in dictionary of package ({}).".format(key, package_dict))
        return value

    @staticmethod
    def _get_output_file(name, node):
        file = node.get('output', {}).get('file')
        if not file:
            raise FatalError('Missing output file for {}.'.format(name))
        return file

    def _get_documentation_step_packages(self, parameters):
        installed_packages = set([self._get_package_value('package', package) for package in self.installed_packages])
        include_packages = set(parameters.get('edi_doc_include_packages', installed_packages))
        step_packages = installed_packages.intersection(include_packages)
        exclude_packages = set(parameters.get('edi_doc_exclude_packages', []))
        step_packages = step_packages - exclude_packages
        step_package_list = [package for package in self.installed_packages
                             if self._get_package_value('package', package) in step_packages]
        return step_package_list

    @staticmethod
    def _get_replacements(parameters):
        replacements = parameters.get('edi_doc_replacements', [])
        if not isinstance(replacements, list):
            raise FatalError("'edi_doc_replacements' should contain a list of replacement instructions.")
        return replacements

    @staticmethod
    def _apply_replacements(string_list, replacements):
        result = []
        for item in string_list:
            for replacement in replacements:
                p = replacement.get('pattern', '')
                r = replacement.get('replacement', '')
                try:
                    item = re.sub(p, r, item)
                except Exception as e:
                    raise FatalError(("Failed to apply regular expression:\n"
                                      "pattern: {}\nreplacement: {}:\nmessage: {}").format(p, r, str(e)))

            result. append(item)

        return result

    def _add_changelog(self, package, baseline_date, replacements):
        # TODO: evaluate baseline by package
        package_changelog_path = None
        package_name = self._get_package_value('package', package)
        if os.path.isfile(os.path.join(self.raw_input, package_name, 'changelog.Debian.gz')):
            package_changelog_path = os.path.join(self.raw_input, package_name, 'changelog.Debian.gz')
        elif os.path.isfile(os.path.join(self.raw_input, package_name, 'changelog.gz')):
            package_changelog_path = os.path.join(self.raw_input, package_name, 'changelog.gz')
        else:
            logging.warning("No changelog found for package '{}'.".format(package_name))

        if package_changelog_path:
            with gzip.open(package_changelog_path) as fh:
                try:
                    changelog = Changelog(fh)
                except UnicodeDecodeError as e:
                    raise FatalError("Failed to parse changelog of {}:\n{}".format(package_name, str(e)))

                if not (changelog.package or changelog.date or changelog.author):
                    logging.warning("The changelog of package '{}' is incomplete.".format(package_name))
                    return

                package_dict = dict()
                package_dict['author'] = changelog.author
                package_dict['date'] = changelog.date
                package_dict['short_date'] = self._parse_date(changelog.date).strftime("%d. %B %Y")
                package_dict['version'] = str(changelog.get_version())
                package_dict['package'] = changelog.package

                change_blocks = list()
                for change_block in changelog:
                    changeblock_date = self._parse_date(change_block.date)

                    if changeblock_date <= baseline_date:
                        break

                    if change_block.version <= Version(self.baseline_versions.get(package_name, '0.0.0')):
                        break

                    block_dict = dict()
                    block_dict['author'] = change_block.author
                    block_dict['date'] = change_block.date
                    block_dict['short_date'] = changeblock_date.strftime("%d. %B %Y")
                    block_dict['version'] = str(change_block.version)
                    block_dict['package'] = change_block.package
                    block_dict['distributions'] = change_block.distributions
                    block_dict['urgency'] = change_block.urgency
                    changes = self._apply_replacements(change_block.changes(), replacements)
                    block_dict['changes'] = ChangesAnnotator(package_name).annotate(changes)
                    change_blocks.append(block_dict)

                package_dict['change_blocks'] = change_blocks

                package['changelog'] = package_dict

    @staticmethod
    def _parse_date(date_string):
        try:
            return parser.parse(date_string)
        except Exception as e:
            raise FatalError("Failed to parse date string '{}':\n{}".format(date_string, str(e)))

    def _run_documentation_step(self, template_path, parameters, outfile):
        step_packages = self._get_documentation_step_packages(parameters)
        step_replacements = self._get_replacements(parameters)

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
            first_package = self._get_package_value('package', step_packages[0])
            last_package = self._get_package_value('package', step_packages[-1])

            for package in step_packages:
                context = parameters.copy()
                name = self._get_package_value('package', package)
                if name == first_package:
                    context['edi_doc_first_chunk'] = True
                else:
                    context['edi_doc_first_chunk'] = False
                if name == last_package:
                    context['edi_doc_last_chunk'] = True
                else:
                    context['edi_doc_last_chunk'] = False

                package_context = package.copy()
                package_context['baseline_version'] = self.baseline_versions.get(name, "0.0.0")

                if add_changelog:
                    self._add_changelog(package_context, baseline_date, step_replacements)

                context['edi_doc_packages'] = [package_context]

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
