from pathlib import Path
from typing import List, AnyStr

from cgcrepair.utils.data import Test


class Tests:
    def __init__(self, polls_path: Path, povs_path: Path, tests: List[AnyStr] = None, pos_tests: bool = False,
                 neg_tests: bool = False, only_numbers: bool = False):
        self.polls_path = polls_path
        self.povs_path = povs_path
        self.only_numbers = only_numbers
        self.pos_tests = {}
        self.neg_tests = {}
        self.mapped = {}
        self._tests = {}
        self.load_pos_tests()
        self.load_neg_tests()
        self.map_only_number_ids()

        if tests:
            self._tests = {test: self[test] for test in tests}
        elif pos_tests:
            self._tests = self.pos_tests
        elif neg_tests:
            self._tests = self.neg_tests
        else:
            self._tests.update(self.pos_tests)
            self._tests.update(self.neg_tests)

    def __getitem__(self, name: str):
        if self.only_numbers:
            if name in self.mapped:
                return self.mapped[name]
        elif name in self.pos_tests:
            return self.pos_tests[name]
        elif name in self.neg_tests:
            return self.neg_tests[name]

        raise ValueError(f"Test {name} not found in set of tests.")

    def __iter__(self):
        return iter(self._tests)

    def __len__(self):
        return len(self._tests)

    def keys(self):
        return self._tests.keys()

    def items(self):
        return self._tests.items()

    def values(self):
        return self._tests.values()

    def load_pos_tests(self):
        if not self.pos_tests:
            # Map cases to tests names where p is for positive test cases
            for i, file in enumerate(sorted(self.get_polls()), 1):
                test = Test(name=f"p{i}", is_pov=False, file=file, order=i)
                self.pos_tests[test.name] = test

            if not self.pos_tests:
                raise ValueError('No polls found')

    def load_neg_tests(self):
        if not self.neg_tests:
            # Map cases to tests names where n is for negative test cases
            for i, file in enumerate(sorted(self.get_povs()), 1):
                test = Test(name=f"n{i}", is_pov=True, file=file, order=i)
                self.neg_tests[test.name] = test

            if not self.neg_tests:
                raise ValueError('No POVs found')

    def get_polls(self):
        for_release = self.polls_path / Path('for-release')
        for_testing = self.polls_path / Path('for-testing')

        if for_testing.exists():
            return [file for file in for_testing.iterdir() if file.suffix == ".xml"]

        if for_release.exists():
            return [file for file in for_release.iterdir() if file.suffix == ".xml"]

    def get_povs(self):
        return [file for file in self.povs_path.iterdir() if file.suffix == ".pov"]

    def map_only_number_ids(self):
        if not self.mapped:
            self.mapped = {str(test.order): test for test in self.pos_tests.values()}
            count_pos_tests = len(self.pos_tests)
            self.mapped.update({str(test.order + count_pos_tests): test for test in self.neg_tests.values()})

            if not self.mapped:
                raise ValueError("Input tests could not be mapped with available tests.")
