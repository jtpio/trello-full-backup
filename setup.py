from setuptools import setup, find_packages

# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='trello-full-backup',
    packages=find_packages(),
    version='0.2.3',
    author='Jeremy Tuloup',
    author_email='jerem@jtp.io',
    url='https://github.com/jtpio/trello-full-backup',
    description='Backup everything from Trello',
    long_description=long_description,
    license='MIT',
    classifiers=[
        'Topic :: System :: Archiving :: Backup',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ],
    install_requires=['requests'],
    entry_points={
        'console_scripts': [
            'trello-full-backup = trello_full_backup:main'
        ]
    }
)
