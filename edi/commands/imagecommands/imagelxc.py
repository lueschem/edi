# -*- coding: utf-8 -*-
# Copyright (C) 2016 Matthias Luescher
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
import os
import tempfile
import time
import calendar
import yaml
import shutil
import glob
from jinja2 import Template
from codecs import open
from edi.commands.image import Image
from edi.commands.imagecommands.bootstrap import Bootstrap
from edi.lib.helpers import chown_to_user


class Lxc(Image):

    @classmethod
    def advertise(cls, subparsers):
        help_text = "upgrade a bootstrap image to a lxc image"
        description_text = "Upgrade a bootstrap image to a lxc image."
        parser = subparsers.add_parser(cls._get_short_command_name(),
                                       help=help_text,
                                       description=description_text)
        cls._require_config_file(parser)

    def run_cli(self, cli_args):
        result = self.run(cli_args.config_file)
        print("Generated {0}.".format(result))

    def run(self, config_file):
        self._setup_parser(config_file)

        if os.path.isfile(self._result()):
            logging.info(("{0} is already there. "
                          "Delete it to regenerate it."
                          ).format(self._result()))
            return self._result()

        self._require_sudo()

        bootstrap_cmd = Bootstrap()

        # This command is based upon the output of the bootstrap command
        bootstrap_result = bootstrap_cmd.run(config_file)

        workdir = self.config.get_workdir()

        with tempfile.TemporaryDirectory(dir=workdir) as tempdir:
            chown_to_user(tempdir)
            lxcimagedir = os.path.join(tempdir, "lxcimage")
            rootfsdir = self._unpack_image(bootstrap_result, lxcimagedir)
            self._write_container_metadata(lxcimagedir)
            archive = self._pack_image(tempdir, lxcimagedir)
            chown_to_user(archive)
            shutil.move(archive, self._result())

        return self._result()

    def clean(self, config_file):
        self._setup_parser(config_file)

        if os.path.isfile(self._result()):
            logging.info("Removing '{}'.".format(self._result()))
            os.remove(self._result())

    def _result(self):
        archive_name = ("{0}_{1}.tar.{2}"
                        ).format(self.config.get_project_name(),
                                 self._get_command_file_name_prefix(),
                                 self.config.get_compression())
        return os.path.join(self.config.get_workdir(), archive_name)

    def _write_container_metadata(self, imagedir):
        metadata = {}
        metadata["architecture"] = self.config.get_architecture()
        metadata["creation_date"] = calendar.timegm(time.gmtime())

        template_node = {}
        template_list = self.config.get_ordered_items("lxc_templates",
                                                      "edi_env_lxc")

        if template_list:
            templates_dest = os.path.join(imagedir, "templates")
            os.mkdir(templates_dest)

        for name, path, dictionary in template_list:
            logging.info(("Loading template {} located in "
                          "{} with dictionary:\n{}"
                          ).format(name, path,
                                   yaml.dump(dictionary,
                                             default_flow_style=False)))

            with open(path, encoding="UTF-8", mode="r") as template_file:
                template = Template(template_file.read())
                sub_node = yaml.load(template.render(dictionary))

            template_node = dict(template_node, **sub_node)

            templates_src = os.path.dirname(path)

            tpl_files = glob.iglob(os.path.join(templates_src, "*.tpl"))
            for tpl_file in tpl_files:
                if os.path.isfile(tpl_file):
                    shutil.copy(tpl_file, templates_dest)

        if template_node:
            metadata["templates"] = template_node

        metadatafile = os.path.join(imagedir, "metadata.yaml")

        with open(metadatafile, encoding='utf-8', mode='w') as f:
            f.write(yaml.dump(metadata))
