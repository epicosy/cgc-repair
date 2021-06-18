from cement import Controller, ex

from cgcrepair.core.exc import CGCRepairError


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
        checkout_handler.run()

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
        genpolls_handler.set()
        genpolls_handler.run()

        if genpolls_handler.error:
            self.app.log.error(genpolls_handler.error)


    @ex(
        help='Generates polls for challenge. Theses are the positive tests.',
        arguments=[
            (['-n', '--count'], {'help': 'Number of traversals through the state graph per round', 'type': int,
                                 'default': 100})
        ]
    )
    def genpovs(self):
        genpovs_handler = self.app.handler.get('commands', 'genpovs', setup=True)
        genpovs_handler.set()
        genpovs_handler.run()

        if genpovs_handler.error:
            self.app.log.error(genpovs_handler.error)
