import time

from queue import Queue
from typing import List
from threading import Thread

from cement import Handler
from cement.core.log import LogHandler

from cgcrepair.core.data.store import Runner, TaskData
from cgcrepair.core.interfaces import RunnerInterface


class TaskWorker(Thread):
    def __init__(self, queue: Queue, logger: LogHandler):
        Thread.__init__(self)
        self.queue = queue
        self.daemon = True
        self.logger = logger
        self.start()

    def run(self):
        while True:
            (task, callback) = self.queue.get()
            task.start()

            try:
                self.logger.info(f"Running {task.commands_handler.Meta.label}")
                # task.commands_handler.set()
                task.run_ret = task.commands_handler.run(**task.run_args)

                if task.commands_handler.error:
                    self.logger.error(f"{task.commands_handler.Meta.label} failed: {task.commands_handler.error}")
                else:
                    self.logger.info(f"{task.commands_handler.Meta.label} command ran without errors.")

            except Exception as e:
                task.error(str(e))
                raise e.with_traceback(e.__traceback__)
            finally:
                if callback is not None:
                    callback(task)
                self.queue.task_done()
                self.logger.info(f"Task duration: {task.duration()}")
                print(task)


class ThreadPoolWorker(Thread):
    """Pool of threads consuming tasks from a queue"""
    def __init__(self, runner_data: Runner, tasks: List[TaskData], threads: int, logger: LogHandler):
        Thread.__init__(self)
        self.runner_data = runner_data
        self.tasks = tasks
        self.daemon = True
        self.logger = logger
        self.queue = Queue(threads)
        self.workers = []

        for _ in range(threads):
            self.workers.append(TaskWorker(self.queue, logger))

    def run(self):
        for task in self.tasks:
            self.runner_data.running += [task]
            task.wait()
            self.logger.info(f"Adding task for {task.commands_handler.Meta.label} handler to the queue.")
            self.add_task(task)

        """Wait for completion of all the tasks in the queue"""
        self.queue.join()

    def add_task(self, task: TaskData):
        """Add a task to the queue"""
        if task.status is not None:
            self.queue.put((task, self.runner_data.done))


class RunnerHandler(RunnerInterface, Handler):
    class Meta:
        label = 'runner'

    def __call__(self, tasks: List[TaskData], threads: int = 2) -> Runner:
        runner_data = Runner()
        worker = ThreadPoolWorker(runner_data, tasks=tasks, threads=threads, logger=self.app.log)
        worker.start()

        while worker.is_alive():
            time.sleep(1)

        return runner_data
