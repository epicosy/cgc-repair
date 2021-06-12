from cgcrepair.core.corpus.challenge import Challenge
from cgcrepair.core.corpus.cwe_parser import CWEParser
from cgcrepair.core.corpus.manifest import Manifest
from cgcrepair.core.handlers.database import Metadata, Database


def init_metadata(app):
    database = Database(debug=app.config.get_config('debug'))

    if not database.query(Metadata):

        challenges = app.config.lib.get_challenges()
        challenges_count = len(challenges)

        for i, challenge_name in enumerate(challenges):
            app.log.info(f"Processing {challenge_name} for metadata. {i}/{challenges_count}")
            challenge_paths = app.config.lib.get_challenge_paths(challenge_name)
            challenge = Challenge(challenge_paths)
            cwe_parser = CWEParser(description=challenge.info(), level=app.config.get_config('cwe_level'))
            manifest = Manifest(source_path=challenge_paths.source)

            metadata = Metadata()
            metadata.name = challenge_name
            metadata.excluded = False
            metadata.total_lines = manifest.total_lines
            metadata.vuln_lines = manifest.vuln_lines
            metadata.patch_lines = manifest.patch_lines
            metadata.vuln_files = len(manifest.vuln_files)
            metadata.main_cwe = cwe_parser.cwe_type()
            # metadata.vulns = manifest.get_vulns()
            # metadata.patches = manifest.get_patches()

            database.add(metadata)

    app.extend('db', database)


def load(app):
    app.hook.register('post_setup', init_metadata)
