from dataclasses import dataclass
from pathlib import Path


@dataclass
class Test:
    name: str
    order: int
    is_pov: bool
    file: Path


@dataclass
class CompileCommand:
    command: str
    file: Path
    dir: Path


@dataclass
class WorkingPaths:
    root: Path
    source: Path
    build_root: Path
    build: Path
    cmake: Path


@dataclass
class Tools:
    root: Path
    cmake_file: Path
    test: Path
    genpolls: Path

    def validate(self):
        assert self.root.exists(), f'Tools root path {self.root} not found'
        assert self.cmake_file.exists(), f'CMakeLists file {self.cmake_file} not found'
        assert self.genpolls.exists(), f'Polls generation script {self.genpolls} not found'
        assert self.test.exists(), f'Test script {self.test} not found'


@dataclass
class ChallengePaths:
    name: str
    source: Path
    cmake: Path
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
        # TODO: fix this path
        # assert self.povs.exists(), f'POVs path {self.povs} not found'
        assert self.challenges.exists(), f'Corpus path {self.challenges} not found'

    def get_challenges(self):
        return [challenge.name for challenge in self.challenges.iterdir() if challenge.is_dir()]

    def get_polls_path(self, challenge_name: str):
        return self.polls / Path(challenge_name, 'poller')

    def get_challenge_paths(self, challenge_name):
        source = self.challenges / challenge_name
        cmake = source / "CMakeLists.txt"
        readme = source / "README.md"
        polls = self.polls / challenge_name / 'poller'
        povs = self.povs / challenge_name
        poller = self.challenges / challenge_name / 'poller'

        return ChallengePaths(challenge_name, source, cmake, readme, polls, poller, povs)

