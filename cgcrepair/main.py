from cement import App, TestApp
from cement.core.exc import CaughtSignal
from .core.exc import CGCRepairError

# Controllers
from .controllers.base import Base
from cgcrepair.controllers.corpus import Corpus
from cgcrepair.controllers.instance import Instance
from cgcrepair.controllers.database import Database

# Handlers
from cgcrepair.core.handlers.configurations import YamlConfigurations
from cgcrepair.core.handlers.commands import CommandsHandler
from cgcrepair.core.handlers.corpus import CorpusHandler
from cgcrepair.core.handlers.database import MetadataHandler
from cgcrepair.core.handlers.operations.checkout import CheckoutHandler
from cgcrepair.core.handlers.operations.genpolls import GenPollsHandler
from cgcrepair.core.handlers.operations.genpovs import GenPOVsHandler
from cgcrepair.core.handlers.database import InstanceHandler
from cgcrepair.core.handlers.operations.make import MakeHandler
from cgcrepair.core.handlers.operations.compile import CompileHandler
from cgcrepair.core.handlers.operations.test import TestHandler

from cgcrepair.core.interfaces import CommandsInterface, DatabaseInterface, CorpusInterface


class CGCRepair(App):
    """cgcrepair primary application."""

    class Meta:
        label = 'cgcrepair'

        # call sys.exit() on close
        exit_on_close = True

        interfaces = [
            CommandsInterface, DatabaseInterface, CorpusInterface
        ]

        # load additional framework extensions
        extensions = [
            'cgcrepair.ext.hooks.init',
            'colorlog',
            'jinja2',
        ]

        # configuration handler
        config_handler = 'yaml_configurations'

        # configuration file suffix
        config_file_suffix = '.yml'

        # set the log handler
        log_handler = 'colorlog'

        # set the output handler
        output_handler = 'jinja2'

        # register handlers
        handlers = [
            Base, YamlConfigurations, CommandsHandler, CorpusHandler,
            Corpus, CheckoutHandler, GenPollsHandler, GenPOVsHandler,
            Instance, MakeHandler, CompileHandler, TestHandler,
            InstanceHandler, Database, MetadataHandler
        ]


class CGCRepairTest(TestApp, CGCRepair):
    """A sub-class of CGCRepair that is better suited for testing."""

    class Meta:
        label = 'cgcrepair'


def main():
    with CGCRepair() as app:
        try:
            app.config.validate()
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
