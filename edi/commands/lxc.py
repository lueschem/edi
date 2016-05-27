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


class Lxc(EdiCommand):

    """
    Note: python3-pylxd version 2.0.0-0ubuntu1 does currently have some issues
    with python3. As soon as
    https://github.com/lxc/pylxd/commit/96a44e4755252e45db7aec027390a01722289823
    gets released with a new Debian package, we can try to replace the shell
    stuff within the subcommands with pylxd calls.
    """

    @classmethod
    def advertise(cls, subparsers):
        help_text = "run lxc related operations"
        description_text = "Run edi images within lxc."
        parser = subparsers.add_parser(cls._get_short_command_name(),
                                       help=help_text,
                                       description=description_text)

        cls._add_sub_commands(parser)

    def run_cli(self, cli_args):
        self._run_sub_command_cli(cli_args)
