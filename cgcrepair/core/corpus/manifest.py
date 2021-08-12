import json
from typing import Dict, List, NoReturn
from pathlib import Path

from cgcrepair.core.corpus.source_file import SourceFile


EXTENSIONS = (".c", ".cc", ".h")
IGNORE = ("polls", "poller", "support")


class Manifest:
    def __init__(self, source_path: Path, out_dir: str = None):
        self.root = source_path

        if out_dir:
            out_dir = Path(out_dir)
            self.file = out_dir / 'manifest' if out_dir.is_dir() else out_dir
        else:
            self.file = source_path / 'manifest'

        self.vuln_file = source_path / 'vuln'
        self.source_files: Dict[(str, SourceFile)] = {}
        self.vuln_files: Dict[(str, SourceFile)] = {}
        self.total_lines = 0
        self.vuln_lines = 0
        self.patch_lines = 0
        self.multi_cb = len([d for d in self.root.iterdir() if d.is_dir() and d.name.startswith('cb_')]) > 0
        self.collect_files()

    def collect_files(self) -> NoReturn:
        def recurse_walk(current: Path, parent: Path):
            for f in current.iterdir():
                if f.is_dir():
                    recurse_walk(f, parent / Path(f.name))
                elif f.name.endswith(EXTENSIONS):
                    short_path = str(parent / Path(f.name))
                    src_file = SourceFile(f)
                    self.total_lines += src_file.total_lines

                    if src_file.has_snippets():
                        self.vuln_files[short_path] = src_file
                        self.vuln_lines += src_file.vuln_lines
                        self.patch_lines += src_file.patch_lines
                    else:
                        self.source_files[short_path] = src_file

        for folder in self.root.iterdir():
            if folder.name not in IGNORE and not folder.name.startswith('pov') and folder.is_dir():
                recurse_walk(folder, Path(folder.name))

    def get_snippets(self):
        return {f_name: src_file.snippets for f_name, src_file in self.vuln_files.items()}

    def get_patches(self):
        return {f_name: src_file.get_patch() for f_name, src_file in self.vuln_files.items()}

    def get_vulns(self):
        return {f_name: src_file.get_vuln() for f_name, src_file in self.vuln_files.items()}

    def write(self) -> NoReturn:
        with self.file.open(mode="w") as of, self.vuln_file.open(mode="w") as vf:
            of.writelines('\n'.join(list(self.vuln_files.keys())))
            vulns = self.get_vulns()
            json.dump(vulns, vf, indent=2)

    def remove_patches(self, source: Path):
        new_vuln = {}

        with self.file.open(mode='r') as mf:
            files = mf.read().splitlines()

            for file in files:
                src_file = SourceFile(source / Path(file))
                src_file.remove_patch()
                new_vuln.update({file: src_file.get_vuln()})

        with self.vuln_file.open(mode='w') as vf:
            json.dump(new_vuln, vf, indent=2)


# TODO: this might fail in cases where the header files have files associated
def map_instrumented_files(instrumented_files: List[str], cpp_files: bool, manifest_path: Path) -> Dict[(str, str)]:
    mapping = {}

    with manifest_path.open(mode="r") as mp:
        manifest_files = mp.read().splitlines()
        manifest_files = [mf.split(":")[0] for mf in manifest_files]

    for short_path in manifest_files:
        if short_path.endswith(".h"):
            continue
        if cpp_files:
            short_path = short_path.replace('.c', '.i')

        for inst_file in instrumented_files:
            if short_path in inst_file:
                if cpp_files:
                    short_path = short_path.replace('.i', '.c')
                mapping[short_path] = inst_file
                break

    return mapping
