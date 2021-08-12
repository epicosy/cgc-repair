from cement import Controller, ex

from cgcrepair.core.data.store import TaskData
from cgcrepair.core.exc import CGCRepairError
from cgcrepair.core.handlers.database import Sanity


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
