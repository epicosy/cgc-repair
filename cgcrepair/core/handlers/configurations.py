from cement.ext.ext_yaml import YamlConfigHandler
from pathlib import Path
from shutil import which


def key_not_found_msg(key: str):
    return f"'{key}' key not found in configurations"


def key_pos_int_msg(key: str, equal: bool = False):
    return f"'{key}' in configurations must be an integer greater than " + ("or equal" if equal else "") + "0"


class YamlConfigurations(YamlConfigHandler):
    class Meta:
        label = 'yaml_configurations'

    def __init__(self, **kw):
        super().__init__(**kw)

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
        corpus = self.get_config('corpus')
        tools = self.get_config('tools')
        polls = self.get_config('polls')
        gcov = self.get_config('gcov')
        python2 = self.get_config('python2')
        # povs = self.get_config('polls')

        assert corpus, key_not_found_msg('corpus')
        assert python2, key_not_found_msg('python2')
        assert gcov, key_not_found_msg('gcov')
        assert tools, key_not_found_msg('tools')
        assert polls, key_not_found_msg('polls')
        # assert povs, key_not_found_msg('povs')
        assert cores, key_not_found_msg('cores')
        assert working_dir, key_not_found_msg('working_dir')
        assert margin, key_not_found_msg('margin')
        assert timeout, key_not_found_msg('timeout')
        assert cwe_level, key_not_found_msg('cwe_level')

        assert Path(corpus).exists(), f'Corpus path {corpus} not found'
        assert which(gcov) is not None, f'GCOV executable {gcov} not found in PATH'
        assert which(python2) is not None, f'Python2 executable {python2} not found in PATH'
        assert Path(tools).exists(), f'Tools path {tools} not found'
        assert Path(polls).exists(), f'Polls path {polls} not found'
        # assert povs.exists(), f'POVs path {povs} not found'
        assert Path(cores).exists(), f"'cores' path {cores} in configurations not found"
        assert Path(working_dir).exists(), f"'working_dir' path {working_dir} in configurations not found"
        assert (margin > 0 and isinstance(margin, int)), key_pos_int_msg('margin')
        assert (timeout > 0 and isinstance(timeout, int)), key_pos_int_msg('timeout')
        assert (cwe_level >= 0 and isinstance(timeout, int)), key_pos_int_msg('cwe_level', equal=True)


def load(app):
    app.handler.register(YamlConfigurations)
