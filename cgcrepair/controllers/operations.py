from cement import Controller, ex


make_args = [
            (['-wba', '--write_build_args'], {'help': 'File to output build args.', 'type': str, 'default': None}),
            (['-ctp', '--compiler_trail_path'], {'help': "Trail's compile commands path to compiler",
                                                 'action': 'store_true'}),
            (['-S', '--save_temps'], {'help': 'Store the normally temporary intermediate files.', 'action': 'store_true',
                                      'default': None}),
            (['-ee', '--exit_err'], {'help': 'Exits when error occurred.', 'action': 'store_false', 'required': False}),
            (['-R', '--replace'], {'help': 'Replaces output extension.', 'action': 'store_true'}),
            (['-T', '--tag'], {'help': 'Flag for tracking sanity check.', 'action': 'store_true', 'required': False})
        ]


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
        arguments=make_args
    )
    def make(self):
        make_handler = self.app.handler.get('commands', 'make', setup=True)
        make_handler.set()
        make_handler.run()
        make_handler.save_outcome()

        if make_handler.error:
            self.app.log.error(make_handler.error)

    @ex(
        help='Compiles challenge binary.',
        arguments=[
            (['-ifs', '--inst_files'], {'help': 'Instrumented files to compile.', 'nargs': '+', 'default': None}),
            (['-cov', '--coverage'], {'help': 'Cmake generates gcov files.', 'action': 'store_true', 'required': False}),
            (['-L', '--link'], {'help': 'Flag for only links objects into executable.', 'action': 'store_true',
                                'required': False}),
            (['-cpp', '--cpp_files'], {'help': 'Flag to indicate that instrumented files are preprocessed.',
                                       'action': 'store_true', 'required': False}),
            (['-ffs', '--fix_files'], {'help': 'The file with changes applied by the repair tool.', 'nargs': '+',
                                       'default': None}),
            (['-B', '--backup'], {'help': 'Backups the manifest file to a given path.', 'type': str, 'default': None})
        ] + make_args
    )
    def compile(self):
        compile_handler = self.app.handler.get('commands', 'compile', setup=True)
        compile_handler.set()
        compile_handler.run()
        compile_handler.save_outcome()

        if compile_handler.error:
            self.app.log.error(compile_handler.error)
