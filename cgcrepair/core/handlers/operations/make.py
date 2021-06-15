import traceback
import platform
from json import loads
from pathlib import Path

from cgcrepair.core.corpus.manifest import Manifest
from cgcrepair.core.exc import CommandError
from cgcrepair.core.handlers.commands import CommandsHandler
from cgcrepair.core.handlers.database import CompileOutcome, Instance
from cgcrepair.utils.data import WorkingPaths, CompileCommand


class MakeHandler(CommandsHandler):
    class Meta:
        label = 'make'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.compile_commands = {}
        self.cmake_opts = ""

    def set(self):
        super().set()
        self.cmake_opts = f"{self.env['CMAKE_OPTS']}" if 'CMAKE_OPTS' in self.env else ""

        if self.app.pargs.replace:
            self.cmake_opts = f"{self.cmake_opts} -DCMAKE_CXX_OUTPUT_EXTENSION_REPLACE=ON"

        self.cmake_opts = f"{self.cmake_opts} -DCMAKE_EXPORT_COMPILE_COMMANDS=ON"

        if self.app.pargs.save_temps:
            self.env["SAVETEMPS"] = "True"

        # setting platform architecture
        if '64bit' in platform.architecture()[0]:
            self.cmake_opts = f"{self.cmake_opts} -DCMAKE_SYSTEM_PROCESSOR=amd64"
        else:
            self.cmake_opts = f"{self.cmake_opts} -DCMAKE_SYSTEM_PROCESSOR=i686"

        # clang as default compiler
        if "CC" not in self.env:
            self.env["CC"] = "clang"

        if "CXX" not in self.env:
            self.env["CXX"] = "clang++"

        c_compiler = f"-DCMAKE_C_COMPILER={self.env['CC']}"
        asm_compiler = f"-DCMAKE_ASM_COMPILER={self.env['CC']}"
        cxx_compiler = f"-DCMAKE_CXX_COMPILER={self.env['CXX']}"

        # Default shared libs
        build_link = "-DBUILD_SHARED_LIBS=ON -DBUILD_STATIC_LIBS=OFF"

        if "LINK" in self.env and self.env["LINK"] == "STATIC":
            build_link = "-DBUILD_SHARED_LIBS=OFF -DBUILD_STATIC_LIBS=ON"

        self.cmake_opts = f"{self.cmake_opts} {c_compiler} {asm_compiler} {cxx_compiler} {build_link}"

    def _make(self, source: Path, name: str, dest: Path):
        if not dest.exists():
            self.app.log.info("Creating build directory")
            dest.mkdir(exist_ok=True)

        super().__call__(cmd_str=f"cmake {self.cmake_opts} {source} -DCB_PATH:STRING={name}",
                         msg="Creating build files.", cmd_cwd=str(dest), raise_err=True)

    def run(self):
        try:
            instance_handler = self.app.handler.get('database', 'instance', setup=True)
            instance = instance_handler.get(instance_id=self.app.pargs.id)
            working = instance.working()

            self._make(working.root, instance.name, working.build_root)

            if self.app.pargs.write_build_args:
                self._write_build_args(working)

        except CommandError as ce:
            self.error = str(ce)
        finally:
            self.unset()

    def unset(self):
        if self.app.pargs.save_temps:
            del self.env["SAVETEMPS"]

    def _write_build_args(self, working: WorkingPaths):
        manifest = Manifest(source_path=working.source)
        write_build_args = Path(self.app.pargs.write_build_args)

        if not self.compile_commands:
            self.load_commands(working)

        for fname, _ in {**manifest.source_files, **manifest.vuln_files}.items():
            if fname.endswith(".h"):
                continue
            compile_command = self.compile_commands[fname]

            with write_build_args.open(mode="a") as baf:
                cmd = compile_command.command.split()
                bargs = ' '.join(cmd[1:-2])
                baf.write(f"{working.root}\n{bargs}\n")

            write_build_args.chmod(0o777)

    def load_commands(self, working: WorkingPaths):
        compile_commands_file = working.build_root / Path('compile_commands.json')

        with compile_commands_file.open(mode="r") as json_file:
            for entry in loads(json_file.read()):
                if self.app.pargs.compiler_trail_path:
                    entry['command'] = entry['command'].replace('/usr/bin/', '')
                compile_command = CompileCommand(file=Path(entry['file']), dir=Path(entry['directory']),
                                                 command=entry['command'])
                if "-DPATCHED" not in compile_command.command:
                    # Looking for the path within the source code folder
                    if str(compile_command.file).startswith(str(working.source)):
                        short_path = compile_command.file.relative_to(working.source)
                    else:
                        short_path = compile_command.file.relative_to(working.root)
                    self.compile_commands[str(short_path)] = compile_command

    def save_outcome(self):
        outcome = CompileOutcome()
        outcome.instance_id = self.app.pargs.id
        outcome.error = self.error
        outcome.exit_status = self.return_code

        if self.app.pargs.tag:
            outcome.tag = self.app.pargs.tag
        else:
            outcome.tag = self.Meta.label

        co_id = self.app.db.add(outcome)
        self.app.db.update(entity=Instance, entity_id=self.app.pargs.id, attr='pointer', value=co_id)
        self.app.log.info(f"Inserted '{self.Meta.label} outcome' with id {co_id} for instance {self.app.pargs.id}.")
