from pathlib import Path

from cgcrepair.core.corpus.challenge import Challenge
from cgcrepair.core.exc import CommandError
from cgcrepair.core.handlers.commands import CommandsHandler
from cgcrepair.utils.data import ChallengePaths


class GenPOVsHandler(CommandsHandler):
    class Meta:
        label = 'genpovs'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.out_dir = None
        self.polls = []

    def set(self):
        super().set()

    def run(self, challenge: Challenge):
        try:
            compile_handler = self.app.handler.get('commands', 'compile', setup=True)

            self.app.pargs.replace = None
            self.app.pargs.save_temps = None
            self.app.pargs.coverage = None
            self.app.pargs.fix_files = None

            compile_handler.set()
            compile_handler.build_povs(challenge)

            if compile_handler.error:
                raise CommandError(compile_handler.error)

        except CommandError as ce:
            self.error = str(ce)
        finally:
            self.unset()
