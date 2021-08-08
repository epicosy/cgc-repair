import os
import traceback

from pathlib import Path

from cgcrepair.core.corpus.challenge import Challenge
from cgcrepair.core.handlers.commands import CommandsHandler
from cgcrepair.core.handlers.database import Sanity
from cgcrepair.core.tests import Tests


class SanityHandler(CommandsHandler):
    class Meta:
        label = 'sanity'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set(self):
        super().set()

    def run(self, challenge: Challenge, sanity: Sanity):
        working_dir = Path(f"/tmp/check_{challenge.name}")
        # TODO: add genpovs operation
        self.app.log.info(f"Sanity checking {challenge.name}")
        sanity.cid = challenge.cid

        try:
            if self.check_genpolls(challenge, sanity):
                if self.check_genpovs(challenge, sanity):
                    if self.check_prepare(challenge, working_dir, sanity):
                        if self.check_test(challenge, sanity):
                            return True
            return False

        except Exception as e:
            self.error = str(e)
            self.app.log.error(f"The following exception was raised for the challenge {challenge.name}")
            self.app.log.error(traceback.format_exc())
        finally:
            self.unset()
            self.app.db.add(sanity)
            if not self.app.pargs.keep:
                self.dispose(working_dir)

    def dispose(self, working_dir: Path):
        os.system(f"rm -rf {working_dir}")
        self.app.log.info("Deleted temporary files generated")

    def check_genpovs(self, challenge: Challenge, sanity: Sanity):
        if not self.app.pargs.genpovs:
            return True

        genpovs_handler = self.app.handler.get('commands', 'genpovs', setup=True)
        genpovs_handler.set()
        genpovs_handler.run(challenge)

        if genpovs_handler.error:
            self.app.log.error(f"Gen POVs Failed: {genpovs_handler.error}")
            sanity.status = "Gen POVs Check Failed"

            return False

        self.app.log.info(f"Gen POVs: generated POVs")
        return True

    def check_genpolls(self, challenge: Challenge, sanity: Sanity):
        if not self.app.pargs.genpolls:
            return True

        genpolls_handler = self.app.handler.get('commands', 'genpolls', setup=True)
        genpolls_handler.set()
        genpolls_handler.run(challenge, self.app.pargs.genpolls)

        if genpolls_handler.error:
            self.app.log.error(f"Gen Polls Failed: {genpolls_handler.error}")
            sanity.status = "GenPolls Check Failed"

            return False

        self.app.log.info(f"Gen Polls: generated {self.app.pargs.genpolls} polls")
        return True

    def check_prepare(self, challenge: Challenge, working_dir: Path, sanity: Sanity):
        # Checkout
        checkout_handler = self.app.handler.get('commands', 'checkout', setup=True)
        checkout_handler.set(working_dir=working_dir)
        sanity.iid = checkout_handler.run(challenge)

        if checkout_handler.error:
            self.app.log.error(f"Checkout Failed {checkout_handler.error}")
            sanity.status = "Checkout Check Failed"

            return False

        self.app.log.info("Checkout Passed")

        # Compile
        compile_handler = self.app.handler.get('commands', 'compile', setup=True)
        compile_handler.set(tag="sanity")
        instance_handler = self.app.handler.get('database', 'instance', setup=True)
        instance = instance_handler.get(sanity.iid)
        compile_handler.run(instance, instance.working())
        sanity.co_id = compile_handler.save_outcome(instance)

        if compile_handler.error:
            self.app.log.error(f"Compile {compile_handler.error}")
            sanity.status = "Compile Check Failed"

            return False

        self.app.log.info("Compile Passed")
        return True

    def check_test(self, challenge: Challenge, sanity: Sanity):
        self.app.log.info(f"Testing with timeout {self.app.pargs.timeout}.")
        instance_handler = self.app.handler.get('database', 'instance', setup=True)
        instance = instance_handler.get(sanity.iid)
        test_handler = self.app.handler.get('commands', 'test', setup=True)
        test_handler.set(timeout=self.app.pargs.timeout)
        tests = Tests(polls_path=challenge.paths.polls, povs_path=challenge.paths.povs, neg_tests=self.app.pargs.povs)
        test_handler.run(instance, instance.working(), challenge.paths, tests)

        if test_handler.error:
            self.app.log.error(test_handler.error)

        outcomes = instance_handler.get_test_outcome(instance.id)

        neg_fails, pos_fails, passing, fails = [], [], [], []

        for outcome in outcomes:
            if not outcome.passed or outcome.exit_status != 0:
                if not outcome.passed and outcome.is_pov and outcome.sig == 11:
                    continue
                self.app.log.error(f"Failed {outcome.name} {outcome.passed}")
                fails.append(f"{outcome.name} {outcome.passed}")

                if outcome.is_pov:
                    neg_fails.append(outcome.name)
                else:
                    pos_fails.append(outcome.name)
            else:
                passing.append(f"{outcome.name} {outcome.passed}")

        if not outcomes or fails:
            self.app.log.error(f"Failed tests: {fails}")

            if passing:
                self.app.log.info(f"Passed tests: {passing}")

            sanity.status = "Test Check Failed"
            return False
        sanity.status = "Passed"
        return True
