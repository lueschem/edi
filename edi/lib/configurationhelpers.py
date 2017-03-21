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
import jinja2
from codecs import open
from edi.lib.helpers import FatalError


placeholder = 'PROJECTNAME'


class ConfigurationTemplate():
    """
    Transforms a configuration template into a working configuration
    """

    def __init__(self, folder):
        """
        :param folder: The folder that contains a *copy* of the configuration template files.
        """
        self._folder = os.path.abspath(folder)

    def render(self, dictionary):
        """
        Renders the configuration template "in place".
        :param dictionary: the dictionary that gets applied during the rendering operations
        :return: list: returns a list of the resulting files
        """
        if not dictionary.get('edi_project_name'):
            raise FatalError('''Missing or empty dictionary entry 'edi_project_name'!''')

        self._walk_over_files(self._render_jinja2, dictionary, self._is_real_file)
        self._walk_over_files(self._rename_file, dictionary, os.path.isfile)
        self._walk_over_files(self._rename_file, dictionary, os.path.islink) # dangling links!
        self._walk_over_files(self._relink_file, dictionary, os.path.islink)
        return self._walk_over_files(self._no_operation)

    def _walk_over_files(self, operation, dictionary={}, custom_filter=None):
        def _filter_it(path):
            return not custom_filter or custom_filter and custom_filter(path)

        touched_files = []
        for root, dirs, files in os.walk(self._folder, topdown=False):
            for name in files:
                path = os.path.join(root, name)
                if _filter_it(path):
                    touched_files.append(operation(path, **dictionary))
            for name in dirs:
                path = os.path.join(root, name)
                if _filter_it(path):
                    touched_files.append(operation(path, **dictionary))

        return touched_files

    @staticmethod
    def _is_real_file(path):
        return os.path.isfile(path) and not os.path.islink(path)

    @staticmethod
    def _render_jinja2(path, **kwargs):
        dictionary = kwargs
        with open(path, encoding="UTF-8", mode="r") as template_file:
            template = jinja2.Template(template_file.read(), trim_blocks=True, lstrip_blocks=True)
            result = template.render(dictionary)

        with open(path, encoding="UTF-8", mode="w") as result_file:
            result_file.write(result)

        return path

    @staticmethod
    def _rename_file(path, edi_project_name=None, **_):
        directory = os.path.dirname(path)
        filename = os.path.basename(path)
        if placeholder in filename:
            newpath = os.path.join(directory, filename.replace(placeholder, edi_project_name))
            os.rename(path, newpath)
            return newpath
        else:
            return path

    @staticmethod
    def _relink_file(path, edi_project_name=None, **_):
        link = os.readlink(path)
        if placeholder in link:
            newlink = link.replace(placeholder, edi_project_name)
            os.remove(path)
            os.symlink(newlink, path)

        return path

    @staticmethod
    def _no_operation(path, **kwargs):
        return path