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

from edi.lib.configurationparser import ConfigurationParser
from edi.lib.commandrunner import CommandRunner
from edi.lib.artifact import ArtifactType, Artifact
from tests.libtesting.contextmanagers.workspace import workspace
from tests.libtesting.helpers import get_command, suppress_chown_during_debuild
from edi.lib import mockablerun
from edi.lib.helpers import FatalError
import subprocess
import os
from codecs import open
import pytest


def test_run_and_clean(config_files, monkeypatch):
    def intercept_command_run(*popenargs, **kwargs):
        if "command" in get_command(popenargs):
            print(popenargs)
            with open(get_command(popenargs), encoding='utf-8') as f:
                print(f.read())
            return subprocess.run(*popenargs, **kwargs)
        else:
            return subprocess.run(*popenargs, **kwargs)

    monkeypatch.setattr(mockablerun, 'run_mockable', intercept_command_run)

    suppress_chown_during_debuild(monkeypatch)

    with workspace() as workdir:
        with open(config_files, "r") as main_file:
            parser = ConfigurationParser(main_file)

            input_file = os.path.join(workdir, 'input.txt')
            with open(input_file, mode='w', encoding='utf-8') as i:
                i.write("*input file*\n")

            runner = CommandRunner(parser, 'postprocessing_commands', Artifact(name='edi_input_artifact',
                                                                               location=input_file,
                                                                               type=ArtifactType.PATH))

            artifacts = runner.run()

            assert os.path.isfile(os.path.join('artifacts', 'first.txt'))
            assert os.path.isfile(os.path.join('artifacts', 'last.txt'))

            def verify_last_artifact(artifact):
                assert str(workdir) in str(artifact.location)
                assert 'artifacts/last.txt' in str(artifact.location)
                assert 'last.txt' in str(artifact.location)

                with open(artifact.location, mode='r') as result_file:
                    content = result_file.read()
                    assert "*input file*" in content
                    assert "*first step*" in content
                    assert "*second step*" in content
                    assert "*last step*" in content

            verify_last_artifact(artifacts[-1])

            first_file = os.path.join('artifacts', 'first.txt')
            first_folder = os.path.join('artifacts', 'first_folder')
            os.remove(first_file)
            os.rmdir(first_folder)

            runner.run()
            assert os.path.isfile(first_file)
            assert os.path.isdir(first_folder)
            runner.clean()
            assert not os.path.isfile(os.path.join('artifacts', 'last.txt'))
            assert not os.path.isfile(first_file)
            assert not os.path.isdir(first_folder)


def test_plugin_report(config_files):
    with open(config_files, "r") as main_file:
        parser = ConfigurationParser(main_file)

        input_file = os.path.join(os.sep, 'fake_folder', 'input.txt')

        runner = CommandRunner(parser, 'postprocessing_commands', Artifact(name='edi_input_artifact',
                                                                           location=input_file, type=ArtifactType.PATH))

        output = runner.get_plugin_report()
        commands = output.get('postprocessing_commands', [])
        assert len(commands) == 3
        assert next(iter(commands[0].keys())) == '10_first_command'
        assert next(iter(commands[1].keys())) == '20_second_command'
        assert next(iter(commands[2].keys())) == '40_last_command'


def test_require_root(config_files):
    with open(config_files, "r") as main_file:
        parser = ConfigurationParser(main_file)

        input_file = os.path.join(os.sep, 'fake_folder', 'input.txt')

        runner = CommandRunner(parser, 'postprocessing_commands', Artifact(name='edi_input_artifact',
                                                                           location=input_file, type=ArtifactType.PATH))
        assert not runner.require_real_root()
        assert not runner.require_real_root_for_clean()


@pytest.mark.parametrize("artifact_item, expected_type, expected_location", [
    ('foo', ArtifactType.PATH, 'foo'),
    ({'location': 'bar'}, ArtifactType.PATH, 'bar'),
    ({'location': 'bingo:bongo', 'type': 'buildah-container'}, ArtifactType.BUILDAH_CONTAINER, 'bingo:bongo'),
])
def test_output_node(artifact_item, expected_type, expected_location):
    artifact = CommandRunner._get_artifact('some_node', 'some_key', artifact_item)
    assert artifact.type is expected_type
    assert expected_location in artifact.location
    assert artifact.name == 'some_key'


@pytest.mark.parametrize("artifact_item, error_message", [
    ('', 'must not be empty'),
    ({'location': ''}, 'must not be empty'),
    ({'location': 'bingo/bongo'}, 'shall be a file or a folder'),
    ({'location': 'bingo:bongo', 'type': 'unknown-artifact'}, 'invalid artifact type'),
])
def test_output_node_failure(artifact_item, error_message):
    with pytest.raises(FatalError) as error:
        CommandRunner._get_artifact('some_node', 'some_key', artifact_item)
    assert error_message in str(error)
