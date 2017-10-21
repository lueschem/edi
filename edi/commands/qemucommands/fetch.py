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

from edi.commands.qemu import Qemu
from edi.lib.helpers import (print_success, chown_to_user, FatalError, get_workdir,
                             get_artifact_dir, create_artifact_dir)
from edi.lib.shellhelpers import get_debian_architecture
import apt_inst
import tempfile
import os
import logging
import shutil
from edi.lib.debhelpers import PackageDownloader


class Fetch(Qemu):

    @classmethod
    def advertise(cls, subparsers):
        help_text = "fetch a QEMU binary"
        description_text = "Fetch a QEMU binary."
        parser = subparsers.add_parser(cls._get_short_command_name(),
                                       help=help_text,
                                       description=description_text)
        cls._offer_introspection_options(parser)
        cls._require_config_file(parser)

    def dry_run_cli(self, cli_args):
        return self.dry_run(cli_args.config_file)

    def dry_run(self, config_file):
        self._setup_parser(config_file)
        plugins = {}
        return plugins

    def run_cli(self, cli_args):
        self.run(cli_args.config_file, introspection_method=self._get_introspection_method(cli_args))

    def run(self, config_file, introspection_method=None):
        self._setup_parser(config_file)

        if introspection_method:
            self._print(introspection_method())
            return self._result()

        if not self._needs_qemu():
            return None

        if os.path.isfile(self._result()):
            logging.info(("{0} is already there. "
                          "Delete it to re-fetch it."
                          ).format(self._result()))
            return self._result()

        qemu_package = self.config.get_qemu_package_name()
        print("Going to fetch qemu Debian package ({}).".format(qemu_package))

        workdir = get_workdir()

        with tempfile.TemporaryDirectory(dir=workdir) as tempdir:
            chown_to_user(tempdir)

            qemu_repository = self.config.get_qemu_repository()

            if qemu_repository:
                key_url = self.config.get_qemu_repository_key()
            else:
                qemu_repository = self.config.get_bootstrap_repository()
                key_url = self.config.get_bootstrap_repository_key()

            d = PackageDownloader(repository=qemu_repository, repository_key=key_url,
                                  architectures=[get_debian_architecture()])
            package_file = d.download(package_name=qemu_package, dest=tempdir)

            apt_inst.DebFile(package_file).data.extractall(tempdir)
            qemu_binary = os.path.join(tempdir, 'usr', 'bin', self._get_qemu_binary_name())
            chown_to_user(qemu_binary)
            create_artifact_dir()
            shutil.move(qemu_binary, self._result())

        print_success("Fetched qemu binary {}.".format(self._result()))
        return self._result()

    def clean(self, config_file):
        self._setup_parser(config_file)

        result = self._result()
        if not result:
            return
        elif os.path.isfile(result):
            logging.info("Removing '{}'.".format(result))
            os.remove(result)
            print_success("Removed QEMU binary {}.".format(result))

    def _result(self):
        if not self._needs_qemu():
            return None
        else:
            return os.path.join(get_artifact_dir(), self._get_qemu_binary_name())

    def _get_qemu_binary_name(self):
        arch_dict = {'amd64': 'x86_64',
                     'arm64': 'aarch64',
                     'armel': 'arm',
                     'armhf': 'arm',
                     'i386': 'i386',
                     'mips': 'mips',
                     'mipsel': 'mipsel',
                     'powerpc': 'ppc',
                     'ppc64el': 'ppc64le',
                     's390x': 's390x'}
        debian_arch = self.config.get_bootstrap_architecture()
        qemu_arch = arch_dict.get(debian_arch)
        if not qemu_arch:
            raise FatalError('Unable to derive QEMU architecture form Debian architecture ({}).'.format(debian_arch))

        return 'qemu-{}-static'.format(qemu_arch)

    def _needs_qemu(self):
        host_architecture = get_debian_architecture()
        container_architecture = self.config.get_bootstrap_architecture()
        if host_architecture == container_architecture:
            return False
        elif host_architecture == 'amd64' and container_architecture == 'i386':
            return False
        else:
            return True
