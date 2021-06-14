import subprocess
import psutil
import time

from os import environ
from typing import Union, AnyStr, Tuple, List
from threading import Timer

from cement import Handler

from cgcrepair.core.exc import CommandError
from cgcrepair.core.interfaces import CommandsInterface


class CommandsHandler(CommandsInterface, Handler):
    class Meta:
        label = 'commands'

    def __init__(self, **kw):
        super().__init__(**kw)
        self.env = None
        self.return_code = 0
        self.output, self.error = None, None

    def set(self):
        self.env = environ.copy()
        self.env["CGC_INCLUDE_DIR"] = self.app.config.get_config('include')
        lib_root = self.app.config.get_config('lib')
        self.env["CGC_LIB_DIR"] = f"{lib_root};{lib_root}/libpov;{lib_root}/aes"
        ld_lib_path = f"{lib_root}/polls:{lib_root}:{lib_root}/aes"

        if "LD_LIBRARY_PATH" in self.env:
            self.env["LD_LIBRARY_PATH"] = ld_lib_path + ":" + self.env["LD_LIBRARY_PATH"]
        else:
            self.env["LD_LIBRARY_PATH"] = ld_lib_path

    def run(self):
        pass

    def unset(self):
        pass

    def _exec(self, proc: subprocess.Popen):
        out = []

        for line in proc.stdout:
            decoded = line.decode()
            out.append(decoded)

            if self.app.pargs.verbose:
                self.app.log.info(decoded)

        self.output = ''.join(out)

        proc.wait(timeout=1)

        if proc.returncode and proc.returncode != 0:
            self.return_code = proc.returncode
            proc.kill()
            self.error = proc.stderr.read().decode()

            if self.error:
                self.app.log.error(self.error)

    def __call__(self, cmd_str: Union[AnyStr, List[AnyStr]], cmd_cwd: str = None, msg: str = None, timeout: int = None,
                 raise_err: bool = False, exit_err: bool = False) -> Tuple[Union[str, None], Union[str, None], float]:

        if msg and self.app.pargs.verbose:
            self.app.log.info(msg)

        self.app.log.debug(cmd_str, __name__)

        # based on https://stackoverflow.com/a/28319191
        with subprocess.Popen(args=cmd_str, shell=isinstance(cmd_str, str), stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, env=self.env, cwd=cmd_cwd) as proc:

            time_start = time.time()

            if timeout:
                timer = Timer(timeout, _timer_out, args=[proc, self])
                timer.start()
                self._exec(proc)
                proc.stdout.close()
                timer.cancel()
            else:
                self._exec(proc)

            time_delta = time.time() - time_start

            if raise_err and self.error:
                raise CommandError(self.error)

            if exit_err and self.error:
                exit(proc.returncode)

            return self.output, self.error, time_delta


# https://stackoverflow.com/a/54775443
def _timer_out(p: subprocess.Popen, cmd: CommandsHandler):
    cmd.error = "Command timed out"
    process = psutil.Process(p.pid)
    cmd.return_code = p.returncode if p.returncode else -3

    for proc in process.children(recursive=True):
        proc.kill()

    process.kill()


def load(app):
    app.handler.register(CommandsHandler)
