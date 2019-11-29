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
from edi.lib.helpers import FatalError, copy_tree, print_success
from edi.lib.versionhelpers import get_edi_version, get_stripped_version
from jinja2 import Template
import yaml
from edi.commands.config import Config
from edi.lib.configurationparser import get_base_dictionary
from edi.lib.configurationhelpers import (get_available_templates, get_template,
                                          get_project_tree, ConfigurationTemplate)


class Init(Config):

    @classmethod
    def advertise(cls, subparsers):
        help_text = "initialize a configuration within an empty folder"
        description_text = "Initialize a configuration within an empty folder."
        parser = subparsers.add_parser(cls._get_short_command_name(),
                                       help=help_text,
                                       description=description_text)
        parser.add_argument('project_name')
        parser.add_argument('config_template', choices=get_available_templates())

    def run_cli(self, cli_args):
        self.run(cli_args.project_name, cli_args.config_template)

    def run(self, project_name, config_template):
        workdir = os.getcwd()

        if os.getuid() == 0:
            raise FatalError('Do not initialize a configuration as root!')

        if not os.access(workdir, os.W_OK):
            raise FatalError('''No write access to '{}'.'''.format(workdir))

        if os.listdir(workdir):
            raise FatalError('Please initialize your new configuration within an empty folder!')

        source = get_project_tree()
        copy_tree(source, workdir)
        template = ConfigurationTemplate(workdir)
        with open(get_template(config_template), encoding="UTF-8", mode="r") as template_file:
            t = Template(template_file.read())
            template_dict = yaml.safe_load(t.render(get_base_dictionary())).get('parameters', {})

        template_dict['edi_project_name'] = project_name
        template_dict["edi_edi_version"] = get_stripped_version(get_edi_version())
        template.render(template_dict)

        print_success('''Configuration for project '{}' generated in folder '{}'.'''.format(project_name, workdir))
