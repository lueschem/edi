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

import tempfile
import os
import shutil
import logging
from codecs import open
from aptsources.sourceslist import SourceEntry
from edi.commands.image import Image
from edi.commands.qemucommands.fetch import Fetch
from edi.lib.helpers import (require_executable, FatalError,
                             chown_to_user, print_success)
from edi.lib.shellhelpers import run, get_chroot_cmd
from edi.lib.keyhelpers import fetch_repository_key, build_keyring


class Bootstrap(Image):

    @classmethod
    def advertise(cls, subparsers):
        help_text = "bootstrap an initial image"
        description_text = "Bootstrap an initial image."
        parser = subparsers.add_parser(cls._get_short_command_name(),
                                       help=help_text,
                                       description=description_text)
        cls._require_config_file(parser)

    def run_cli(self, cli_args):
        self.run(cli_args.config_file)

    def run(self, config_file):
        self._setup_parser(config_file)

        if os.path.isfile(self._result()):
            logging.info(("{0} is already there. "
                          "Delete it to regenerate it."
                          ).format(self._result()))
            return self._result()

        self._require_sudo()

        qemu_executable = Fetch().run(config_file)

        print("Going to bootstrap initial image - be patient.")

        if self.config.get_bootstrap_tool() != "debootstrap":
            raise FatalError(("At the moment only debootstrap "
                              "is supported for bootstrapping!"))

        require_executable("debootstrap", "sudo apt install debootstrap")

        workdir = self.config.get_workdir()

        with tempfile.TemporaryDirectory(dir=workdir) as tempdir:
            chown_to_user(tempdir)
            key_data = fetch_repository_key(self.config.get_bootstrap_repository_key())
            keyring_file = build_keyring(tempdir, "temp_keyring.gpg", key_data)
            rootfs = self._run_debootstrap(tempdir, keyring_file, qemu_executable)
            self._postprocess_rootfs(rootfs, key_data)
            archive = self._pack_image(tempdir, rootfs)
            chown_to_user(archive)
            shutil.move(archive, self._result())

        print_success("Bootstrapped initial image {}.".format(self._result()))

        return self._result()

    def clean(self, config_file):
        self._setup_parser(config_file)

        if os.path.isfile(self._result()):
            logging.info("Removing '{}'.".format(self._result()))
            os.remove(self._result())
            print_success("Removed bootstrap image {}.".format(self._result()))

    def _result(self):
        archive_name = ("{0}_{1}.tar.{2}"
                        ).format(self.config.get_project_name(),
                                 self._get_command_file_name_prefix(),
                                 self.config.get_compression())
        return os.path.join(self.config.get_workdir(), archive_name)

    def _run_debootstrap(self, tempdir, keyring_file, qemu_executable):
        # Ansible uses python on the target system
        # sudo is needed for privilege escalation
        additional_packages = ("python,sudo,netbase,net-tools,iputils-ping,ifupdown,isc-dhcp-client,"
                               "resolvconf,systemd,systemd-sysv,gnupg")
        rootfs = os.path.join(tempdir, "rootfs")
        bootstrap_source = SourceEntry(self.config.get_bootstrap_repository())
        components = ",".join(bootstrap_source.comps)

        cmd = []
        cmd.append("debootstrap")
        cmd.append("--arch={0}".format(self.config.get_bootstrap_architecture()))
        if qemu_executable:
            cmd.append("--foreign")
        cmd.append("--variant=minbase")
        cmd.append("--include={0}".format(additional_packages))
        cmd.append("--components={0}".format(components))
        if keyring_file:
            cmd.append("--force-check-gpg")
            cmd.append("--keyring={0}".format(keyring_file))
        cmd.append(bootstrap_source.dist)
        cmd.append(rootfs)
        cmd.append(bootstrap_source.uri)
        run(cmd, sudo=True, log_threshold=logging.INFO)

        if qemu_executable:
            qemu_target_path = os.path.join(rootfs, "usr", "bin")
            shutil.copy(qemu_executable, qemu_target_path)
            second_stage_cmd = get_chroot_cmd(rootfs)
            second_stage_cmd.append("/debootstrap/debootstrap")
            second_stage_cmd.append("--second-stage")
            run(second_stage_cmd, sudo=True, log_threshold=logging.INFO)

        return rootfs

    def _postprocess_rootfs(self, rootfs, key_data):
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

        apt_list_cmd = get_chroot_cmd(rootfs)
        apt_list_cmd.append("rm")
        apt_list_cmd.append("-rf")
        apt_list_cmd.append("/var/lib/apt/lists/")
        run(apt_list_cmd, sudo=True)

        # after a cross debootstrap /etc/apt/sources.list points
        # to the wrong repository
        sources_list = os.path.join(rootfs, 'etc', 'apt', 'sources.list')
        with open(sources_list, mode='w', encoding='utf-8') as f:
            f.write(('# edi bootstrap repository\n{}\n'
                     ).format(self.config.get_bootstrap_repository()))
