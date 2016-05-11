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

from edi.lib.edicommand import EdiCommand
from edi.lib.helpers import require_executable, print_error_and_exit
import tempfile
import requests
import codecs
import subprocess


class BootstrapImage(EdiCommand):

    @classmethod
    def advertise(cls, subparsers):
        help_text = "bootstrap an initial image"
        description_text = "Bootstrap an initial image."
        parser = subparsers.add_parser(cls.__name__.lower(),
                                       help=help_text,
                                       description=description_text)
        cls.require_config_file(parser)

    def run(self):
        self.require_sudo()

        require_executable("debootstrap", "sudo apt install debootstrap")

        workdir = self.config.get_workdir()

        with tempfile.TemporaryDirectory(dir=workdir) as tempdir:
            key_file = self._fetch_bootstrap_repository_key(tempdir)
            result1 = subprocess.run(["cat", key_file], stdout=subprocess.PIPE)
            print(result1)
            result2 = subprocess.run(["cat", key_file], stdout=subprocess.PIPE, universal_newlines=True)
            print(result2)
            result3 = subprocess.run(["/home/lueschem/workspace/edi/bin/edi", "bootstrapimage", "--help"], stdout=subprocess.PIPE, universal_newlines=True)
            print(result3)
            print(result3.stdout)
            result0 = subprocess.run(["sudo", "-u", "lueschem", "cat", key_file], stdout=subprocess.PIPE, universal_newlines=True)
            print(result0.stdout)
            print(result0)


    def _fetch_bootstrap_repository_key(self, tempdir):
        key_url = self.config.get_bootstrap_repository_key()
        key_req = requests.get(key_url)
        if key_req.status_code != 200:
            print_error_and_exit(("Unable to fetch repository key '{0}'"
                                  ).format(key_url))

        key_file = "{0}/bootstrap_key.asc".format(tempdir)
        with codecs.open(key_file, "w", key_req.encoding) as f:
            f.write(key_req.text)
        return key_file
