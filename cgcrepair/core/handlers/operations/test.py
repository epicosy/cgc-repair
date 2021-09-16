import os
import binascii

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

    def set(self, timeout: int = None, neg_pov: bool = False, print_ids: bool = False, only_numbers: bool = False,
            print_class: bool = False, out_file: str = None, write_fail: bool = True, prefix: str = None):
        super().set()
        self.timeout = timeout
        self.neg_pov = neg_pov
        self.print_ids = print_ids
        self.only_numbers = only_numbers
        self.print_class = print_class
        self.out_file = out_file
        self.write_fail = write_fail
        self.prefix = prefix

    def run(self, instance: Instance, working: WorkingPaths, challenge_paths: ChallengePaths, tests: Tests):
        try:
            self.app.log.info(f"Running {len(tests)} tests.")
            timeout = self.get_timeout()

            for test in tests.values():
                cmd_str = self._cmd_str(test, working=working)
                super().__call__(cmd_str=' '.join(cmd_str), cmd_cwd=str(self.app.config.get_config('tools')),
                                 timeout=timeout, raise_err=False, exit_err=False,
                                 msg=f"Testing {test.name} on {test.file.name}\n")

                test_outcome = self._process_result(test, challenge_name=challenge_paths.name)
                test_outcome.instance_id = instance.id
                test_outcome.co_id = instance.pointer
                test_outcome.duration = round(self.duration, 3)
                if test_outcome.duration > timeout and test_outcome.error and test_outcome.exit_status != 0:
                    test_outcome.error = "Test timed out"
                test_outcome.exit_status = self.return_code
                t_id = self.app.db.add(test_outcome)
                self.app.log.debug(f"Inserted 'test outcome' with id {t_id} for instance {instance.id}.")
                self._process_flags(test_outcome)

        except (ValueError, CommandError) as e:
            self.error = str(e)
        finally:
            self.unset()

    def unset(self):
        super().unset()

    def get_timeout(self):
        # TODO: add/remove margin for execution
        margin = self.app.config.get_config('margin')
        # TODO: add duration of tests from sanity
        # sanity_handler = self.app.handler.get('database', 'sanity', setup=True)
        # duration = sanity_handler.get(challenge, test)
        # if duration:
        #     return duration + margin
        if self.timeout:
            return self.timeout + margin

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
        if test_outcome.is_pov and self.neg_pov:
            # Invert negative test's result
            test_outcome.result = not test_outcome.result

            if not test_outcome.result:
                self.failed = True

        if self.print_ids and test_outcome.result:
            if self.only_numbers:
                print(test_outcome.name[1:])
            else:
                print(test_outcome.name)
        if self.print_class:
            print("PASS" if test_outcome.result else 'FAIL')

        if self.out_file is not None:
            self.write_result(test_outcome)

        if not test_outcome.result or test_outcome.error:
            if not test_outcome.is_pov:
                self.failed = True
            elif not self.neg_pov:
                self.failed = True

    def _cmd_str(self, test: Test, working: WorkingPaths):
        bin_names = working.get_binaries()

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
        if self.prefix:
            out_file = Path(self.prefix, self.out_file)
        else:
            out_file = Path(self.out_file)

        if not self.write_fail and not test_outcome.passed:
            return
        with out_file.open(mode="a") as of:
            of.write(f"{test_outcome.name} {test_outcome.result}\n")
