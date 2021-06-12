from dataclasses import dataclass
from pathlib import Path


@dataclass
class Tools:
    root: Path
    cmake_file: Path
    cmake_file_no_patch: Path
    test: Path
    genpolls: Path

    def validate(self):
        assert self.root.exists(), f'Tools root path {self.root} not found'
        assert self.cmake_file.exists(), f'CMakeLists file {self.cmake_file} not found'
        assert self.cmake_file_no_patch.exists(), f'CMakeLists file {self.cmake_file_no_patch} not found'
        assert self.genpolls.exists(), f'Polls generation script {self.genpolls} not found'
        assert self.test.exists(), f'Test script {self.test} not found'


@dataclass
class ChallengePaths:
    name: str
    source: Path
    info: Path
    polls: Path
    poller: Path
    povs: Path


@dataclass
class LibPaths:
    root: Path
    polls: Path
    povs: Path
    challenges: Path

    def validate(self):
        assert self.root.exists(), f'Library root path {self.root} not found'
        assert self.polls.exists(), f'Polls path {self.polls} not found'
        assert self.povs.exists(), f'POVs path {self.povs} not found'
        assert self.challenges.exists(), f'Corpus path {self.challenges} not found'

    def get_challenges(self):
        return [challenge.name for challenge in self.challenges.iterdir() if challenge.is_dir()]

    def get_polls_path(self, challenge_name: str):
        return self.polls / Path(challenge_name, 'poller')

    def get_challenge_paths(self, challenge_name):
        source = self.challenges / Path(challenge_name)
        readme = source / Path("README.md")
        polls = self.polls / Path(challenge_name, 'poller')
        povs = self.povs / challenge_name
        poller = self.challenges / Path(challenge_name, 'poller')

        return ChallengePaths(challenge_name, source, readme, polls, poller, povs)

