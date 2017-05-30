Trello Full Backup
==================

.. image:: https://img.shields.io/pypi/v/trello-full-backup.svg?style=flat-square
    :target: https://pypi.python.org/pypi/trello-full-backup

.. image:: https://img.shields.io/pypi/pyversions/trello-full-backup.svg?style=flat-square
    :target: https://pypi.python.org/pypi/trello-full-backup

.. image:: https://img.shields.io/docker/automated/jtpio/trello-full-backup.svg?style=flat-square
    :target: https://hub.docker.com/r/jtpio/trello-full-backup/

Backup everything from Trello:

- boards, open and closed, as json files
- lists, open and archived, as json files
- cards, open and archived, as json files
- attachments, downloaded as raw files

The script also creates a **folder tree structure** corresponding to the
way data is organized. This is to make it more convenient to navigate
locally between folders, as it mimics the flow you have when using the
web and mobile apps.

Here is an example of what the tree structure looks like:

::

    2015-11-12_23-28-36_backup/
    └── me
        └── A Test Board
            ├── 0_To Do
            │   ├── 0_Task3
            │   │   ├── attachments
            │   │   │   └── 0_chessboard.png
            │   │   ├── card.json
            │   │   └── description.md
            │   └── 1_Task4
            │       ├── card.json
            │       └── description.md
            ├── 1_In Progress
            │   └── 0_Task2
            │       ├── card.json
            │       └── description.md
            ├── 2_Done
            │   └── 0_Task1
            │       ├── attachments
            │       ├── card.json
            │       └── description.md
            └── A Test Board_full.json

- Lists and cards have their names prefixed by their position to keep
  the order
- For each card:
- The description is saved to a separate Markdown file
- The attachments are downloaded to a separate folder
- The rest stays in the json file


Run with Docker
---------------

The easiest way to execute the script with the default parameters (if you have Docker):

::

    docker run -t -e TRELLO_API_KEY=YOUR_KEY -e TRELLO_TOKEN=YOUR_TOKEN -v /backups:/app jtpio/trello-full-backup

This will create a new folder on your host system in the `backups` directory. Feel free to adjust it based on your host system (GNU/Linux, Mac OS, Windows...).

To pass different parameters, for example to avoid downloading attachments:

::

    docker run -t -e TRELLO_API_KEY=YOUR_KEY -e TRELLO_TOKEN=YOUR_TOKEN -v /backups:/app jtpio/trello-full-backup trello-full-backup -a 0


Install
-------

::

    pip install trello-full-backup


Usage
-----

Make sure the environment variables **TRELLO\_API\_KEY** and
**TRELLO\_TOKEN** are correctly set.

- To get the API key: https://trello.com/app-key
- To get the token: https://trello.com/1/authorize?scope=read&expiration=never&name=backup&key=REPLACE_WITH_YOUR_API_KEY&response_type=token

Then you can run the following commands:

::

    export TRELLO_API_KEY=yourapikey
    export TRELLO_TOKEN=yourtoken


And execute the script:

::

    trello-full-backup


By default the script creates a folder with the current date as a name.
Example: *2015-11-12\_18-57-56\_backup*

You can specify your own destination directory, but the script **does
not** create the intermediate directories in case they don't exist:

::

    trello-full-backup -d path/to/dir

Options
-------

::

    trello-full-backup -h

::

    usage: trello-full-backup [-h] [-d [DEST]] [-i] [-t] [-B] [-L] [-C] [-o]
                              [-a [ATTACHMENT_SIZE]]

    Trello Full Backup

    optional arguments:
      -h, --help            show this help message and exit
      -d [DEST]             Destination folder
      -i, --incremental     Backup in an already existing folder incrementally
      -t, --tokenize        Tokenize the names for folders and files. Useful for
                            scripts
      -B, --closed-boards   Backup closed board
      -L, --archived-lists  Backup archived lists
      -C, --archived-cards  Backup archived cards
      -o, --organizations   Backup organizations
      -a [ATTACHMENT_SIZE], --attachment-size [ATTACHMENT_SIZE]
                            Attachment size limit in bytes. Set to -1 to disable
                            the limit

Incremental mode
----------------
The incremental mode is useful for scripts. It will replace the names of the folders in each board by unique tokens.
Furthermore, it allows the user to specify the same directory for backup.
This will update all the json and description.md files. However it will download the attachment only if they have changed from the last backup.
