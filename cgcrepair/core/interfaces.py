from cement import Interface
from abc import abstractmethod


class CommandsInterface(Interface):
    class Meta:
        interface = 'commands'

    @abstractmethod
    def set(self):
        pass

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def unset(self):
        pass


class CorpusInterface(Interface):
    class Meta:
        interface = 'corpus'
