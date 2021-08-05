import shutil
import traceback
from binascii import b2a_hex
from os import urandom
from pathlib import Path

from cgcrepair.core.corpus.challenge import Challenge
from cgcrepair.core.exc import NotEmptyDirectory
from cgcrepair.core.handlers.commands import CommandsHandler
from cgcrepair.core.corpus.manifest import Manifest
from shutil import copytree
from cgcrepair.core.handlers.database import Instance


class CheckoutHandler(CommandsHandler):
    class Meta:
        label = 'checkout'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set(self, no_patch: bool = False, working_dir: str = None, seed: int = None, force: bool = False):
        super().set()
        self.no_patch = no_patch
        self.working_dir = working_dir
        self.seed = seed
        self.force = force

        if not no_patch:
            self.env["PATCH"] = "True"

    def run(self, challenge: Challenge):
        try:
            working_dir = self._mkdir(challenge)
            working_dir_source = working_dir / challenge.name

            self._checkout_files(challenge.name, working_dir, working_dir_source)
            self._write_manifest(working_dir_source)

            # Inserting instance into database
            instance = Instance(m_id=challenge.id(), name=challenge.name, path=str(working_dir))
            _id = self.app.db.add(instance)

            # write the instance id to a file inside the working directory
            # useful to use in external scripts and to keep track locally of instances
            with (working_dir / '.instance_id').open(mode='w') as oid:
                oid.write(str(_id))

            print(f"Checked out {challenge.name} with id {_id}")

            return _id

        except Exception as e:
            self.error = str(e)
            self.app.log.warning(traceback.format_exc())
        finally:
            self.unset()

    def _mkdir(self, challenge: Challenge):
        # Make working directory
        if self.working_dir:
            working_dir = Path(self.working_dir)
        else:
            if not self.seed:
                seed = b2a_hex(urandom(2)).decode()

            working_dir = Path(self.app.config.get_config('working_dir'), f"{challenge.name}_{self.seed}")

        self.app.log.info(f"Checking out {challenge.name} to {working_dir}.")

        if working_dir.exists():
            if any(working_dir.iterdir()) and not self.force:
                raise NotEmptyDirectory(f"Working directory {working_dir} exists and is not empty.")
        else:
            self.app.log.info("Creating working directory.")
            working_dir.mkdir(parents=True)

        return working_dir

    def _checkout_files(self, challenge_name: str, working_dir: Path, working_dir_source: Path):
        self.app.log.info(f"Copying files to {working_dir}.")
        # Copy challenge source files
        working_dir_source.mkdir()
        corpus_handler = self.app.handler.get('corpus', 'corpus', setup=True)
        paths = corpus_handler.get_challenge_paths(challenge_name=challenge_name)
        self.app.log.warning(f"src {paths.source} dst {working_dir_source}")
        copytree(src=str(paths.source), dst=str(working_dir_source), dirs_exist_ok=True)

        # Copy CMakeLists.txt
        shutil.copy2(src=self.app.tools.cmake_file, dst=working_dir)

    def _write_manifest(self, working_dir_source: Path):
        if self.app.pargs.verbose:
            self.app.log.info(f"Writing manifest files.")

        manifest = Manifest(source_path=working_dir_source)
        manifest.write()

        if self.no_patch:
            vuln_files = ', '.join(manifest.vuln_files.keys())
            self.app.log.info(f"Removing patches definitions from vulnerable files {vuln_files}.")
            manifest.remove_patches(working_dir_source)
