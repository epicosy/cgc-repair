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

    @ex(
        help='example sub command1',

        # sub-command level arguments. ex: 'cgcrepair command1 --foo bar'
        arguments=[
            ### add a sample foo option under subcommand namespace
            (['-f', '--foo'],
             {'help': 'notorious foo option',
              'action': 'store',
              'dest': 'foo'}),
        ],
    )
    def command1(self):
        """Example sub-command."""

        commands_handler = self.app.handler.get('commands', 'commands', setup=True)
        out, err, dur = commands_handler(cmd_str='ping www.google.com', msg='test command', timeout=5)
        self.app.log.warning(dur)
