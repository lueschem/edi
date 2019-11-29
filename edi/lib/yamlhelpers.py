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

import yaml
from edi.lib.helpers import FatalError


class LiteralString(str):
    pass


def literal_string_representer(dumper, data):
    return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='|')


yaml.add_representer(LiteralString, literal_string_representer)


def normalize_yaml(yaml_string):
    """
    Feeds a yaml string through pyyaml to normalize its representation.
    :param yaml_string: string in yaml format
    :return: string in yaml format with pyyaml default_flow_style=False
    """
    return yaml.dump(yaml.safe_load(yaml_string), default_flow_style=False)


def annotated_yaml_load(stream, context_hint):
    """
    Load a yaml configuration and throw a FatalError containing a hint
    if the yaml stream can not be parsed.
    :param stream: A yaml formatted stream.
    :param context_hint: A hint for the user where the yaml configuration comes from.
    :return: The content of the yaml as a Python object.
    """
    try:
        return yaml.safe_load(stream)
    except yaml.parser.ParserError as e:
        raise FatalError("Invalid yaml configuration '{}':\n{}".format(context_hint, str(e))) from e
