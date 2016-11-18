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
from edi.lib.helpers import require_executable, get_user
from edi.lib.shellhelpers import run, host_resolv_conf


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

            playbook_list = self.config.get_ordered_items("playbooks",
                                                          self.environment)
            for name, path, extra_vars in playbook_list:
                logging.info(("Running playbook {} located in "
                              "{} with extra vars:\n{}"
                              ).format(name, path,
                                       yaml.dump(extra_vars,
                                                 default_flow_style=False)))

                extra_vars_file = os.path.join(tempdir, ("extra_vars_{}"
                                                         ).format(name))
                with open(extra_vars_file, encoding='utf-8', mode='w') as f:
                    f.write(yaml.dump(extra_vars))

                self._run_playbook(path, inventory, extra_vars_file)

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

        ansible_env = os.environ.copy()
        ansible_env['ANSIBLE_REMOTE_TEMP'] = '/tmp/ansible-{}'.format(get_user())

        if self.running_in_chroot:
            with host_resolv_conf(self.target):
                run(cmd, sudo=self.running_in_chroot, env=ansible_env)
        else:
            # TODO: implement non chroot version
            assert False

    def _write_inventory_file(self, tempdir):
        inventory_file = os.path.join(tempdir, "inventory")
        with open(inventory_file, encoding='utf-8', mode='w') as f:
            f.write("[edi]\n{}\n".format(self.target))
        chown_to_user(inventory_file)
        return inventory_file
