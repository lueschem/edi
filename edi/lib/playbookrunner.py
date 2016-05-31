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

import os
import logging
import tempfile
import yaml
from codecs import open
from edi.lib.helpers import chown_to_user
from docutils.parsers.rst.directives import path
from edi.lib.helpers import print_error_and_exit, require_executable
from edi.lib.shellhelpers import run, resolv_conf


class PlaybookRunner():

    def __init__(self, config, target, environment,
                 running_in_chroot=False):
        self.config = config
        self.target = target
        self.environment = environment
        self.running_in_chroot = running_in_chroot

    def run_all(self):
        workdir = self.config.get_workdir()

        with tempfile.TemporaryDirectory(dir=workdir) as tempdir:
            chown_to_user(tempdir)
            inventory = self._write_inventory_file(tempdir)

            for k, v in self.config.get_playbooks().items():
                logging.info("Running playbook {}".format(k))
                path = v.get("path", None)
                assert path is not None
                tool = v.get("tool", "ansible")
                assert tool == "ansible"
                playbook = self._resolve_path(path)

                extra_vars = self._write_extra_vars_file(tempdir, k)

                self._run_playbook(playbook, inventory, extra_vars)

    def _run_playbook(self, playbook, inventory, extra_vars):
        require_executable("ansible-playbook", "sudo apt install ansible")

        cmd = []
        cmd.append("ansible-playbook")
        cmd.extend(["-c", "chroot"])
        cmd.append(playbook)
        cmd.extend(["--inventory", inventory])
        cmd.extend(["--extra-vars", "@{}".format(extra_vars)])
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            cmd.append("-vvvv")

        if self.running_in_chroot:
            with resolv_conf(self.target):
                run(cmd, sudo=self.running_in_chroot)
        else:
            # TODO: implement non chroot version
            assert False

    def _resolve_path(self, path):
        # TODO: generalize for any plugin
        if os.path.isabs(path):
            if not os.path.isfile(path):
                print_error_and_exit(("'{}' does not exist."
                                      ).format(path))
            return path
        else:
            locations = [self.config.get_project_plugin_directory(),
                         self.config.get_edi_plugin_directory()]

            for location in locations:
                abspath = os.path.join(location, path)
                if os.path.isfile(abspath):
                    return abspath

            print_error_and_exit(("'{0}' not found in the "
                                  "following locations:\n{1}"
                                  ).format(path, "\n".join(locations)))

    def _write_inventory_file(self, tempdir):
        inventory_file = os.path.join(tempdir, "inventory")
        with open(inventory_file, encoding='utf-8', mode='w') as f:
            f.write("[edi]\n{}\n".format(self.target))
        chown_to_user(inventory_file)
        return inventory_file

    def _write_extra_vars_file(self, tempdir, playbookname):
        extra_vars_file = os.path.join(tempdir,
                                       "extra_vars_{}".format(playbookname))
        with open(extra_vars_file, encoding='utf-8', mode='w') as f:
            extra_vars = self.config.get_playbook_dictionary(self.environment,
                                                             playbookname)
            f.write(yaml.dump(extra_vars))

        return extra_vars_file
