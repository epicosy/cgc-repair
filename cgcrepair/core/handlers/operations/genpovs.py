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

    def compile_povs(self, challenge_paths: ChallengePaths):
        challenge = Challenge(challenge_paths)
        compile_handler = self.app.handler.get('commands', 'compile', setup=True)

        self.app.pargs.replace = None
        self.app.pargs.save_temps = None
        self.app.pargs.coverage = None
        self.app.pargs.fix_files = None

        compile_handler.set()
        compile_handler.build_povs(challenge)

        if compile_handler.error:
            raise CommandError(compile_handler.error)

    def run(self):
        try:
            corpus_handler = self.app.handler.get('corpus', 'corpus', setup=True)
            challenge_paths = corpus_handler.get_challenge_paths(self.app.pargs.challenge)

            self.compile_povs(challenge_paths)

        except CommandError as ce:
            self.error = str(ce)
        finally:
            self.unset()
