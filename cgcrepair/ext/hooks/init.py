import json
from pathlib import Path
from cgcrepair.core.corpus.challenge import Challenge
from cgcrepair.core.corpus.cwe_parser import CWEParser
from cgcrepair.core.corpus.manifest import Manifest


def init_metadata(app):
    metadata_file = Path('./metadata.json')
    metadata = {}

    if not metadata_file.exists():

        challenges = app.config.lib.get_challenges()
        challenges_count = len(challenges)

        for i, challenge_name in enumerate(challenges):
            app.log.info(f"Processing {challenge_name} for metadata. {i}/{challenges_count}")
            challenge_paths = app.config.lib.get_challenge_paths(challenge_name)
            challenge = Challenge(challenge_paths)
            cwe_parser = CWEParser(description=challenge.info(), level=app.config.get_config('cwe_level'))
            main_cwe = cwe_parser.cwe_type()
            manifest = Manifest(source_path=challenge_paths.source)
            patches = manifest.get_patches()
            vulns = manifest.get_vulns()

            metadata[challenge_name] = {'excluded': False, 'lines': manifest.total_lines,
                                        'vuln_lines': manifest.vuln_lines, 'patch_lines': manifest.patch_lines,
                                        'vuln_files': len(manifest.vuln_files), 'main_cwe': main_cwe,
                                        'vulns': vulns, 'patches': patches}

        with metadata_file.open(mode='w') as mf:
            json.dump(metadata, mf, indent=2)

    else:
        with metadata_file.open(mode='r') as mf:
            metadata = json.load(mf)

    app.extend('metadata', metadata)


def load(app):
    app.hook.register('post_setup', init_metadata)
