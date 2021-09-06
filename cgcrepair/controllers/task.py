from cement import Controller, ex

from cgcrepair.core.data.store import TaskData
from cgcrepair.core.exc import CGCRepairError
from cgcrepair.core.handlers.database import Sanity
from cgcrepair.core.tests import Tests


class Task(Controller):
    class Meta:
        label = 'task'
        stacked_on = 'base'
        stacked_type = 'nested'

    def get_challenges(self):
        challenges = []
        corpus_handler = self.app.handler.get('corpus', 'corpus', setup=True)
        metadata_handler = self.app.handler.get('database', 'metadata', setup=True)

        if self.app.pargs.cid:
            for challenge in self.app.pargs.cid:
                metadata = metadata_handler.get(challenge)

                if not metadata:
                    raise CGCRepairError(f"No challenge with id {challenge} in the database")

                if not corpus_handler.has(metadata.name):
                    raise CGCRepairError(f"No {metadata.name} challenge in the CGC Corpus")

                challenges.append(corpus_handler.get(metadata.name))

            return challenges
        return corpus_handler.all()

    @ex(
        help='Sanity checks for challenges.',
        arguments=[(['--cid'], {'help': 'The challenge id.', 'type': str, 'nargs': '+', 'required': False}),
                   (['--timeout'], {'type': int, 'default': 60, 'help': 'The timeout for tests in seconds.'}),
                   (['--m32'], {'action': 'store_true', 'help': 'Flag for compiling for 32 bit arch.'}),
                   (['--genpolls'], {'type': int, 'default': None, 'help': 'Number of polls to generate.'}),
                   (['--threads'], {'type': int, 'default': 2, 'help': 'Number of threads to use.'}),
                   (['--genpovs'], {'action': 'store_true', 'help': 'Flag for enabling POVs generation.'}),
                   (['--keep'], {'action': 'store_true', 'help': 'Keeps the files generated.'}),
                   (['--povs'], {'action': 'store_true', 'help': 'Tests only POVs.'}),
                   (['--strict'], {'action': 'store_true', 'help': 'Stops testing at the first fail.'}),
                   ]
    )
    def sanity(self):
        sanity_handler = self.app.handler.get('commands', 'sanity', setup=True)
        runner_handler = self.app.handler.get('runner', 'runner', setup=True)

        results = runner_handler(tasks=[TaskData(run_args={'challenge': challenge, 'sanity': Sanity()}) for challenge in self.get_challenges()],
                                 commands_handler=sanity_handler, threads=self.app.pargs.threads)
        print(t.run_ret for t in results.tasks)

        if sanity_handler.error:
            self.app.log.error(sanity_handler.error)

    @ex(
        help='Queries the (number of) positive and negative tests.',
        arguments=[
            (['--count'], {'help': "Prints the count of the tests.", 'required': False, 'action': 'store_true'}),
            (['--cid'], {'help': 'The challenge id.', 'type': str, 'required': True})
        ]
    )
    def tests(self):
        corpus_handler = self.app.handler.get('corpus', 'corpus', setup=True)
        metadata_handler = self.app.handler.get('database', 'metadata', setup=True)
        metadata = metadata_handler.get(self.app.pargs.cid)

        if not metadata:
            self.app.log.warning(f"Challenge {self.app.pargs.cid} not found.")
            return

        challenge = corpus_handler.get(metadata.name)
        tests = Tests(polls_path=challenge.paths.polls, povs_path=challenge.paths.povs)

        # TODO: use jinja templates instead of prints
        if self.app.pargs.count:
            print(len(tests.pos_tests))
            print(len(tests.neg_tests))
        else:
            print(' '.join(tests.pos_tests.keys()))
            print(' '.join(tests.neg_tests.keys()))

    @ex(
        help='Generates the Polls and POVs for the challenges in the metadata.',
        arguments=[
            (['-n', '--count'], {'type': int, 'default': 10, 'help': 'Number of polls to generate.'}),
            (['--m32'], {'action': 'store_true', 'help': 'Flag for compiling for 32 bit arch.'}),
            (['--threads'], {'type': int, 'default': 2, 'help': 'Number of threads to use.'})
        ]
    )
    def generate(self):
        genpovs_handler = self.app.handler.get('commands', 'genpovs', setup=True)
        genpovs_handler.set(m32=True if self.app.pargs.m32 else False)

        genpolls_handler = self.app.handler.get('commands', 'genpolls', setup=True)
        genpolls_handler.set()

        metadata_handler = self.app.handler.get('database', 'metadata', setup=True)
        corpus_handler = self.app.handler.get('corpus', 'corpus', setup=True)
        runner_handler = self.app.handler.get('runner', 'runner', setup=True)
        tasks = []
        challenges = []

        for metadata in metadata_handler.all():
            if metadata.name in challenges:
                continue
            challenge = corpus_handler.get(metadata.name)
            tasks.append(TaskData(run_args={'challenge': challenge}, commands_handler=genpovs_handler))
            tasks.append(TaskData(run_args={'challenge': challenge, 'count': self.app.pargs.count},
                                  commands_handler=genpolls_handler))
            challenges.append(metadata.name)

        results = runner_handler(tasks=tasks, threads=self.app.pargs.threads)
        print(results)
