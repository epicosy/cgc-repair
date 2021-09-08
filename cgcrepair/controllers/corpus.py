from cement import Controller, ex

from cgcrepair.core.corpus.challenge import Challenge
from cgcrepair.core.corpus.manifest import Manifest
from cgcrepair.core.exc import CGCRepairError


class Corpus(Controller):
    class Meta:
        label = 'corpus'
        stacked_on = 'base'
        stacked_type = 'nested'

        arguments = [
            (['--cid'], {'help': 'The challenge id.', 'type': str, 'required': True}),
        ]

    def get_challenge(self) -> Challenge:
        corpus_handler = self.app.handler.get('corpus', 'corpus', setup=True)
        metadata_handler = self.app.handler.get('database', 'metadata', setup=True)
        metadata = metadata_handler.get(self.app.pargs.cid)

        if not metadata:
            raise CGCRepairError(f"No challenge with id {self.app.pargs.cid} in the database")

        if not corpus_handler.has(metadata.name):
            raise CGCRepairError(f"No {metadata.name} challenge in the CGC Corpus")

        return corpus_handler.get(metadata.name)

    @ex(
        help='Checks out the specified challenge to a working directory.',
        arguments=[
            (['-rp', '--remove_patches'],
             {'help': 'Flag to checkout without patch definitions in the source code.', 'action': 'store_true',
              'dest': 'no_patch'}),
            (['-wd', '--working_directory'], {'help': 'The working directory.', 'type': str, 'required': False,
                                              'dest': 'working_dir'}),
            (['-rd', '--root_dir'], {'help': 'The root directory used for the working directory.', 'type': str,
                                     'required': False}),
            (['-S', '--seed'], {'help': "Random seed", 'required': False, 'type': int}),
            (['-F', '--force'], {'help': "Forces to checkout to existing directory", 'required': False,
                                 'action': 'store_true'})
        ]
    )
    def checkout(self):
        challenge = self.get_challenge()
        checkout_handler = self.app.handler.get('commands', 'checkout', setup=True)
        checkout_handler.set(no_patch=self.app.pargs.no_patch, working_dir=self.app.pargs.working_dir,
                             seed=self.app.pargs.seed, force=self.app.pargs.force, root_dir=self.app.pargs.root_dir)
        checkout_handler.run(challenge)

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
        challenge = self.get_challenge()
        assert self.app.pargs.count > 0
        genpolls_handler = self.app.handler.get('commands', 'genpolls', setup=True)
        genpolls_handler.set()
        genpolls_handler.run(challenge, self.app.pargs.count)

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
        genpovs_handler.set(m32=self.app.pargs.m32)
        genpovs_handler.run(self.get_challenge())

        if genpovs_handler.error:
            self.app.log.error(genpovs_handler.error)

    @ex(
        help="Returns the vulnerable files.",
        arguments=[
            (['--path'], {'help': "Manifest is saved under the path or to the file specified.", 'required': False,
                          'type': str}),
            (['--lines'], {'help': "Manifest includes the lines.", 'required': False, 'action': 'store_true'}),
        ]
    )
    def manifest(self):
        challenge = self.get_challenge()
        manifest = Manifest(source_path=challenge.paths.source, out_dir=self.app.pargs.path)

        if self.app.pargs.path:
            manifest.write()
        else:
            vulns = manifest.get_vulns()

            for file, vuln in vulns.items():
                if self.app.pargs.lines:
                    print(file, ' '.join([f"{v} {v+ len(l)}" for v, l in vuln.items()]))
                else:
                    print(file)

    @ex(
        help='Prints challenge\'s description',
        arguments=[]
    )
    def info(self):
        challenge = self.get_challenge()
        print(challenge.info())
