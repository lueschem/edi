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

command_registry = {}


class CommandFactory(type):
    """Command factory metaclass

    Metaclass that adds all commands to the command registry.
    """

    def __new__(cls, clsname, bases, attrs):
        new_class = super(CommandFactory, cls).__new__(cls, clsname,
                                                       bases, attrs)
        if clsname != "EdiCommand":
            command_registry[clsname.lower()] = new_class
        return new_class
