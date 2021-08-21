from dataclasses import dataclass, field
from typing import List, AnyStr, Any, Dict
from datetime import datetime

from cgcrepair.core.handlers.commands import CommandsHandler


@dataclass
class TaskData:
    run_args: Dict[AnyStr, Any]
    commands_handler: CommandsHandler
    run_ret: Any = None
    status: str = None
    start_date: datetime = None
    end_date: datetime = None
    err: AnyStr = None

    def duration(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).total_seconds()
        return 0

    def has_started(self):
        return self.status == "Started"

    def start(self):
        self.start_date = datetime.now()
        self.status = "Started"

    def wait(self):
        self.status = "Waiting"

    def error(self, msg: AnyStr):
        self.status = "Error"
        self.err = msg
        self.end_date = datetime.now()

    def done(self):
        if self.has_started():
            self.status = "Done"
        else:
            self.status = "Finished"

        self.end_date = datetime.now()


@dataclass
class Runner:
    tasks: List[TaskData] = field(default_factory=lambda: [])
    finished: List[TaskData] = field(default_factory=lambda: [])
    running: List[TaskData] = field(default_factory=lambda: [])
    waiting: List[TaskData] = field(default_factory=lambda: [])

    def done(self, task: TaskData):
        task.done()
        self.finished += [task]
        self.running.remove(task)
