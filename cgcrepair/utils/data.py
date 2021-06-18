from dataclasses import dataclass
from pathlib import Path
from os import listdir


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
    binary: Path

    def get_binaries(self):
        # Collect the names of binaries to be tested
        cb_dirs = [el for el in listdir(str(self.source)) if el.startswith('cb_')]

        if len(cb_dirs) > 0:
            # There are multiple binaries in this challenge
            return ['{}_{}'.format(self.binary.name, i + 1) for i in range(len(cb_dirs))]
        else:
            # Check the challenge binary
            if not self.binary.exists():
                raise ValueError(f"Challenge binary {self.binary.name} not found")

            return [self.binary.name]


@dataclass
class Tools:
    cmake_file: Path
    test: Path
    genpolls: Path

    def validate(self):
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
