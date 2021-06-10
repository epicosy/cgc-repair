from cgcrepair.utils.data import ChallengePaths


class Challenge:
    def __init__(self, paths: ChallengePaths):
        self.paths = paths
        self.name = paths.name

    def info(self):
        with self.paths.info.open(mode="r") as f:
            return f.read()
