from pathlib import Path

from cement import Handler
from cgcrepair.core.interfaces import CorpusInterface
from cgcrepair.core.corpus.challenge import Challenge


class CorpusHandler(CorpusInterface, Handler):
    class Meta:
        label = 'corpus'

    def challenge(self, challenge_name: str):
        paths = self.app.config.lib.get_challenge_paths(challenge_name=challenge_name)
        return Challenge(paths=paths)
