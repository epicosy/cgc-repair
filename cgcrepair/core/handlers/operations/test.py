import os
import binascii

from os import listdir
from pathlib import Path

from cgcrepair.core.handlers.database import TestOutcome, Instance
from cgcrepair.utils.parse.test_result import get_outcome, get_pids_sig, pov_signals
from cgcrepair.utils.helpers import kill_by_name

from cgcrepair.core.exc import CommandError
from cgcrepair.core.handlers.commands import CommandsHandler
from cgcrepair.core.tests import Tests
from cgcrepair.utils.data import Test, WorkingPaths, ChallengePaths


class TestHandler(CommandsHandler):
    class Meta:
        label = 'test'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.failed = False

    def set(self):
        super().set()

    def run(self, instance: Instance, working: WorkingPaths, challenge_paths: ChallengePaths):
        try:
            tests = Tests(polls_path=challenge_paths.polls, povs_path=working.build, tests=self.app.pargs.tests,
                          pos_tests=self.app.pargs.pos_tests, neg_tests=self.app.pargs.neg_tests,
                          only_numbers=self.app.pargs.only_numbers)

            self.app.log.info(f"Running {len(tests)} tests.")
            timeout = self.get_timeout()

            for test in tests.values():
                cmd_str = self._cmd_str(test, working=working, challenge_name=challenge_paths.name)
                super().__call__(cmd_str=' '.join(cmd_str), cmd_cwd=str(self.app.config.get_config('tools')),
                                 timeout=timeout, raise_err=False, exit_err=False,
                                 msg=f"Testing {test.name} on {test.file.name}\n")
                test_outcome = self._process_result(test, challenge_name=challenge_paths.name)
                test_outcome.instance_id = instance.id
                test_outcome.co_id = instance.pointer
                test_outcome.duration = round(self.duration, 3)
                test_outcome.exit_status = self.return_code
                t_id = self.app.db.add(test_outcome)
                self.app.log.info(f"Inserted 'test outcome' with id {t_id} for instance {self.app.pargs.id}.")
                self._process_flags(test_outcome)

        except (ValueError, CommandError) as e:
            self.error = str(e)
        finally:
            self.unset()

    def get_timeout(self):
        # TODO: add/remove margin for execution
        margin = self.app.config.get_config('margin')
        # TODO: add duration of tests from sanity
        # sanity_handler = self.app.handler.get('database', 'sanity', setup=True)
        # duration = sanity_handler.get(challenge, test)
        # if duration:
        #     return duration + margin
        if self.app.pargs.timeout:
            return self.app.pargs.timeout + margin

        return self.app.config.get_config('tests_timeout') + margin

    def _process_result(self, test: Test, challenge_name: str):
        pids, sig = get_pids_sig(self.output)
        test_outcome = get_outcome(self.output, test=test, sig=sig)

        if self.error and sig not in pov_signals:
            self.app.log.warning(f"Killing {challenge_name} process.")
            killed_pids = kill_by_name(process_name=challenge_name, target_pids=pids)

            if killed_pids:
                self.app.log.info(f"Killed processes {killed_pids}.")

        return test_outcome

    def _process_flags(self, test_outcome: TestOutcome):
        if test_outcome.is_pov and self.app.pargs.neg_pov:
            # Invert negative test's result
            test_outcome.passed = not test_outcome.passed

            if test_outcome.passed:
                self.failed = True

        if self.app.pargs.print_ids and test_outcome.passed:
            if self.app.pargs.only_numbers:
                print(test_outcome.name[1:])
            else:
                print(test_outcome.name)
        if self.app.pargs.print_class:
            print("PASS" if test_outcome.passed else 'FAIL')

        if self.app.pargs.out_file is not None:
            self.write_result(test_outcome)

        if not test_outcome.passed or test_outcome.error:
            if not test_outcome.is_pov:
                self.failed = True
            elif not self.app.pargs.neg_pov:
                self.failed = True

    def _cmd_str(self, test: Test, working: WorkingPaths, challenge_name: str):
        # Collect the names of binaries to be tested
        cb_dirs = [el for el in listdir(str(working.source)) if el.startswith('cb_')]

        if len(cb_dirs) > 0:
            # There are multiple binaries in this challenge
            bin_names = ['{}_{}'.format(challenge_name, i + 1) for i in range(len(cb_dirs))]
        else:
            bin_names = [challenge_name]
        # use timeout or duration from sanity check
        timeout = self.get_timeout()
        python2 = self.app.config.get_config('python2')
        cb_cmd = [python2, str(self.app.tools.test), '--directory', str(working.build), '--xml', str(test.file),
                  '--concurrent', '1', '--debug', '--timeout', str(timeout), '--negotiate_seed', '--cb'] + bin_names

        if test.is_pov:
            cb_cmd += ['--cores_path', self.app.config.get_config("cores"), '--should_core']
            # double check
            seed = binascii.b2a_hex(os.urandom(48))
            cb_cmd += ['--pov_seed', seed.decode()]

        return cb_cmd

    def write_result(self, test_outcome: TestOutcome):
        if self.app.pargs.prefix:
            out_file = Path(self.app.pargs.prefix, self.app.pargs.out_file)
        else:
            out_file = Path(self.app.pargs.out_file)

        if not self.app.pargs.write_fail and not test_outcome.passed:
            return
        with out_file.open(mode="a") as of:
            of.write(f"{test_outcome.name} {test_outcome.passed}\n")
