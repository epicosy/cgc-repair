import os
from pathlib import Path

import yaml
from sqlalchemy.exc import OperationalError

from cgcrepair.core.exc import CGCRepairError
from cgcrepair.core.handlers.database import Metadata, Database, Vulnerability
from cgcrepair.utils.data import Tools


def bind_tools(app):
    tools_root = Path(app.config.get_config('tools'))
    corpus = Path(app.config.get_config('corpus'))

    tools = Tools(cmake_file=corpus / 'CMakeLists.txt', test=tools_root / 'cb-test.py',
                  genpolls=tools_root / Path('generate-polls', 'generate-polls'))

    app.extend('tools', tools)


def init_metadata(app):
    try:
        database = Database(dialect=app.config.get_config('dialect'), username=app.config.get_config('username'),
                            password=app.config.get_config('password'), host=app.config.get_config('host'),
                            port=app.config.get_config('port'), database=app.config.get_config('database'),
                            debug=app.config.get('log.colorlog', 'database'))

        if not database.query(Metadata):
            corpus_handler = app.handler.get('corpus', 'corpus', setup=True)
            metadata_handler = app.handler.get('database', 'metadata', setup=True)
            challenges = corpus_handler.get_challenges()
            challenges_count = len(challenges)

            with open(app.config.get_config("metadata")) as mp:
                yaml_metadata = yaml.load(mp, Loader=yaml.FullLoader)

            for i, challenge_name in enumerate(challenges):
                app.log.info(f"Processing {challenge_name} for metadata. {i}/{challenges_count}")
                challenge = corpus_handler.get(challenge_name)
                metadata = metadata_handler(challenge)

                if metadata.vuln_files > 1:
                    app.log.info(f"Removing multi-file challenge: {challenge_name}.")
                    os.system(f"rm -rf {challenge.paths.source}")
                    continue

                if metadata.multi_cb:
                    app.log.info(f"Removing challenge with multiple binaries: {challenge_name}.")
                    os.system(f"rm -rf {challenge.paths.source}")
                    continue

                if metadata.id in yaml_metadata:
                    for pov, pov_metadata in yaml_metadata[metadata.id]['pov'].items():
                        if 'related' in pov_metadata:
                            related = ';'.join([str(r) for r in pov_metadata['related']])
                        else:
                            related = None
                        vuln = Vulnerability(id=f"{metadata.id}_{pov}", cwe=pov_metadata['cwe'], related=related,
                                             test=f"n{pov}")

                        metadata.vid = database.add(vuln)
                        database.add(metadata)

        app.extend('db', database)

    except OperationalError as oe:
        raise CGCRepairError(oe)


def load(app):
    app.hook.register('post_setup', init_metadata)
    app.hook.register('pre_run', bind_tools)
