from cement.ext.ext_yaml import YamlConfigHandler
from pathlib import Path
from os.path import dirname

from cgcrepair.utils.data import LibPaths, Tools

ROOT_DIR = dirname(dirname(dirname(dirname(__file__))))


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
        cores = self.get_config('cores')

        assert cores, f"'cores' key not found in configurations"
        assert margin, f"'margin' key not found in configurations"
        assert timeout, f"'timeout' key not found in configurations"

        assert Path(cores).exists(), f"'cores' path in configurations {cores} not found"
        assert (margin > 0 and isinstance(margin, int)), "'margin' in configurations must be an integer greater than 0"
        assert (timeout > 0 and isinstance(timeout, int)), \
            "'timeout' in configurations must be an integer greater than 0"

        self.lib.validate()
        self.tools.validate()


def load(app):
    app.handler.register(YamlConfigurations)
