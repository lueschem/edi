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

import os
import logging
import tempfile
import yaml
import jinja2
import stat
from codecs import open
from edi.lib.helpers import (chown_to_user, FatalError, get_workdir, get_artifact_dir,
                             create_artifact_dir, print_success)
from edi.lib.shellhelpers import run
from edi.lib.configurationparser import remove_passwords
from edi.lib.yamlhelpers import LiteralString


class CommandRunner():

    def __init__(self, config, section, input_artifact):
        self.config = config
        self.config_section = section
        self.input_artifact = input_artifact

    def run(self):
        workdir = get_workdir()
        create_artifact_dir()

        commands = self._get_commands()

        for filename, content, name, path, dictionary, raw_node, artifacts in commands:
            if self._are_all_artifacts_available(artifacts):
                logging.info(('''Artifacts for command '{}' are already there. '''
                              '''Delete them to regenerate them.'''
                              ).format(name))
            else:
                with tempfile.TemporaryDirectory(dir=workdir) as tmpdir:
                    chown_to_user(tmpdir)
                    require_root = raw_node.get('require_root', False)

                    logging.info(("Running command {} located in "
                                  "{} with dictionary:\n{}"
                                  ).format(name, path,
                                           yaml.dump(remove_passwords(dictionary),
                                                     default_flow_style=False)))

                    command_file = self._flush_command_file(tmpdir, filename, content)
                    self._run_command(command_file, require_root)
                    self._post_process_artifacts(name, artifacts)

        return self._result(commands)

    def require_root(self):
        commands = self._get_commands()

        for _, _, _, _, _, raw_node, artifacts in commands:
            if not self._are_all_artifacts_available(artifacts) and raw_node.get('require_root', False):
                return True

        return False

    def require_root_for_clean(self):
        for _, _, _, _, _, raw_node, artifacts in self._get_commands():
            if raw_node.get('require_root', False) and self._is_an_artifact_a_directory(artifacts):
                return True

        return False

    def get_plugin_report(self):
        result = {}

        commands = self._get_commands()

        if commands:
            result[self.config_section] = []

        for _, content, name, path, dictionary, _, _ in commands:
            plugin_info = {name: {'path': path, 'dictionary': dictionary, 'result': LiteralString(content)}}

            result[self.config_section].append(plugin_info)

        return result

    def clean(self):
        commands = self._get_commands()
        for filename, content, name, path, dictionary, raw_node, artifacts in commands:
            for _, artifact in artifacts.items():
                if not str(get_workdir()) in str(artifact):
                    raise FatalError(('Output artifact {} is not within the current working directory!'
                                      ).format(artifact))

                if os.path.isfile(artifact):
                    logging.info("Removing '{}'.".format(artifact))
                    os.remove(artifact)
                    print_success("Removed image artifact {}.".format(artifact))
                elif os.path.isdir(artifact):
                    logging.warning("Command runner clean command is not implemented for directories.")

    @staticmethod
    def _run_command(command_file, require_root):
        cmd = ['sh', '-c', command_file]

        run(cmd, log_threshold=logging.INFO, sudo=require_root)

    def _get_commands(self):
        artifactdir = get_artifact_dir()
        commands = self.config.get_ordered_path_items(self.config_section)
        augmented_commands = []
        artifacts = dict()
        if self.input_artifact:
            artifacts['edi_input_artifact'] = self.input_artifact

        for name, path, dictionary, raw_node in commands:
            output = raw_node.get('output')
            if type(output) != dict:
                raise FatalError(('''The output specification in command node '{}' is not a key value dictionary.'''
                                  ).format(name))

            new_artifacts = dict()
            for artifact_key, artifact_item in output.items():
                if str(artifact_item) != os.path.basename(artifact_item):
                    raise FatalError((('''The specified output artifact '{}' within the '''
                                       '''command node '{}' is invalid.\n'''
                                       '''The output shall be a file or a folder (no '/' in string).''')
                                      ).format(artifact_key, name))
                artifact_path = os.path.join(artifactdir, artifact_item)
                new_artifacts[artifact_key] = str(artifact_path)

            artifacts.update(new_artifacts)
            dictionary.update(artifacts)
            filename, content = self._render_command_file(path, dictionary)
            augmented_commands.append((filename, content, name, path, dictionary, raw_node, new_artifacts))

        return augmented_commands

    @staticmethod
    def _are_all_artifacts_available(artifacts):
        for _, artifact in artifacts.items():
            if not os.path.isfile(artifact) and not os.path.isdir(artifact):
                return False

        return True

    @staticmethod
    def _is_an_artifact_a_directory(artifacts):
        for _, artifact in artifacts.items():
            if os.path.isdir(artifact):
                return True

        return False

    @staticmethod
    def _post_process_artifacts(command_name, expected_artifacts):
        for _, artifact in expected_artifacts.items():
            if not os.path.isfile(artifact) and not os.path.isdir(artifact):
                raise FatalError(('''The command '{}' did not generate '''
                                  '''the specified output artifact '{}'.'''.format(command_name, artifact)))
            elif os.path.isfile(artifact):
                chown_to_user(artifact)

    @staticmethod
    def _render_command_file(input_file, dictionary):
        with open(input_file, encoding="UTF-8", mode="r") as template_file:
            template = jinja2.Template(template_file.read())
            result = template.render(dictionary)

        filename = os.path.basename(input_file)
        return filename, result

    @staticmethod
    def _flush_command_file(output_dir, filename, content):
        output_file = os.path.join(output_dir, filename)
        with open(output_file, encoding="UTF-8", mode="w") as result_file:
            result_file.write(content)

        st = os.stat(output_file)
        os.chmod(output_file, st.st_mode | stat.S_IEXEC)

        chown_to_user(output_file)

        return output_file

    def _result(self, commands):
        all_artifacts = list()
        for _, _, _, _, _, _, artifacts in commands:
            for _, artifact in artifacts.items():
                all_artifacts.append(artifact)

        if all_artifacts:
            return all_artifacts
        else:
            return [self.input_artifact]
