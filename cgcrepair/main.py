from os.path import dirname

from cement import App, TestApp
from cement.core.exc import CaughtSignal

from .controllers.base import Base
from .core.exc import CGCRepairError
from cgcrepair.core.handlers.configurations import YamlConfigurations


ROOT_DIR = dirname(dirname(__file__))


class CGCRepair(App):
    """cgcrepair primary application."""

    class Meta:
        label = 'cgcrepair'

        # call sys.exit() on close
        exit_on_close = True

        # load additional framework extensions
        extensions = [
            'colorlog',
            'jinja2',
        ]

        config_defaults = {'root': ROOT_DIR}

        # configuration handler
        config_handler = 'yaml_configurations'

        config_dirs = [f'{ROOT_DIR}/config']

        # configuration file suffix
        config_file_suffix = '.yml'

        # set the log handler
        log_handler = 'colorlog'

        # set the output handler
        output_handler = 'jinja2'

        # register handlers
        handlers = [
            Base, YamlConfigurations
        ]


class CGCRepairTest(TestApp, CGCRepair):
    """A sub-class of CGCRepair that is better suited for testing."""

    class Meta:
        label = 'cgcrepair'


def main():
    with CGCRepair() as app:
        try:
            # app.config.validate()
            app.run()

        except AssertionError as e:
            print('AssertionError > %s' % e.args[0])
            app.exit_code = 1

            if app.debug is True:
                import traceback
                traceback.print_exc()

        except CGCRepairError as e:
            print('CGCRepairError > %s' % e.args[0])
            app.exit_code = 1

            if app.debug is True:
                import traceback
                traceback.print_exc()

        except CaughtSignal as e:
            # Default Cement signals are SIGINT and SIGTERM, exit 0 (non-error)
            print('\n%s' % e)
            app.exit_code = 0


if __name__ == '__main__':
    main()
