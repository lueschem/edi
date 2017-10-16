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
from codecs import open
from edi.lib.helpers import chown_to_user
from edi.lib.shellhelpers import run
from edi.lib.configurationparser import remove_passwords


class CommandRunner():

    def __init__(self, config, section, input_artifact):
        self.config = config
        self.section = section
        self.input_artifact = input_artifact

    def run_all(self):
        workdir = self.config.get_workdir()

        result = self.input_artifact

        command_list = self.config.get_ordered_command_items(self.section)
        for name, path, dictionary, output, require_root in command_list:
            with tempfile.TemporaryDirectory(dir=workdir) as temp_directory:
                chown_to_user(temp_directory)

                with tempfile.TemporaryDirectory(dir=workdir) as edi_temp_directory:
                    chown_to_user(edi_temp_directory)

                    dictionary['edi_input_artifact'] = result
                    output_artifact = os.path.join(workdir, output)
                    dictionary['edi_output_artifact'] = str(output_artifact)
                    dictionary['edi_temp_directory'] = str(temp_directory)
                    dictionary['edi_plugin_directory'] = str(path)
                    dictionary['edi_log_level'] = logging.getLevelName(logging.getLogger().getEffectiveLevel())
                    self._write_dictionary_file(edi_temp_directory, dictionary)

                    logging.info(("Running command {} located in "
                                  "{} with dictionary:\n{}"
                                  ).format(name, path,
                                           yaml.dump(remove_passwords(dictionary),
                                                     default_flow_style=False)))

                    command_file = self._render_command_file(path, dictionary, edi_temp_directory)
                    self._run_command(command_file, require_root)
                    result = str(output_artifact)

        return result

    @staticmethod
    def _run_command(self, command_file, require_root):
        cmd = [command_file]

        run(cmd, log_threshold=logging.INFO, sudo=require_root)

    @staticmethod
    def _write_dictionary_file(directory, dictionary):
        dictionary_file = os.path.join(directory, "dictionary.yml")
        dictionary['edi_dictionary_file'] = str(dictionary_file)
        with open(dictionary_file, encoding='utf-8', mode='w') as f:
            f.write(yaml.dump(dictionary))
        chown_to_user(dictionary_file)
        return dictionary_file

    @staticmethod
    @staticmethod
    def _render_command_file(input_file, dictionary, output_dir):
        with open(input_file, encoding="UTF-8", mode="r") as template_file:
            template = jinja2.Template(template_file.read(), trim_blocks=True, lstrip_blocks=True)
            result = template.render(dictionary)

        filename = os.path.basename(input_file)
        output_file = os.path.join(output_dir, filename)
        with open(output_file, encoding="UTF-8", mode="w") as result_file:
            result_file.write(result)

        st = os.stat(output_file)
        os.chmod(output_file, st.st_mode | os.stat.S_IEXEC)

        chown_to_user(output_file)

        return output_file
