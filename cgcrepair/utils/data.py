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
