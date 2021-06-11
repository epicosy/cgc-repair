from cement import Controller, ex
from cement.utils.version import get_version_banner
from ..core.version import get_version

VERSION_BANNER = """
DARPA CGC challenge set extended into a benchmark for Automatic Program Repair tools. %s
%s
""" % (get_version(), get_version_banner())


class Base(Controller):
    class Meta:
        label = 'base'

        # text displayed at the top of --help output
        description = 'DARPA CGC challenge set extended into a benchmark for Automatic Program Repair tools.'

        # text displayed at the bottom of --help output
        epilog = 'Usage: cgcrepair command1 --foo bar'

        # controller level arguments. ex: 'cgcrepair --version'
        arguments = [
            ### add a version banner
            (['-v', '--version'], {'action': 'version', 'version': VERSION_BANNER}),
            (['-vb', '--verbose'], {'help': 'Verbose output.', 'action': 'store_true'}),
            (['-ns', '--no_status'], {'help': 'No status output.', 'action': 'store_true'}),
            (['--excl'], {'help': 'Flag for not skipping excluded challenges.', 'action': 'store_true'})
        ]

    def _default(self):
        """Default action if no sub-command is passed."""

        self.app.args.print_help()
