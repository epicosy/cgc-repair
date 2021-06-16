from cement import Controller, ex


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
                                    'required': False})
        ]
    )
    def list(self):
        if self.app.pargs.instances:
            instance_handler = self.app.handler.get('database', 'instance', setup=True)
            instances = instance_handler.all()

            self.app.render({'header': "ID | Name | Path | Pointer", 'collection': instances}, 'list.jinja2')

        if self.app.pargs.metadata:
            metadata_handler = self.app.handler.get('database', 'metadata', setup=True)
            metadata = metadata_handler.all()

            self.app.render({'header': "Name | CWE | Nº POVs | LOC | Vuln LOC | Patch LOC | Vuln Files",
                             'collection': metadata}, 'list.jinja2')
