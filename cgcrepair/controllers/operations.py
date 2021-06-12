from cement import Controller, ex


class Operations(Controller):
    class Meta:
        label = 'operations'
        stacked_on = 'base'
        stacked_type = 'nested'

        # controller level arguments. ex: 'cgcrepair --version'
        arguments = [
            (['--id'], {'help': 'The id of the instance (challenge checked out).', 'type': str, 'required': True}),
        ]

    @ex(
        help='Cmake init of the Makefiles.',
        arguments=[
            (['-wba', '--write_build_args'], {'help': 'File to output build args.', 'type': str, 'default': None}),
            (['-ctp', '--compiler_trail_path'], {'help': "Trail's compile commands path to compiler",
                                                 'action': 'store_true'}),
            (['-S', '--save_temps'], {'help': 'Store the normally temporary intermediate files.', 'action': 'store_true',
                                      'default': None}),
            (['-ee', '--exit_err'], {'help': 'Exits when error occurred.', 'action': 'store_false', 'required': False}),
            (['-R', '--replace'], {'help': 'Replaces output extension.', 'action': 'store_true'}),
            (['-T', '--tag'], {'help': 'Flag for tracking sanity check.', 'action': 'store_true', 'required': False})
        ]
    )
    def make(self):
        make_handler = self.app.handler.get('commands', 'make', setup=True)
        make_handler.set()
        make_handler.run()

        if make_handler.error:
            self.app.log.error(make_handler.error)
