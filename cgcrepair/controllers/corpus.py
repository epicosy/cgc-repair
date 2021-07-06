from cement import Controller, ex

from cgcrepair.core.corpus.manifest import Manifest
from cgcrepair.core.exc import CGCRepairError
from cgcrepair.core.tests import Tests


class Corpus(Controller):
    class Meta:
        label = 'corpus'
        stacked_on = 'base'
        stacked_type = 'nested'

        # controller level arguments. ex: 'cgcrepair --version'
        arguments = [
            (['-cn', '--challenge'], {'help': 'The challenge name.', 'type': str, 'required': True}),
        ]

    def _post_argument_parsing(self):
        if 'challenge' in self.app.pargs:
            # TODO: maybe add as well the metadata
            corpus_handler = self.app.handler.get('corpus', 'corpus', setup=True)

            if not corpus_handler.has(self.app.pargs.challenge):
                raise CGCRepairError(f"No {self.app.pargs.challenge} challenge in the CGC Corpus")

            self.challenge = corpus_handler.get(self.app.pargs.challenge)

    @ex(
        help='Checks out the specified challenge to a working directory.',
        arguments=[
            (['-rp', '--remove_patches'],
             {'help': 'Flag to checkout without patch definitions in the source code.', 'action': 'store_true',
              'dest': 'no_patch'}),
            (['-wd', '--working_directory'], {'help': 'The working directory.', 'type': str, 'required': False,
                                              'dest': 'working_dir'}),
            (['-S', '--seed'], {'help': "Random seed", 'required': False, 'type': int}),
            (['-F', '--force'], {'help': "Forces to checkout to existing directory", 'required': False,
                                 'action': 'store_true'})
        ]
    )
    def checkout(self):
        checkout_handler = self.app.handler.get('commands', 'checkout', setup=True)
        checkout_handler.set()
        checkout_handler.run(self.challenge)

        if checkout_handler.error:
            self.app.log.error(checkout_handler.error)

    @ex(
        help='Generates polls for challenge. Theses are the positive tests.',
        arguments=[
            (['-n', '--count'], {'help': 'Number of traversals through the state graph per round', 'type': int,
                                 'default': 100})
        ]
    )
    def genpolls(self):
        genpolls_handler = self.app.handler.get('commands', 'genpolls', setup=True)
        corpus_handler = self.app.handler.get('corpus', 'corpus', setup=True)
        challenge_paths = corpus_handler.get_challenge_paths(self.app.pargs.challenge)
        genpolls_handler.set()
        genpolls_handler.run(challenge_paths)

        if genpolls_handler.error:
            self.app.log.error(genpolls_handler.error)

    @ex(
        help='Builds the POVs for the challenge. Theses are the negative tests.',
        arguments=[
            (['--m32'], {'help': "Compiles the POVs as 32 bit binaries", 'required': False, 'action': 'store_true'})
        ]
    )
    def genpovs(self):
        genpovs_handler = self.app.handler.get('commands', 'genpovs', setup=True)
        genpovs_handler.set()
        genpovs_handler.run(self.challenge)

        if genpovs_handler.error:
            self.app.log.error(genpovs_handler.error)

    @ex(
        help='Queries the (number of) positive and negative tests.',
        arguments=[
            (['--pos'], {'help': "Flag for only positive tests (Polls).", 'required': False, 'action': 'store_true'}),
            (['--neg'], {'help': "Flag for only negative tests (POVs).", 'required': False, 'action': 'store_true'}),
            (['--count'], {'help': "Prints the count of the tests.", 'required': False, 'action': 'store_true'})
        ]
    )
    def tests(self):
        tests = Tests(polls_path=self.challenge.paths.polls, povs_path=self.challenge.paths.povs)

        # TODO: use jinja templates instead of prints
        if self.app.pargs.neg:
            if self.app.pargs.count:
                print(len(tests.neg_tests))
            else:
                print(' '.join(tests.neg_tests.keys()))
        elif self.app.pargs.pos:
            if self.app.pargs.count:
                print(len(tests.pos_tests))
            else:
                print(' '.join(tests.pos_tests.keys()))
        else:
            if self.app.pargs.count:
                print(len(tests.pos_tests), len(tests.neg_tests))
            else:
                print(' '.join(tests.pos_tests.keys()), ' '.join(tests.neg_tests.keys()))

    @ex(
        help="Returns the vulnerable files.",
        arguments=[
            (['--path'], {'help': "Manifest is saved under the path or to the file specified.", 'required': False,
                          'type': str}),
            (['--lines'], {'help': "Manifest includes the lines.", 'required': False, 'action': 'store_true'}),
        ]
    )
    def manifest(self):
        manifest = Manifest(source_path=self.challenge.paths.source, out_dir=self.app.pargs.path)

        if self.app.pargs.path:
            manifest.write()
        else:
            vulns = manifest.get_vulns()

            for file, vuln in vulns.items():
                if self.app.pargs.lines:
                    print(file, ' '.join([f"{v} {v+ len(l)}" for v, l in vuln.items()]))
                else:
                    print(file)
