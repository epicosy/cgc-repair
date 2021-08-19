from cement import Interface
from abc import abstractmethod


class CommandsInterface(Interface):
    class Meta:
        interface = 'commands'

    @abstractmethod
    def set(self, *args, **kwargs):
        pass

    @abstractmethod
    def run(self, **kwargs):
        pass

    @abstractmethod
    def unset(self, **kwargs):
        pass


class CorpusInterface(Interface):
    class Meta:
        interface = 'corpus'


class DatabaseInterface(Interface):
    class Meta:
        interface = 'database'


class RunnerInterface(Interface):
    class Meta:
        interface = 'runner'
