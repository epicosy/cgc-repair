from cement import Controller, ex
from cement.ext.ext_argparse import ArgparseArgumentHandler

from cgcrepair.core.exc import CGCRepairError
from cgcrepair.core.tests import Tests

make_args = [
    (['-wba', '--write_build_args'], {'help': 'File to output build args.', 'type': str, 'default': None}),
    (['-ctp', '--compiler_trail_path'], {'help': "Trail's compile commands path to compiler",
                                         'action': 'store_true'}),
    (['-S', '--save_temps'], {'help': 'Store the normally temporary intermediate files.', 'action': 'store_true',
                              'default': None}),
    (['-ee', '--exit_err'], {'help': 'Exits when error occurred.', 'action': 'store_false', 'required': False}),
    (['-R', '--replace'], {'help': 'Replaces output extension.', 'action': 'store_true'}),
    (['-T', '--tag'], {'help': 'Flag for tracking sanity check.', 'action': 'store_true', 'required': False}),
    (['-wd', '--working_dir'], {'help': 'Overwrites the working directory to the specified path', 'type': str,
                                'required': False})
]

# Exclusive arguments for test command
argparse_handler = ArgparseArgumentHandler(add_help=False)
tests_group = argparse_handler.add_mutually_exclusive_group(required=False)
tests_group.add_argument('-pt', '--pos_tests', action='store_true',
                         help='Run all positive tests against the challenge.',
                         required=False)
tests_group.add_argument('-nt', '--neg_tests', action='store_true',
                         help='Run all negative tests against the challenge.',
                         required=False)
tests_group.add_argument('-tn', '--tests', type=str, nargs='+', help='Name of the test', required=False)

# Print group
print_group = argparse_handler.add_mutually_exclusive_group(required=False)
print_group.add_argument('-PI', '--print_ids', help='Flag for printing the list of passed testcase ids.',
                         action='store_true')
print_group.add_argument('-P', '--print_class', help='Flag for printing testcases outcome as PASS/FAIL.',
                         action='store_true')

cov_group = argparse_handler.add_argument_group(title="coverage", description="None")
cov_group.add_argument('-cd', '--cov_dir', type=str, help='The dir where the coverage files are generated.',
                       default=None)
cov_group.add_argument('-cod', '--cov_out_dir', type=str, help='The dir where the coverage files are output.',
                       default=None)
cov_group.add_argument('-cs', '--cov_suffix', type=str, help='The suffix of the coverage files generated.',
                       default=".path")
cov_group.add_argument('-rs', '--rename_suffix', type=str, default=".path",
                       help='Rename the suffix to a specific one when outputting files')


class Instance(Controller):
    class Meta:
        label = 'instance'
        stacked_on = 'base'
        stacked_type = 'nested'

        arguments = [
            (['--id'], {'help': 'The id of the instance (challenge checked out).', 'type': int, 'required': True}),
        ]

    def _post_argument_parsing(self):
        if 'id' in self.app.pargs:
            instance_handler = self.app.handler.get('database', 'instance', setup=True)
            self.instance = instance_handler.get(instance_id=self.app.pargs.id)

            if not self.instance:
                raise CGCRepairError(f"No instance {self.app.pargs.id} found. "
                                     f"Use the ID supplied by the checkout command")

            self.working = self.instance.working()

            if not self.instance.path:
                raise CGCRepairError('Working directory is required. Checkout again the working directory')

            if not self.working.root.exists():
                raise CGCRepairError('Working directory does not exist.')

    @ex(
        help='Cmake init of the Makefiles.',
        arguments=make_args
    )
    def make(self):
        make_handler = self.app.handler.get('commands', 'make', setup=True)
        make_handler.set(replace=self.app.pargs.replace, save_temps=self.app.pargs.save_temps, tag=self.app.pargs.tag,
                         write_build_args=self.app.pargs.write_build_args,
                         compiler_trail_path=self.app.pargs.compiler_trail_path)
        make_handler.run(self.instance, self.working)
        make_handler.save_outcome(self.instance)

        if make_handler.error:
            self.app.log.error(make_handler.error)
            exit(1)

    @ex(
        help='Compiles challenge binary.',
        arguments=[
                      (['-ifs', '--inst_files'],
                       {'help': 'Instrumented files to compile.', 'nargs': '+', 'default': None}),
                      (['-cov', '--coverage'],
                       {'help': 'Cmake generates gcov files.', 'action': 'store_true', 'required': False}),
                      (
                              ['-L', '--link'],
                              {'help': 'Flag for only links objects into executable.', 'action': 'store_true',
                               'required': False}),
                      (['-cpp', '--cpp_files'], {'help': 'Flag to indicate that instrumented files are preprocessed.',
                                                 'action': 'store_true', 'required': False}),
                      (['-ffs', '--fix_files'],
                       {'help': 'The file with changes applied by the repair tool.', 'nargs': '+',
                        'default': None}),
                      (['-B', '--backup'],
                       {'help': 'Backups the manifest file to a given path.', 'type': str, 'default': None})
                  ] + make_args
    )
    def compile(self):
        compile_handler = self.app.handler.get('commands', 'compile', setup=True)
        compile_handler.set(coverage=self.app.pargs.coverage, fix_files=self.app.pargs.fix_files,
                            tag=self.app.pargs.tag,
                            inst_files=self.app.pargs.inst_files, backup=self.app.pargs.backup,
                            link=self.app.pargs.link,
                            replace=self.app.pargs.replace, save_temps=self.app.pargs.save_temps,
                            cpp_files=self.app.pargs.cpp_files, write_build_args=self.app.pargs.write_build_args,
                            compiler_trail_path=self.app.pargs.compiler_trail_path)
        compile_handler.run(self.instance, self.working)
        compile_handler.save_outcome(self.instance)

        if compile_handler.error:
            self.app.log.error(compile_handler.error)
            exit(1)

    @ex(
        help='Runs specified tests against challenge binary.',
        arguments=[
            (['-of', '--out_file'], {'help': 'The file where tests results are written to.', 'type': str}),
            (['-on', '--only_numbers'],
             {'help': 'Testcase ids are only numbers. Negative tests are counter after the positive.',
              'action': 'store_true'}),
            (['-T', '--timeout'], {'help': 'Timeout for the tests.', 'required': False, 'type': int}),
            (['-wf', '--write_fail'], {'help': 'Flag for writing the failed test to the specified out_file.',
                                       'action': 'store_true'}),
            (['-np', '--neg_pov'], {'help': 'Flag for reversing the passed result if is a negative test.',
                                    'action': 'store_true'}),
            (['-ef', '--exit_fail'], {'help': 'Flag that makes program exit with error when a test fails.',
                                      'action': 'store_true'})
        ],
        parents=[argparse_handler]
    )
    def test(self):
        test_handler = self.app.handler.get('commands', 'test', setup=True)
        corpus_handler = self.app.handler.get('corpus', 'corpus', setup=True)
        challenge_paths = corpus_handler.get_challenge_paths(self.instance.name)

        test_handler.set(timeout=self.app.pargs.timeout, neg_pov=self.app.pargs.neg_pov,
                         print_ids=self.app.pargs.print_ids, only_numbers=self.app.pargs.only_numbers,
                         print_class=self.app.pargs.print_class, out_file=self.app.pargs.out_file,
                         write_fail=self.app.pargs.write_fail)
        tests = Tests(polls_path=challenge_paths.polls, povs_path=challenge_paths.povs, tests=self.app.pargs.tests,
                      pos_tests=self.app.pargs.pos_tests, neg_tests=self.app.pargs.neg_tests,
                      only_numbers=self.app.pargs.only_numbers)
        test_handler.run(self.instance, self.working, challenge_paths, tests)

        if test_handler.error:
            self.app.log.error(test_handler.error)

        if (test_handler.error or test_handler.failed) and self.app.pargs.exit_fail:
            exit(1)
        exit(0)

    @ex(
        help='Applies a patch file to an instance\'s source file.',
        arguments=[
            (['-sf', '--source_file'], {'help': 'The relative path to the source file (e.g. src/main.c).', 'type': str,
                                        'required': True}),
            (['-pf', '--patch_file'], {'help': 'The absolute path to the patch file.', 'type': str, 'required': True}),
        ]
    )
    def patch(self):
        command_handler = self.app.handler.get('commands', 'commands', setup=True)
        command_handler(cmd_str=f"patch -d {self.working.source} {self.app.pargs.source_file} -i "
                                f"{self.app.pargs.patch_file} --verbose")

        if not command_handler.error:
            self.app.log.info(f"Patched {self.app.pargs.source_file}")
