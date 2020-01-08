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
        cls._offer_options(parser, introspection=True, clean=True)
        cls._require_config_file(parser)

    def run_cli(self, cli_args):
        self._dispatch(*self._unpack_cli_args(cli_args), run_method=self._get_run_method(cli_args))

    def dry_run(self, config_file):
        return self._dispatch(config_file, run_method=self._dry_run)

    @staticmethod
    def _dry_run():
        return {}

    def run(self, config_file):
        return self._dispatch(config_file, run_method=self._run)

    def _run(self):
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
            if not os.path.isdir(self._result_folder()):
                os.mkdir(self._result_folder())
                chown_to_user(self._result_folder())

            shutil.move(qemu_binary, self._result())

        print_success("Fetched qemu binary {}.".format(self._result()))
        return self._result()

    def clean_recursive(self, config_file, depth):
        self.clean_depth = depth
        self._dispatch(config_file, run_method=self._clean)

    def clean(self, config_file):
        self._dispatch(config_file, run_method=self._clean)

    def _clean(self):
        result_folder = self._result_folder()
        if not result_folder:
            return
        elif os.path.isdir(result_folder):
            logging.info("Removing '{}'.".format(result_folder))
            shutil.rmtree(result_folder)
            print_success("Removed QEMU binary folder {}.".format(result_folder))

    def _dispatch(self, config_file, run_method):
        self._setup_parser(config_file)
        return run_method()

    def _result_folder(self):
        if not self._needs_qemu():
            return None
        else:
            folder_name = "{0}_{1}".format(self.config.get_configuration_name(),
                                           self._get_command_file_name_prefix())
            return os.path.join(get_artifact_dir(), folder_name)

    def _result(self):
        if not self._needs_qemu():
            return None
        else:
            return os.path.join(self._result_folder(), self._get_qemu_binary_name())

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
        if not self.config.has_bootstrap_node():
            return False
        host_architecture = get_debian_architecture()
        container_architecture = self.config.get_bootstrap_architecture()
        if host_architecture == container_architecture:
            return False
        elif host_architecture == 'amd64' and container_architecture == 'i386':
            return False
        else:
            return True
