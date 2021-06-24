import shutil
from pathlib import Path

from cgcrepair.core.corpus.challenge import Challenge
from cgcrepair.core.exc import CommandError
from cgcrepair.core.handlers.commands import CommandsHandler
from cgcrepair.utils.data import ChallengePaths


class GenPollsHandler(CommandsHandler):
    class Meta:
        label = 'genpolls'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.out_dir = None
        self.polls = []

    def set(self):
        super().set()
        assert self.app.pargs.count > 0

    def install_shared_objects(self, challenge_paths: ChallengePaths):
        challenge = Challenge(challenge_paths)
        compile_handler = self.app.handler.get('commands', 'compile', setup=True)

        # TODO: clean this junk
        self.app.pargs.replace = None
        self.app.pargs.save_temps = None
        self.app.pargs.coverage = None
        self.app.pargs.fix_files = None

        compile_handler.set()
        compile_handler.install_shared_objects(challenge)

        if compile_handler.error:
            raise CommandError(compile_handler.error)

    def run(self, challenge_paths: ChallengePaths):
        try:
            self.install_shared_objects(challenge_paths)

            if challenge_paths.polls.exists():
                self.app.log.warning(f"Deleting existing polls for {self.app.pargs.challenge}.")
                shutil.rmtree(str(challenge_paths.polls))

            self.app.log.info(f"Creating directories for {self.app.pargs.challenge} polls.")
            challenge_paths.polls.mkdir(parents=True)
            self.state_machine(challenge_paths)

            if self.out_dir:
                if not self.out_dir.exists() or len(list(self.out_dir.iterdir())) < self.app.pargs.count:
                    self.copy_polls(challenge_paths.name)
            else:
                raise CommandError(f"No poller directories for {challenge_paths.name}")

        except CommandError as ce:
            self.error = str(ce)
        finally:
            self.unset()

    def state_machine(self, challenge_paths: ChallengePaths):
        # looks for the state machine scripts used for generating polls and runs it
        # otherwise sets the directory with the greatest number of polls
        pollers = list(challenge_paths.poller.iterdir())

        # prioritize the for-testing poller
        if len(pollers) > 1:
            pollers.sort(reverse=True)

        for poll_dir in pollers:
            if poll_dir.is_dir():
                polls = [poll for poll in poll_dir.iterdir() if poll.suffix == ".xml"]

                if len(polls) > len(self.polls):
                    self.polls = polls

                self.out_dir = challenge_paths.polls / Path(poll_dir.name)
                state_machine_script = poll_dir / Path("machine.py")
                state_graph = poll_dir / Path("state-graph.yaml")

                if state_machine_script.exists() and state_graph.exists():
                    self.out_dir.mkdir(parents=True, exist_ok=True)
                    python2 = self.app.config.get_config('python2')
                    cmd_str = f"{python2} -B {self.app.tools.genpolls} --count {self.app.pargs.count} " \
                              f"--store_seed --depth 1048575 {state_machine_script} {state_graph} {self.out_dir}"

                    super().__call__(cmd_str=cmd_str, msg=f"Generating polls for {challenge_paths.name}.\n",
                                     cmd_cwd=str(challenge_paths.source), raise_err=False)
                    if self.error:
                        if 'AssertionError' in self.error:
                            self.app.log.warning(self.error)
                        else:
                            raise CommandError(self.error)

                    self.app.log.info(f"Generated polls for {challenge_paths.name}.")
                    break

    def copy_polls(self, challenge_name: str):
        if self.polls:
            self.app.log.warning(f"No scripts for generating polls for {challenge_name}.")
            self.app.log.info(f"Coping pre-generated polls for {challenge_name}.\n")
            self.out_dir.mkdir(parents=True, exist_ok=True)

            if len(self.polls) < self.app.pargs.count:
                warning = f"Number of polls available {len(self.polls)} less than the number specified {self.app.pargs.count}"
                self.app.log.warning(warning)

            self.polls.sort()
            polls = self.polls[:self.app.pargs.count] if len(self.polls) > self.app.pargs.count else self.polls

            for poll in polls:
                shutil.copy(str(poll), self.out_dir)
            self.app.log.info(f"Copied polls for {challenge_name}.")

        else:
            raise CommandError(f"No pre-generated polls found for {challenge_name}.")
