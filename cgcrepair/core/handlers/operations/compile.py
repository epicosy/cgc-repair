import shutil
from pathlib import Path

from cgcrepair.core.corpus.challenge import Challenge
from cgcrepair.core.exc import CommandError
from cgcrepair.core.handlers.database import CompileOutcome, Instance
from cgcrepair.core.handlers.operations.make import MakeHandler
from cgcrepair.core.corpus.manifest import map_instrumented_files
from cgcrepair.utils.data import WorkingPaths


class CompileHandler(MakeHandler):
    class Meta:
        label = "compile"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fixes = []

    def set(self):
        super().set()

        if self.app.pargs.coverage:
            self.env["COVERAGE"] = "True"

        if self.app.pargs.fix_files:
            if not isinstance(self.app.pargs.fix_files, list):
                self.fixes = [self.app.pargs.fix_files]
            else:
                self.fixes = self.app.pargs.fix_files

    def run(self, instance: Instance, working: WorkingPaths):
        try:
            if self.fixes and self.app.pargs.inst_files and len(self.fixes) != len(self.app.pargs.inst_files):
                error = f"The files [{self.fixes}] can not be mapped. Uneven number of files [{self.app.pargs.inst_files}]."
                raise ValueError(error)

            # Backups manifest files
            if self.app.pargs.backup:
                self._backup_manifest_files(working)

            if self.app.pargs.link:
                self.link_executable(working)
            elif self.app.pargs.inst_files:
                self.build_instrumented(working)
            else:
                self.app.log.info(f"Compiling {instance.name}.")
                super().run(instance, working)
                super().__call__(cmd_str=f"cmake --build . --target {instance.name}",
                                 msg=f"Building {working.source.name}\n", raise_err=True,
                                 cmd_cwd=str(working.build_root))
                self.app.log.info(f"Compiled {instance.name}.")

        except CommandError as ce:
            self.error = str(ce)
        finally:
            self.unset()

    def unset(self):
        if self.app.pargs.coverage and 'COVERAGE' in self.env:
            del self.env['COVERAGE']

    def _backup_manifest_files(self, working: WorkingPaths):
        backup_path = Path(self.app.pargs.backup)
        manifest_file = working.source / 'manifest'

        with manifest_file.open(mode="r") as mf:
            files = mf.readlines()

            for file in files:
                file_path = Path(file)
                bckup_path = backup_path / file_path.parent

                if not bckup_path.exists():
                    bckup_path.mkdir(parents=True, exist_ok=True)

                count = self.app.db.count(CompileOutcome) + 1
                bckup_file = bckup_path / f"{file_path.stem}_{count}{file_path.suffix}"
                super().__call__(cmd_str=f"cp {file} {bckup_file}", cmd_cwd=str(working.source),
                                 msg=f"Backup of manifest file {file} to {backup_path}.\n", raise_err=True)

    def build_instrumented(self, working: WorkingPaths):
        self.app.log.info(f"Compiling preprocessed file for {working.source.name}.")
        # compile the preprocessed file to object
        self.load_commands(working)
        mapping = map_instrumented_files(self.app.pargs.inst_files, cpp_files=self.app.pargs.cpp_files,
                                         manifest_path=working.source / 'manifest')

        if mapping:
            # creating object files
            for source_file, cpp_file in mapping.items():
                self.build_file(source_file, cpp_file, working=working)

            # links objects into executable
            self.link_executable(working)
            self.app.log.info(f"Compiled instrumented files {self.app.pargs.inst_files}.")
        else:
            self.error = f"Could not map fix files {self.fixes} with source files."

    def build_file(self, source_file: str, cpp_file: str, working: WorkingPaths):
        if self.fixes:
            cpp_file = self.fixes.pop(0)

            # if self.app.pargs.prefix:
            #    cpp_file = str(self.app.pargs.prefix / Path(cpp_file))

        if Path(cpp_file).exists():
            compile_command = self.get_compile_command(source_file, cpp_file)
            super().__call__(cmd_str=compile_command, msg=f"Creating object file for {cpp_file}.\n",
                             cmd_cwd=str(working.build), raise_err=True)
        else:
            self.error = f"File {cpp_file} not found."

    def link_executable(self, working: WorkingPaths):
        self.app.log.info(f"Linking into executable {working.source.name}.")
        link_file = working.cmake / Path("link.txt")

        if link_file.exists():
            cmd_str = f"cmake -E cmake_link_script {link_file} {working.source.name}"
            super().__call__(cmd_str=cmd_str, msg="Linking object files into executable.\n", cmd_cwd=str(working.build),
                             raise_err=True)
        else:
            self.error = f"Link file {link_file} found"

    def get_compile_command(self, manifest_file: str, instrumented_file: str = None):
        if manifest_file in self.compile_commands:
            compile_command = self.compile_commands[manifest_file]
            modified_command = compile_command.command.replace('-save-temps=obj', '')

            if instrumented_file:
                modified_command = modified_command.replace(str(compile_command.file), instrumented_file)

            return modified_command
        else:
            self.error = "Could not find compile command."
            return None

    def install_shared_objects(self, challenge: Challenge):
        # check if shared objects are installed
        challenge_id = challenge.id()

        if challenge.has_shared_objects():
            lib_polls_dir = Path(self.app.config.get_config('lib'), 'polls')
            lib_id_path = lib_polls_dir / f"lib{challenge_id}.so"

            if lib_id_path.exists():
                self.app.log.info(f"Shared objects {lib_id_path.name} already installed.")
            else:
                build = Path('/tmp', challenge_id)
                build.mkdir(parents=True)

                # make files
                super()._make(source=self.app.config.get_config('corpus'), name=challenge.name, dest=build)
                # build shared objects
                super().__call__(cmd_str=f"cmake --build . --target {challenge_id}", msg=f"Building {challenge_id}",
                                 raise_err=True, cmd_cwd=str(build))

                # install shared objects
                super().__call__(cmd_str=f"cmake --install {build}", raise_err=True, cmd_cwd=str(build),
                                 msg=f"Installing shared objects {lib_id_path.name} for {challenge.name}.")

                self.app.log.info(f"Installed shared objects.")

                shutil.rmtree(str(build))

    def build_povs(self, challenge: Challenge):
        if not challenge.paths.povs.exists():
            self.app.log.info(f"Creating directory for {challenge.name} POVs.")
            challenge.paths.povs.mkdir(parents=True)

        build_dir = Path('/tmp', challenge.name + "_povs")

        povs = [str(f.name) for f in challenge.paths.source.iterdir() if f.name.startswith('pov') and f.is_dir()]
        povs.sort()

        super()._make(source=self.app.config.get_config('corpus'), name=challenge.name, dest=build_dir)

        # build povs
        for pov in povs:
            super().__call__(cmd_str=f"cmake --build . --target {challenge.name}_{pov}", cmd_cwd=str(build_dir),
                             raise_err=True, msg=f"Building {challenge.name} POVs")
            shutil.copy2(f"{build_dir}/{challenge.name}/{pov}.pov", challenge.paths.povs)

        self.app.log.info(f"Built POVs for {challenge.name}.")

        shutil.rmtree(str(build_dir))
