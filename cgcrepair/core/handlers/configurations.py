from cement.ext.ext_yaml import YamlConfigHandler
from pathlib import Path
from os.path import dirname

from cgcrepair.utils.data import LibPaths, Tools

ROOT_DIR = dirname(dirname(dirname(dirname(__file__))))


def key_not_found_msg(key: str):
    return f"'{key}' key not found in configurations"


def key_pos_int_msg(key: str, equal: bool = False):
    return f"'{key}' in configurations must be an integer greater than " + ("or equal" if equal else "") + "0"


class YamlConfigurations(YamlConfigHandler):
    class Meta:
        label = 'yaml_configurations'

    def __init__(self, **kw):
        super().__init__(**kw)
        self.lib = None
        self.tools = None

    def _parse_file(self, file_path):
        super()._parse_file(file_path)

        # TODO: pick root paths from config file
        lib_root = Path(ROOT_DIR, 'lib')
        tools_root = Path(ROOT_DIR, 'tools')

        self.lib = LibPaths(root=lib_root, polls=lib_root / 'polls', povs=lib_root / 'povs',
                            challenges=lib_root / 'challenges')
        self.tools = Tools(root=tools_root, cmake_file=Path(ROOT_DIR, 'cmake', 'CMakeLists.txt'),
                           cmake_file_no_patch=Path(ROOT_DIR, 'cmake', 'CMakeListsNoPatch.txt'),
                           test=tools_root / 'cb-test.py',
                           genpolls=tools_root / Path('generate-polls', 'generate-polls'))

    def get_config(self, key: str):
        if self.has_section('cgcrepair'):
            if key in self.keys('cgcrepair'):
                return self.get('cgcrepair', key)

        return None

    def validate(self):
        timeout = self.get_config('tests_timeout')
        margin = self.get_config('margin')
        cwe_level = self.get_config('cwe_level')
        cores = self.get_config('cores')
        working_dir = self.get_config('working_dir')

        assert cores, key_not_found_msg('cores')
        assert working_dir, key_not_found_msg('working_dir')
        assert margin, key_not_found_msg('margin')
        assert timeout, key_not_found_msg('timeout')
        assert cwe_level, key_not_found_msg('cwe_level')

        assert Path(cores).exists(), f"'cores' path {cores} in configurations not found"
        assert Path(working_dir).exists(), f"'working_dir' path {working_dir} in configurations not found"
        assert (margin > 0 and isinstance(margin, int)), key_pos_int_msg('margin')
        assert (timeout > 0 and isinstance(timeout, int)), key_pos_int_msg('timeout')
        assert (cwe_level >= 0 and isinstance(timeout, int)), key_pos_int_msg('cwe_level', equal=True)

        self.lib.validate()
        self.tools.validate()


def load(app):
    app.handler.register(YamlConfigurations)
