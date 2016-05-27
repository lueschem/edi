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

from edi.lib.commandfactory import CommandFactory
from edi.lib.configurationparser import ConfigurationParser
import argparse
import os
from edi.lib.helpers import print_error_and_exit
from edi.lib.shellhelpers import run
from edi.lib.commandfactory import get_sub_commands, get_command


class EdiCommand(metaclass=CommandFactory):

    def _setup_parser(self, config_file, running_in_chroot=False):
        self.config = ConfigurationParser(config_file, running_in_chroot)

    @classmethod
    def _get_command_name(cls):
        assert len(cls.__bases__) == 1
        if EdiCommand in cls.__bases__:
            return cls.__name__.lower()
        else:
            return "{}.{}".format(cls.__bases__[0].__name__.lower(),
                                  cls.__name__.lower())

    @classmethod
    def _get_short_command_name(cls):
        return cls.__name__.lower()

    @classmethod
    def _get_cli_command_string(cls):
        return cls._get_command_name().replace(".", " ")

    @classmethod
    def _get_command_file_name_prefix(cls):
        return cls._get_command_name().replace(".", "_")

    @classmethod
    def _add_sub_commands(cls, parser):
        title = "{} commands".format(cls._get_short_command_name())
        subparsers = parser.add_subparsers(title=title,
                                           dest="sub_command_name")

        for _, command in get_sub_commands(cls._get_command_name()).items():
            command.advertise(subparsers)

    def _run_sub_command(self, cli_args):
        sub_command = "{}.{}".format(self._get_command_name(),
                                     cli_args.sub_command_name)
        cmd = get_command(sub_command)
        cmd().run_cli(cli_args)

    @staticmethod
    def _require_config_file(parser):
        parser.add_argument('config_file',
                            type=argparse.FileType('r', encoding='UTF-8'))

    def _require_sudo(self):
        if os.getuid() != 0:
            print_error_and_exit(("The subcommand '{0}' requires superuser "
                                  "privileges.\n"
                                  "Use 'sudo edi {1} ...'."
                                  ).format(self._get_short_command_name(),
                                           self._get_cli_command_string()))

    def _pack_image(self, tempdir, datadir, name="result"):
        # advanced options such as numeric-owner are not supported by
        # python tarfile library - therefore we use the tar command line tool
        tempresult = "{0}.tar.{1}".format(name,
                                          self.config.get_compression())
        archive_path = os.path.join(tempdir, tempresult)

        cmd = []
        cmd.append("tar")
        cmd.append("--numeric-owner")
        cmd.extend(["-C", datadir])
        cmd.extend(["-acf", archive_path])
        cmd.extend(os.listdir(datadir))
        run(cmd, sudo=True)
        return archive_path

    def _unpack_image(self, image, tempdir, subfolder="rootfs"):
        target_folder = os.path.join(tempdir, subfolder)
        os.makedirs(target_folder, exist_ok=True)

        cmd = []
        cmd.append("tar")
        cmd.append("--numeric-owner")
        cmd.extend(["-C", target_folder])
        cmd.extend(["-axf", image])
        run(cmd, sudo=True)
        return target_folder
