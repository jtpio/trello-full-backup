# Trello Full Backup

**Python 3** script to backup everything from Trello.

The script does a backup of:
- boards, open and closed, as json files
- lists, open and archived, as json files
- cards, open and archived, as json files
- attachments, downloaded as raw files

The script also creates a **folder tree structure** corresponding to the way data is organized. This is to make it more convenient to navigate locally between folders, as it mimics the flow you have when using the web and mobile apps.

Here is an example of what the tree structure looks like:

```
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
```

- Lists and cards have their names prefixed by their position to keep the order
- For each card:
 - The description is saved to a separate Markdown file
 - The attachments are downloaded to a separate folder
 - The rest stays in the json file

## Usage

Make sure the environment variables **TRELLO_API_KEY** and **TRELLO_TOKEN** are correctly set.
- To get the API key: [https://trello.com/app-key](https://trello.com/app-key)
- To get the token: [https://trello.com/1/authorize?scope=read&expiration=never&name=backup&key=REPLACE_WITH_YOUR_API_KEY&response_type=token](https://trello.com/1/authorize?scope=read&expiration=never&name=backup&key=REPLACE_WITH_YOUR_API_KEY&response_type=token)


Then you can run the following commands:
```
export TRELLO_API_KEY=yourapikey
export TRELLO_TOKEN=yourtoken
```

Install requests if you don't have it:

```
pip install requests
```

Run:

```
python main.py

```

or make the program executable: ```chmod +x main.py```, and run:

```
./main.py
```

By default the script creates a folder with the current date as a name. Example: *2015-11-12_18-57-56_backup*

You can specify your own destination directory, but the script **does not** create the intermediate directories in case they don't exist:

```
./main.py -d path/to/dir
```

## Options

```
./main.py -h
```

```
usage: main.py [-h] [-d [DEST]] [-B] [-L] [-C] [-o] [-a ATTACHMENT_SIZE]

Trello Full Backup

optional arguments:
  -h, --help            show this help message and exit
  -d [DEST]             Destination folder
  -B, --closed-boards   Backup closed board
  -L, --archived-lists  Backup archived lists
  -C, --archived-cards  Backup archived cards
  -o, --organizations   Backup organizations
  -a ATTACHMENT_SIZE, --attachment-size ATTACHMENT_SIZE
                        Attachment size limit in bytes. Set to -1 to disable
                        the limit
```
