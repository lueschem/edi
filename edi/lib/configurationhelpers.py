# -*- coding: utf-8 -*-
# Copyright (C) 2017 Matthias Luescher
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

import os


class ConfigurationTemplate():
    """
    Transforms a configuration template into a working configuration
    """

    def __init__(self, folder):
        """
        :param folder: The folder that contains a *copy* of the configuration template files.
        """
        self._folder = folder

    def render(self, dictionary):
        """
        Renders the configuration template "in place".
        :param dictionary: the dictionary that gets applied during the rendering operations
        """
        print('Files:')
        self._walk_over_files(self._print, dictionary, self._is_real_file)
        print('Directories:')
        self._walk_over_files(self._print, dictionary, os.path.isdir)
        print('Links:')
        self._walk_over_files(self._print, dictionary, os.path.islink)
        print('All:')
        self._walk_over_files(self._print)

    def _walk_over_files(self, operation, dictionary=None, custom_filter=None):
        def _filter_it(path, custom_filter):
            return not custom_filter or custom_filter and custom_filter(path)

        for root, dirs, files in os.walk(self._folder, topdown=False):
            for name in files:
                path = os.path.join(root, name)
                if _filter_it(path, custom_filter=custom_filter):
                    operation(path, dictionary)
            for name in dirs:
                path = os.path.join(root, name)
                if _filter_it(path, custom_filter=custom_filter):
                    operation(path, dictionary)

    @staticmethod
    def _is_real_file(path):
        return os.path.isfile(path) and not os.path.islink(path)

    @staticmethod
    def _print(path, dictionary):
        print('path={}, dict={}.'.format(path, dictionary))

