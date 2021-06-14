from cement import Controller, ex


class SimpleOperations(Controller):
    class Meta:
        label = 'simple_operations'
        stacked_on = 'base'
        stacked_type = 'nested'

        # controller level arguments. ex: 'cgcrepair --version'
        arguments = [
            (['-cn', '--challenge'], {'help': 'The challenge name.', 'type': str, 'required': True}),
        ]

    @ex(
        help='Checks out the specified challenge to a working directory.',
        arguments=[
            (['-rp', '--remove_patches'],
             {'help': 'Flag to checkout without patch definitions in the source code.', 'action': 'store_true',
              'dest': 'no_patch'}),
            (['-wd', '--working_directory'], {'help': 'The working directory.', 'type': str, 'required': False,
                                              'dest': 'working_dir'}),
            (['-S', '--seed'], {'help': "Random seed", 'required': False, 'type': int})
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
