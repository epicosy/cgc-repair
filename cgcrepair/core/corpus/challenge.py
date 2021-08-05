import re

from cgcrepair.utils.data import ChallengePaths

AUTHOR_ID_PATTERN = r'set\( AUTHOR_ID \"(.*)\" \)'
SERVICE_ID_PATTERN = r'set\( SERVICE_ID \"(.*)\" \)'


class Challenge:
    def __init__(self, paths: ChallengePaths):
        self.paths = paths
        self.name = paths.name
        self.cid = self.id()

    def info(self):
        with self.paths.info.open(mode="r") as f:
            return f.read()

    def author(self):
        with self.paths.cmake.open(mode="r") as clf:
            match = re.search(AUTHOR_ID_PATTERN, clf.read())

            if match:
                return match.group(1)

            return None

    def service(self):
        with self.paths.cmake.open(mode="r") as clf:
            match = re.search(SERVICE_ID_PATTERN, clf.read())

            if match:
                return match.group(1)

            return None

    def id(self):
        service = self.service()
        author = self.author()

        if service and author:
            return f"{author}_{service}"

        return None

    def has_shared_objects(self):
        with self.paths.cmake.open(mode='r') as cmf:
            return 'buildSO()' in cmf.read()
