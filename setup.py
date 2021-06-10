
from setuptools import setup, find_packages
from cgcrepair.core.version import get_version

VERSION = get_version()

f = open('README.md', 'r')
LONG_DESCRIPTION = f.read()
f.close()

setup(
    name='cgcrepair',
    version=VERSION,
    description='DARPA CGC challenge set extended into a benchmark for Automatic Program Repair tools.',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    author='Eduard Pinconschi',
    author_email='eduard.pinconschi@tecnico.ulisboa.pt',
    url='https://github.com/epicosy/cgc-repair',
    license='MIT',
    packages=find_packages(exclude=['ez_setup', 'tests*']),
    package_data={'cgcrepair': ['templates/*']},
    include_package_data=True,
    entry_points="""
        [console_scripts]
        cgcrepair = cgcrepair.main:main
    """,
)
