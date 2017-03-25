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
import yaml
from codecs import open
from edi.lib.helpers import FatalError, get_edi_plugin_directory


placeholder = 'PROJECTNAME'


def get_available_templates():
    template_dir = os.path.join(get_edi_plugin_directory(), 'config_templates')
    all_items = os.listdir(template_dir)
    templates = []
    for item in all_items:
        name, extension = os.path.splitext(item)
        if extension == '.yml':
            templates.append(name)

    return templates


def get_template(name):
    return os.path.join(get_edi_plugin_directory(), 'config_templates', '{}.yml'.format(name))


def get_project_tree():
    return os.path.join(get_edi_plugin_directory(), 'config_templates', 'project_tree')


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
        self._walk_over_files(self._replace_edilink, dictionary, self._is_edilink)
        self._walk_over_files(self._hide_edihidden, dictionary, self._is_edihidden)
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
    def _is_edilink(path):
        _, extension = os.path.splitext(path)
        return extension == '.edilink'

    @staticmethod
    def _is_edihidden(path):
        _, extension = os.path.splitext(path)
        return extension == '.edihidden'

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
    def _replace_edilink(path, **_):
        with open(path, mode='r', encoding='utf-8') as link_file:
            link_target = yaml.load(link_file.read()).get('link')

        new_link, _ = os.path.splitext(path)
        os.remove(path)
        os.symlink(link_target, new_link)
        return new_link

    @staticmethod
    def _hide_edihidden(path, **_):
        directory = os.path.dirname(path)
        filename, _ = os.path.splitext(os.path.basename(path))
        new_file = os.path.join(directory, '.{}'.format(filename))
        os.rename(path, new_file)
        return new_file

    @staticmethod
    def _no_operation(path, **kwargs):
        return path