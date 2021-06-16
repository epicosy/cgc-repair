from pathlib import Path

from cement import Handler
from cgcrepair.core.interfaces import CorpusInterface
from cgcrepair.core.corpus.challenge import Challenge
from cgcrepair.utils.data import ChallengePaths


class CorpusHandler(CorpusInterface, Handler):
    class Meta:
        label = 'corpus'

    def has(self, challenge_name: str):
        return challenge_name in self.get_challenges()

    def get(self, challenge_name: str):
        paths = self.get_challenge_paths(challenge_name)
        return Challenge(paths=paths)

    def get_challenges(self):
        corpus_path = Path(self.app.config.get_config('corpus'))
        return [challenge.name for challenge in corpus_path.iterdir() if challenge.is_dir()]

    def get_polls_path(self, challenge_name: str):
        return Path(self.app.config.get_config('polls'), challenge_name, 'poller')

    def get_challenge_paths(self, challenge_name):
        corpus_path = Path(self.app.config.get_config('corpus'))
        polls_path = Path(self.app.config.get_config('polls'))
        povs_path = Path(self.app.config.get_config('povs'))

        source = corpus_path / challenge_name
        cmake = source / "CMakeLists.txt"
        readme = source / "README.md"
        polls = polls_path / challenge_name / 'poller'
        povs = povs_path / challenge_name
        poller = corpus_path / challenge_name / 'poller'

        return ChallengePaths(challenge_name, source, cmake, readme, polls, poller, povs)
