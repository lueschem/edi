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
from edi.lib.helpers import (print_success, chown_to_user)
import apt
import apt_inst
import tempfile
import os


class Fetch(Qemu):

    @classmethod
    def advertise(cls, subparsers):
        help_text = "fetch a qemu binary"
        description_text = "Fetch a qemu binary."
        parser = subparsers.add_parser(cls._get_short_command_name(),
                                       help=help_text,
                                       description=description_text)
        cls._require_config_file(parser)

    def run_cli(self, cli_args):
        result = self.run(cli_args.config_file)

    def run(self, config_file):
        self._setup_parser(config_file)

        qemu_package = self.config.get_qemu_package_name()
        print("Going to fetch qemu Debian package ({}).".format(qemu_package))

        workdir = self.config.get_workdir()

        with tempfile.TemporaryDirectory(dir=workdir) as tempdir:
            chown_to_user(tempdir)

            apt_path = os.path.join(tempdir, 'etc', 'apt')
            os.makedirs(apt_path)

            sources_list_path = os.path.join(apt_path, 'sources.list')
            qemu_repository = self.config.get_qemu_repository()

            with open(sources_list_path, encoding='utf-8', mode='w') as f:
                if qemu_repository:
                    f.write(qemu_repository)
                else:
                    f.write(self.config.get_bootstrap_repository())

            cache = apt.Cache(rootdir=tempdir, memonly=True)
            cache.update()
            cache.open()

            pkg = cache[qemu_package]
            # TODO:
            # - Error handling
            # - Proxy handling
            # - Binary extraction
            # - Trust check
            # - Keyring handling
            print('{0} is trusted: {1}'.format(qemu_package, pkg.candidate.origins[0].trusted))
            print(pkg.candidate.uri)
            package_file = pkg.candidate.fetch_binary(destdir=workdir)
            apt_inst.DebFile(package_file).data.extractall(workdir)

        print_success("Fetched qemu binary {}.".format(self._result()))
        return self._result()

    def _result(self):
        return "None"
