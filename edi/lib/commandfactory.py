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
from edi.lib.helpers import print_error_and_exit

_command_anchor = "edicommand"

_command_registry = {}


def get_command(command):
    return _command_registry.get(command)


def get_sub_commands(parent_command=_command_anchor):
    level = len(parent_command.split("."))
    sub_command_prefix = "{}.".format(parent_command)
    return {k: v for (k, v) in _command_registry.items()
            if k.startswith(sub_command_prefix)
            if len(k.split(".")) == level + 1}


class CommandFactory(type):
    """Command factory metaclass

    Metaclass that adds all commands to the command registry.
    """

    def __new__(cls, clsname, bases, attrs):
        new_class = super(CommandFactory, cls).__new__(cls, clsname,
                                                       bases, attrs)
        if clsname.lower() != _command_anchor:
            new_key = new_class._get_command_name()
            if _command_registry.get(new_key):
                print_error_and_exit(("A command named '{}' has "
                                      "already been registered"
                                      ).format(new_key))
            _command_registry[new_key] = new_class
        return new_class
