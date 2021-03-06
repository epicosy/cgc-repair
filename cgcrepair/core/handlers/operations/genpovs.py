from cgcrepair.core.corpus.challenge import Challenge
from cgcrepair.core.exc import CommandError
from cgcrepair.core.handlers.commands import CommandsHandler


class GenPOVsHandler(CommandsHandler):
    class Meta:
        label = 'genpovs'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.out_dir = None
        self.polls = []

    def set(self, m32: bool = False):
        super().set()
        self.m32 = m32

    def run(self, challenge: Challenge):
        try:
            compile_handler = self.app.handler.get('commands', 'compile', setup=True)

            if self.m32:
                compile_handler.env["M32"] = "True"

            compile_handler.set()
            compile_handler.build_povs(challenge)

            if compile_handler.error:
                raise CommandError(compile_handler.error)

        except CommandError as ce:
            self.error = str(ce)
        finally:
            self.unset()

    def unset(self):
        super(GenPOVsHandler, self).unset()
