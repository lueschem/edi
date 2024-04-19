# -*- coding: utf-8 -*-
# Copyright (C) 2018 Matthias Luescher
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

import click
import os
import logging
import subprocess
import tempfile
import yaml
from codecs import open
from edi.lib.helpers import chown_to_user, FatalError
from edi.lib.helpers import print_error, get_user, get_workdir
from edi.lib.shellhelpers import run, require
from edi.lib.sharedfoldercoordinator import SharedFolderCoordinator
from edi.lib.configurationparser import remove_passwords


class PlaybookRunner:

    def __init__(self, config, target, connection):
        self.config = config
        self.target = target
        self.connection = connection
        self.config_section = 'playbooks'

    def run_all(self):
        workdir = get_workdir()

        applied_playbooks = []
        with tempfile.TemporaryDirectory(dir=workdir) as tempdir:
            chown_to_user(tempdir)
            inventory = self._write_inventory_file(tempdir)

            collected_playbooks = self._get_playbooks()

            if len(collected_playbooks) > 1 and self.config.get_start_task():
                raise FatalError("The -s/--start-at-task feature is currently only available for configurations "
                                 "that contain just one playbook!")

            for name, path, extra_vars, in collected_playbooks:
                logging.info(("Running playbook {} located in "
                              "{} with extra vars:\n{}"
                              ).format(name, path,
                                       yaml.dump(remove_passwords(extra_vars),
                                                 default_flow_style=False)))

                extra_vars_file = os.path.join(tempdir, ("extra_vars_{}"
                                                         ).format(name))
                with open(extra_vars_file, encoding='utf-8', mode='w') as f:
                    f.write(yaml.dump(extra_vars))

                ansible_user = extra_vars.get("edi_config_management_user_name")
                self._run_playbook(path, inventory, extra_vars_file, ansible_user)
                applied_playbooks.append(name)

        return applied_playbooks

    def _get_playbooks(self):
        augmented_list = []
        playbook_list = self.config.get_ordered_path_items(self.config_section)
        for name, path, extra_vars, _ in playbook_list:
            sfc = SharedFolderCoordinator(self.config)
            extra_vars['edi_shared_folder_mountpoints'] = sfc.get_mountpoints()
            augmented_list.append((name, path, extra_vars))

        return augmented_list

    def get_plugin_report(self):
        result = {}

        playbooks = self._get_playbooks()

        if playbooks:
            result[self.config_section] = []

        for name, path, extra_vars in playbooks:
            plugin_info = {name: {'path': path, 'dictionary': extra_vars}}

            result[self.config_section].append(plugin_info)

        return result

    @require("ansible-playbook", "'sudo apt install ansible'")
    def _run_playbook(self, playbook, inventory, extra_vars, ansible_user):
        snap_path = '/snap/bin'
        cmd = list()
        # on a Debian system the snap path might not be found in the PATH variable
        if snap_path not in os.environ['PATH']:
            cmd.extend(["env", "PATH={}:{}".format(os.environ['PATH'], snap_path)])
        cmd.append("ansible-playbook")

        start_task = self.config.get_start_task()
        if start_task:
            cmd.extend(["--start-at-task", start_task])

        cmd.extend(["--connection", self.connection])
        cmd.extend(["--inventory", inventory])
        cmd.extend(["--extra-vars", "@{}".format(extra_vars)])
        if self.connection == "ssh":
            cmd.extend(["--user", ansible_user])
        cmd.append(playbook)
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            cmd.append("-vvvv")

        ansible_env = os.environ.copy()
        ansible_env['ANSIBLE_REMOTE_TEMP'] = '/tmp/ansible-{}'.format(get_user())

        while True:
            try:
                run(cmd, env=ansible_env, log_threshold=logging.INFO)
                break
            except subprocess.CalledProcessError as error:
                if self.config.debug_mode():
                    print_error("{}\nFor more information increase the log level.".format(error))
                    click.echo('You can now fix the playbook and press "r" to retry. Hit any other key to abort: ',
                               nl=False)
                    input_char = click.getchar()
                    click.echo()
                    if input_char.lower() == 'r':
                        pass
                    else:
                        raise KeyboardInterrupt
                else:
                    raise error

    def _write_inventory_file(self, tempdir):
        inventory_file = os.path.join(tempdir, "inventory")
        with open(inventory_file, encoding='utf-8', mode='w') as f:
            f.write("[edi]\n{}\n".format(self.target))
        chown_to_user(inventory_file)
        return inventory_file
