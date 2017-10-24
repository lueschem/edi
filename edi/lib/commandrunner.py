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
        result = self.input_artifact

        create_artifact_dir()

        commands = self._get_commands()
        start_index = self._evaluate_start_index(commands)

        for index in range(start_index, len(commands)):
            filename, content, name, path, dictionary, raw_node = commands[index]
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
                new_result = dictionary.get('edi_output_artifact')
                if new_result:
                    result = new_result
                    if not os.path.isfile(new_result) and not os.path.isdir(new_result):
                        raise FatalError(('''The command '{}' did not generate '''
                                          '''the specified output artifact '{}'.'''.format(name, new_result)))
                    elif os.path.isfile(new_result):
                        chown_to_user(new_result)

        return result

    def require_root(self):
        commands = self._get_commands()
        start_index = self._evaluate_start_index(commands)

        for index in range(start_index, len(commands)):
            _, _, _, _, _, raw_node = commands[index]
            if raw_node.get('require_root', False):
                return True

        return False

    def require_root_for_clean(self):
        for _, _, _, _, dictionary, raw_node in self._get_commands():
            if raw_node.get('require_root', False):
                output = dictionary.get('edi_output_artifact')
                if output and os.path.isdir(output):
                    return True

        return False

    def get_plugin_report(self):
        result = {}

        commands = self._get_commands()

        if commands:
            result[self.config_section] = []

        for _, content, name, path, dictionary, _ in commands:
            plugin_info = {name: {'path': path, 'dictionary': dictionary, 'result': LiteralString(content)}}

            result[self.config_section].append(plugin_info)

        return result

    def clean(self):
        commands = self._get_commands()
        for filename, content, name, path, dictionary, raw_node in commands:
            output = dictionary.get('edi_output_artifact')

            if output:
                if not str(get_workdir()) in str(output):
                    raise FatalError('Output artifact {} is not within the current working directory!'.format(output))

                if os.path.isfile(output):
                    logging.info("Removing '{}'.".format(output))
                    os.remove(output)
                    print_success("Removed image artifact {}.".format(output))
                elif os.path.isdir(output):
                    logging.warning("Command runner clean command is not implemented for directories.")

    @staticmethod
    def _run_command(command_file, require_root):
        cmd = [command_file]

        run(cmd, log_threshold=logging.INFO, sudo=require_root)

    def _get_commands(self):
        artifactdir = get_artifact_dir()
        result = self.input_artifact
        commands = self.config.get_ordered_path_items(self.config_section)
        augmented_commands = []
        for name, path, dictionary, raw_node in commands:
            output = raw_node.get('output')

            dictionary['edi_input_artifact'] = result
            if output:
                if str(output) != os.path.basename(output):
                    raise FatalError((('''The specified output '{}' within the command node '{}' is invalid.\n'''
                                       '''The output shall be a file or a folder (no '/' in string).''')
                                      ).format(output, name))
                output_artifact = os.path.join(artifactdir, output)
                dictionary['edi_output_artifact'] = str(output_artifact)
                result = str(output_artifact)

            filename, content = self._render_command_file(path, dictionary)
            augmented_commands.append((filename, content, name, path, dictionary, raw_node))

        return augmented_commands

    @staticmethod
    def _evaluate_start_index(commands, log_existing=False):
        for index, command in reversed(list(enumerate(commands))):
            _, _, name, _, dictionary, _ = command
            artifact = dictionary.get('edi_output_artifact')
            if artifact and (os.path.isfile(artifact) or os.path.isdir(artifact)):
                if log_existing:
                    logging.info(('''Artifact '{}' for command '{}' is already there. '''
                                  '''Delete it to regenerate it.'''
                                  ).format(artifact, name))
                return index + 1

        return 0

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
