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
from edi.lib.helpers import chown_to_user, FatalError
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

        command_list = self.config.get_ordered_path_items(self.section)
        for name, path, dictionary, raw_node in command_list:
            with tempfile.TemporaryDirectory(dir=workdir) as tmpdir:
                chown_to_user(tmpdir)

                output = raw_node.get('output')
                require_root = raw_node.get('require_root', False)

                dictionary['edi_input_artifact'] = result
                if output:
                    if str(output) != os.path.basename(output):
                        raise FatalError((('''The specified output '{}' within the command node '{}' is invalid.\n'''
                                           '''The output shall be a file or a folder (no '/' in string).''')
                                          ).format(output, name))
                    output_artifact = os.path.join(workdir, output)
                    dictionary['edi_output_artifact'] = str(output_artifact)
                    result = str(output_artifact)

                logging.info(("Running command {} located in "
                              "{} with dictionary:\n{}"
                              ).format(name, path,
                                       yaml.dump(remove_passwords(dictionary),
                                                 default_flow_style=False)))

                command_file = self._render_command_file(path, dictionary, tmpdir)
                self._run_command(command_file, require_root)

        return result

    @staticmethod
    def _run_command(self, command_file, require_root):
        cmd = [command_file]

        run(cmd, log_threshold=logging.INFO, sudo=require_root)

    @staticmethod
    def _render_command_file(input_file, dictionary, output_dir):
        with open(input_file, encoding="UTF-8", mode="r") as template_file:
            template = jinja2.Template(template_file.read())
            result = template.render(dictionary)

        filename = os.path.basename(input_file)
        output_file = os.path.join(output_dir, filename)
        with open(output_file, encoding="UTF-8", mode="w") as result_file:
            result_file.write(result)

        st = os.stat(output_file)
        os.chmod(output_file, st.st_mode | os.stat.S_IEXEC)

        chown_to_user(output_file)

        return output_file
