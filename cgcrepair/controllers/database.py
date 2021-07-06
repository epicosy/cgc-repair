from cement import Controller, ex

from cgcrepair.core.exc import CGCRepairError


class Database(Controller):
    class Meta:
        label = 'database'
        stacked_on = 'base'
        stacked_type = 'nested'

    @ex(
        help='Lists specified table in the database.',
        arguments=[
            (['-I', '--instances'], {'help': 'Lists all instances in the database.', 'action': 'store_true',
                                     'required': False}),
            (['-M', '--metadata'], {'help': 'Lists metadata in the database.', 'action': 'store_true',
                                    'required': False}),
            (['-n', '--name'], {'help': 'Lists only the name of the record in the table.', 'action': 'store_true',
                                'required': False})
        ]
    )
    def list(self):
        if self.app.pargs.instances:
            instance_handler = self.app.handler.get('database', 'instance', setup=True)
            instances = instance_handler.all()

            if self.app.pargs.name:
                self.app.render({'collection': [inst.name for inst in instances]}, 'list.jinja2')
            else:
                self.app.render({'header': "ID | Name | Path | Pointer", 'collection': instances}, 'list.jinja2')

        if self.app.pargs.metadata:
            metadata_handler = self.app.handler.get('database', 'metadata', setup=True)
            metadata = metadata_handler.all()

            if self.app.pargs.name:
                self.app.render({'collection': [met.name for met in metadata]}, 'list.jinja2')
            else:
                self.app.render({'header': "Name | CWE | Nº POVs | LOC | Vuln LOC | Patch LOC | Vuln Files",
                                'collection': metadata}, 'list.jinja2')

    @ex(
        help='Lists outcomes for a specific instance.',
        arguments=[
            (['-t', '--test'], {'help': 'Lists all test outcomes in the database.', 'action': 'store_true',
                                'required': False}),
            (['-c', '--compile'], {'help': 'Lists all compile outcomes in the database.', 'action': 'store_true',
                                   'required': False}),
            (['--iid'], {'help': 'The id of the instance (challenge checked out).', 'type': int, 'required': True})
        ]
    )
    def outcomes(self):
        instance_handler = self.app.handler.get('database', 'instance', setup=True)
        instance = instance_handler.get(self.app.pargs.iid)

        if not instance:
            raise CGCRepairError(f"No instance {self.app.pargs.iid} found. "
                                 f"Use the ID supplied by the checkout command")

        if self.app.pargs.compile:
            outcomes = instance_handler.get_compile_outcome(self.app.pargs.iid)

            self.app.render({'header': "ID | Error | Tag | Exit Status ",
                             'collection': outcomes}, 'list.jinja2')

        if self.app.pargs.test:
            outcomes = instance_handler.get_test_outcome(self.app.pargs.iid)

            self.app.render({'header': "ID | Compile Outcome ID | Name | Error | Exit Status | Passed | Duration | "
                                       "Is POV | Signal | Failed | Total",
                             'collection': outcomes}, 'list.jinja2')
