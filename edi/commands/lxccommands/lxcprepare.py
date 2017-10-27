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
from edi.lib.yamlhelpers import LiteralString, normalize_yaml
from edi.lib.helpers import chown_to_user, print_success, get_workdir, get_artifact_dir, create_artifact_dir
from edi.lib.shellhelpers import get_debian_architecture
from edi.lib.configurationparser import remove_passwords


class Lxc(Image):

    def __init__(self):
        self.config_section = 'lxc_templates'

    @classmethod
    def advertise(cls, subparsers):
        help_text = "upgrade a bootstrap image to a lxc image"
        description_text = "Upgrade a bootstrap image to a lxc image."
        parser = subparsers.add_parser(cls._get_short_command_name(),
                                       help=help_text,
                                       description=description_text)
        cls._offer_introspection_options(parser)
        cls._require_config_file(parser)

    def run_cli(self, cli_args):
        self._dispatch(*self._unpack_cli_args(cli_args), run_method=self._get_run_method(cli_args))

    def dry_run(self, config_file):
        return self._dispatch(config_file, run_method=self._dry_run)

    def _dry_run(self):
        plugins = {}
        plugins.update(Bootstrap().dry_run(self.config.get_base_config_file()))
        plugins.update(self._get_plugin_report())
        return plugins

    def run(self, config_file):
        return self._dispatch(config_file, run_method=self._run)

    def _run(self):
        if os.path.isfile(self._result()):
            logging.info(("{0} is already there. "
                          "Delete it to regenerate it."
                          ).format(self._result()))
            return self._result()

        self._require_sudo()

        bootstrap_cmd = Bootstrap()

        # This command is based upon the output of the bootstrap command
        bootstrap_result = bootstrap_cmd.run(self.config.get_base_config_file())

        workdir = get_workdir()

        print("Going to upgrade the bootstrap image to a lxc image.")

        with tempfile.TemporaryDirectory(dir=workdir) as tempdir:
            chown_to_user(tempdir)
            lxcimagedir = os.path.join(tempdir, "lxcimage")
            self._unpack_image(bootstrap_result, lxcimagedir)
            self._write_container_metadata(lxcimagedir)
            archive = self._pack_image(tempdir, lxcimagedir)
            chown_to_user(archive)
            create_artifact_dir()
            shutil.move(archive, self._result())

        print_success("Created lxc image {}.".format(self._result()))
        return self._result()

    def clean(self, config_file):
        self._dispatch(config_file, run_method=self._clean)

    def _clean(self):
        if os.path.isfile(self._result()):
            logging.info("Removing '{}'.".format(self._result()))
            os.remove(self._result())
            print_success("Removed lxc image {}.".format(self._result()))

    def _dispatch(self, config_file, run_method):
        self._setup_parser(config_file)
        return run_method()

    def _result(self):
        archive_name = ("{0}_{1}.tar.{2}"
                        ).format(self.config.get_configuration_name(),
                                 self._get_command_file_name_prefix(),
                                 self.config.get_compression())
        return os.path.join(get_artifact_dir(), archive_name)

    def _write_container_metadata(self, imagedir):
        metadata = {}
        # we build this container for the host architecture
        # (QEMU makes sure that the binaries of a foreign architecture can also run)
        metadata["architecture"] = get_debian_architecture()
        metadata["creation_date"] = calendar.timegm(time.gmtime())

        template_node = {}
        template_list = self._get_templates()

        if template_list:
            templates_dest = os.path.join(imagedir, "templates")
            os.mkdir(templates_dest)

        for template, name, path, dictionary in template_list:
            logging.info(("Loading template {} located in "
                          "{} with dictionary:\n{}"
                          ).format(name, path,
                                   yaml.dump(remove_passwords(dictionary),
                                             default_flow_style=False)))

            sub_node = yaml.load(template)
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

    def _get_templates(self):
        collected_templates = []
        template_list = self.config.get_ordered_path_items(self.config_section)
        for name, path, dictionary, _ in template_list:
            with open(path, encoding="UTF-8", mode="r") as template_file:
                t = Template(template_file.read())
                template_text = normalize_yaml(t.render(dictionary))
                collected_templates.append((template_text, name, path, dictionary))

        return collected_templates

    def _get_plugin_report(self):
        result = {}
        templates = self._get_templates()

        if templates:
            result[self.config_section] = []

        for template in templates:
            template_text, name, path, dictionary = template

            plugin_info = {name: {'path': path, 'dictionary': dictionary, 'result': LiteralString(template_text)}}

            result[self.config_section].append(plugin_info)

        return result
