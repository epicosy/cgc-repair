import shutil
from binascii import b2a_hex
from os import urandom
from pathlib import Path

from cgcrepair.core.exc import NotEmptyDirectory
from cgcrepair.core.handlers.commands import CommandsHandler
from cgcrepair.core.corpus.manifest import Manifest
from distutils.dir_util import copy_tree
from cgcrepair.core.handlers.database import Instance


class CheckoutHandler(CommandsHandler):
    class Meta:
        label = 'checkout'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.instance = Instance()

    def run(self):
        try:
            working_dir = self._mkdir()
            working_dir_source = working_dir / self.app.pargs.challenge

            self._checkout_files(working_dir, working_dir_source)
            self._write_manifest(working_dir_source)

            # Inserting instance into database
            self.instance.name = self.app.pargs.challenge
            self.instance.path = str(working_dir)
            _id = self.app.db.add(self.instance)

            self.app.log.info(f"Checked out {self.app.pargs.challenge} with id {_id}")

        except Exception as e:
            self.error = str(e)
        finally:
            self.unset()

    def _mkdir(self):
        # Make working directory
        if self.app.pargs.working_dir:
            working_dir = self.app.pargs.working_dir
        else:
            if self.app.pargs.seed:
                seed = self.app.pargs.seed
            else:
                seed = b2a_hex(urandom(2)).decode()

            working_dir = Path(self.app.config.get_config('working_dir'), f"{self.app.pargs.challenge}_{seed}")

        self.app.log.info(f"Checking out {self.app.pargs.challenge} to {working_dir}.")

        if working_dir.exists():
            if any(working_dir.iterdir()):
                raise NotEmptyDirectory(f"Working directory {working_dir} exists and is not empty.")
        else:
            self.app.log.info("Creating working directory.")
            working_dir.mkdir(parents=True)

        return working_dir

    def _checkout_files(self, working_dir: Path, working_dir_source: Path):
        self.app.log.info(f"Copying files to {working_dir}.")
        # Copy challenge source files
        working_dir_source.mkdir()
        paths = self.app.config.lib.get_challenge_paths(challenge_name=self.app.pargs.challenge)
        copy_tree(src=str(paths.source), dst=str(working_dir_source))

        # Copy CMakeLists.txt
        cmake_file = self.app.config.tools.cmake_file_no_patch if self.app.pargs.no_patch else self.app.config.tools.cmake_file
        dst_cmake_file = shutil.copy2(src=cmake_file, dst=working_dir)

        if self.app.pargs.no_patch:
            p_dst_cmake_file = Path(dst_cmake_file)
            p_dst_cmake_file.rename(Path(p_dst_cmake_file.parent, "CMakeLists.txt"))

    def _write_manifest(self, working_dir_source: Path):
        if self.app.pargs.verbose:
            self.app.log.info(f"Writing manifest files.")

        manifest = Manifest(source_path=working_dir_source)
        manifest.write()

        if self.app.pargs.no_patch:
            self.app.log.info(f"Removing patches definitions from vulnerable files {manifest.vuln_files.keys()}.")
            manifest.remove_patches(working_dir_source)
