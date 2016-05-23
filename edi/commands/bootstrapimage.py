# -*- coding: utf-8 -*-
# Copyright (C) 2016 Matthias Luescher
#
# Authors:
#  Matthias Luescher
#
# This file is part of edi.
#
# edi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# edi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with edi.  If not, see <http://www.gnu.org/licenses/>.

import tempfile
import requests
import os
import gnupg
import shutil
import logging
from edi.lib.edicommand import EdiCommand
from edi.lib.helpers import (require_executable, print_error_and_exit,
                             chown_to_user)
from edi.lib.shellhelpers import run, mount_proc_sys_dev, get_chroot_cmd


class BootstrapImage(EdiCommand):

    @classmethod
    def advertise(cls, subparsers):
        help_text = "bootstrap an initial image"
        description_text = "Bootstrap an initial image."
        parser = subparsers.add_parser(cls._get_command_name(),
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

        if self.config.get_bootstrap_tool() != "debootstrap":
            print_error_and_exit(("At the moment only debootstrap "
                                  "is supported for bootstrapping!"))

        require_executable("debootstrap", "sudo apt install debootstrap")

        workdir = self.config.get_workdir()

        with tempfile.TemporaryDirectory(dir=workdir) as tempdir:
            chown_to_user(tempdir)
            key_data = self._fetch_bootstrap_repository_key(tempdir)
            keyring_file = self._build_keyring(tempdir, key_data)
            rootfs = self._run_debootstrap(tempdir, keyring_file)
            self._postprocess_rootfs(rootfs, key_data)
            archive = self._pack_image(tempdir, rootfs)
            chown_to_user(archive)
            shutil.move(archive, self._result())

        return self._result()

    def _result(self):
        archive_name = ("{0}_{1}.tar.{2}"
                        ).format(self.config.get_project_name(),
                                 self._get_command_name(),
                                 self.config.get_compression())
        return os.path.join(self.config.get_workdir(), archive_name)

    def _fetch_bootstrap_repository_key(self, tempdir):
        key_url = self.config.get_bootstrap_repository_key()
        if key_url:
            key_req = requests.get(key_url)
            if key_req.status_code != 200:
                print_error_and_exit(("Unable to fetch repository key '{0}'"
                                      ).format(key_url))

            return key_req.text
        else:
            return None

    def _build_keyring(self, tempdir, key_data):
        if key_data:
            keyring_file = os.path.join(tempdir, "temp_pubring.gpg")
            gpg = gnupg.GPG(gnupghome=tempdir, keyring=keyring_file)
            gpg.encoding = 'utf-8'
            gpg.import_keys(key_data)
            return keyring_file
        else:
            return None

    def _run_debootstrap(self, tempdir, keyring_file):
        additional_packages = "python-minimal"
        rootfs = os.path.join(tempdir, "rootfs")
        components = ",".join(self.config.get_bootstrap_components())

        cmd = []
        cmd.append("debootstrap")
        cmd.append("--arch={0}".format(self.config.get_architecture()))
        cmd.append("--variant=minbase")
        cmd.append("--include={0}".format(additional_packages))
        cmd.append("--components={0}".format(components))
        if keyring_file:
            cmd.append("--force-check-gpg")
            cmd.append("--keyring={0}".format(keyring_file))
        cmd.append(self.config.get_distribution())
        cmd.append(rootfs)
        cmd.append(self.config.get_bootstrap_uri())
        run(cmd, sudo=True)
        return rootfs

    def _postprocess_rootfs(self, rootfs, key_data):
        with mount_proc_sys_dev(rootfs):
            if key_data:
                key_cmd = get_chroot_cmd(rootfs)
                key_cmd.append("apt-key")
                key_cmd.append("add")
                key_cmd.append("-")
                run(key_cmd, input=key_data, sudo=True)

            clean_cmd = get_chroot_cmd(rootfs)
            clean_cmd.append("apt-get")
            clean_cmd.append("clean")
            run(clean_cmd, sudo=True)
