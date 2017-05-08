import sys
import itertools
import os
import argparse
import re
import datetime
import requests
import json

# Do not download files over 100 MB by default
ATTACHMENT_BYTE_LIMIT = 100000000
ATTACHMENT_REQUEST_TIMEOUT = 30  # 30 seconds
FILE_NAME_MAX_LENGTH = 100
FILTERS = ['open', 'all']

API = 'https://api.trello.com/1/'

# Read the API keys from the environment variables
API_KEY = os.getenv('TRELLO_API_KEY', '')
API_TOKEN = os.getenv('TRELLO_TOKEN', '')

auth = '?key={}&token={}'.format(API_KEY, API_TOKEN)


def mkdir(name):
    if not os.access(name, os.R_OK):
        os.mkdir(name)

def get_extension(filename):
    return os.path.splitext(filename)[1]

def sanitize_file_name(name):
    ''' Stip problematic characters for a file name '''
    return re.sub(r'[<>:\/\|\?\*\']', '_', name)[:FILE_NAME_MAX_LENGTH]


def write_file(file_name, obj, dumps=True):
    ''' Write <obj> to the file <file_name> '''
    with open(file_name, 'w', encoding='utf-8') as f:
        to_write = json.dumps(obj, indent=4, sort_keys=True) if dumps else obj
        f.write(to_write)


def filter_boards(boards, closed):
    ''' Return a list of the boards to retrieve (closed or not) '''
    return [b for b in boards if not b['closed'] or closed]


def download_attachments(c, max_size, backup=False):
    ''' Download the attachments for the card <c> '''
    # Only download attachments below the size limit
    attachments = [a for a in c['attachments']
                   if a['bytes'] is not None and
                   (a['bytes'] < max_size or max_size == -1)]

    if len(attachments) > 0:
        # Enter attachments directory
        mkdir('attachments')
        os.chdir('attachments')

        # Download attachments
        for id_attachment, attachment in enumerate(attachments):
            attachment_name = '{}_{}'.format(id_attachment, attachment['name'])
            attachment_name = sanitize_file_name(attachment_name)

            if backup:
                extension = get_extension(attachment_name)
                attachment_name=attachment['id'] + "_" + str(attachment['bytes']) + extension

            if not os.path.isfile(attachment_name):
                print('Saving attachment', attachment_name)
                try:
                    content = requests.get(attachment['url'],
                                           stream=True,
                                           timeout=ATTACHMENT_REQUEST_TIMEOUT)
                except Exception:
                    sys.stderr.write('Failed download: {}'.format(attachment_name))
                    continue

                with open(attachment_name, 'wb') as f:
                    for chunk in content.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
            else:
                print('Attachment', attachment_name, 'exists already.')

        # Exit attachments directory
        os.chdir('..')


def backup_card(id_card, c, attachment_size, backup=False):
    ''' Backup the card <c> with id <id_card> '''

    card_name = sanitize_file_name('{}_{}'.format(id_card, c['name']))
    if backup:
        card_name = c['shortLink']

    mkdir(card_name)

    # Enter card directory
    os.chdir(card_name)

    meta_file_name = 'card.json'
    description_file_name = 'description.md'

    print('Saving', card_name)
    print('Saving', meta_file_name, 'and', description_file_name)
    write_file(meta_file_name, c)
    write_file(description_file_name, c['desc'], dumps=False)

    download_attachments(c, attachment_size, backup)

    # Exit card directory
    os.chdir('..')


def backup_board(board, args):
    ''' Backup the board '''
    board_details = requests.get(''.join((
        '{}boards/{}{}&'.format(API, board["id"], auth),
        'actions=all&actions_limit=1000&',
        'cards={}&'.format(FILTERS[args.archived_cards]),
        'card_attachments=true&',
        'labels=all&',
        'lists={}&'.format(FILTERS[args.archived_lists]),
        'members=all&',
        'member_fields=all&',
        'checklists=all&',
        'fields=all'
    ))).json()

    board_dir = sanitize_file_name(board_details['name'])

    mkdir(board_dir)

    # Enter board directory
    os.chdir(board_dir)

    file_name = '{}_full.json'.format(board_dir)
    print('Saving full json for board',
          board_details['name'], 'with id', board['id'], 'to', file_name)
    write_file(file_name, board_details)

    lists = {}
    cs = itertools.groupby(board_details['cards'], key=lambda x: x['idList'])
    for list_id, cards in cs:
        lists[list_id] = sorted(list(cards), key=lambda card: card['pos'])

    for id_list, ls in enumerate(board_details['lists']):
        if bool(args.backup):
            list_name = ls["id"]
        else:
            list_name = sanitize_file_name('{}_{}'.format(id_list, ls['name']))

        mkdir(list_name)

        # Enter list directory
        os.chdir(list_name)
        cards = lists[ls['id']] if ls['id'] in lists else []

        for id_card, c in enumerate(cards):
            backup_card(id_card, c, args.attachment_size, bool(args.backup))

        # Exit list directory
        os.chdir('..')

    # Exit sub directory
    os.chdir('..')


def cli():

    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Trello Full Backup'
    )

    # The destination folder to save the backup to
    parser.add_argument('-d',
                        metavar='DEST',
                        nargs='?',
                        help='Destination folder')

    # Backup mode. Replace folder names by tokens and
    # don't download the already existing attachments
    parser.add_argument('-b', '--backup',
                        dest='backup',
                        action='store_const',
                        default=False,
                        const=True,
                        help='Backup mode: Change names for tokens and only upload new attachments')

    # Backup the boards that are closed
    parser.add_argument('-B', '--closed-boards',
                        dest='closed_boards',
                        action='store_const',
                        default=0,
                        const=1,
                        help='Backup closed board')

    # Backup the lists that are archived
    parser.add_argument('-L', '--archived-lists',
                        dest='archived_lists',
                        action='store_const',
                        default=0,
                        const=1,
                        help='Backup archived lists')

    # Backup the cards that are archived
    parser.add_argument('-C', '--archived-cards',
                        dest='archived_cards',
                        action='store_const',
                        default=0,
                        const=1,
                        help='Backup archived cards')

    # Backup the cards that are archived
    parser.add_argument('-o', '--organizations',
                        dest='orgs',
                        action='store_const',
                        default=False,
                        const=True,
                        help='Backup organizations')

    # Set the size limit for the attachments
    parser.add_argument('-a', '--attachment-size',
                        dest='attachment_size',
                        nargs='?',
                        default=ATTACHMENT_BYTE_LIMIT,
                        type=int,
                        help='Attachment size limit in bytes. ' +
                        'Set to -1 to disable the limit')

    args = parser.parse_args()

    dest_dir = datetime.datetime.now().isoformat('_')
    dest_dir = '{}_backup'.format(dest_dir.replace(':', '-').split('.')[0])

    if args.d:
        dest_dir = args.d

    if os.access(dest_dir, os.R_OK):
        if not bool(args.backup):
            print('Folder', dest_dir, 'already exists')
            sys.exit(1)

    mkdir(dest_dir)

    os.chdir(dest_dir)

    print('==== Backup initiated')
    print('Backing up to:', dest_dir)
    print('Backup mode:', bool(args.backup))
    print('Backup closed board:', bool(args.closed_boards))
    print('Backup archived lists:', bool(args.archived_lists))
    print('Backup archived cards:', bool(args.archived_cards))
    print('Attachment size limit (bytes):', args.attachment_size)
    print('==== ')
    print()

    org_boards_data = {}

    my_boards_url = '{}members/me/boards{}'.format(API, auth)
    org_boards_data['me'] = requests.get(my_boards_url).json()

    orgs = []
    if args.orgs:
        org_url = '{}members/me/organizations{}'.format(API, auth)
        orgs = requests.get(org_url).json()

    for org in orgs:
        boards_url = '{}organizations/{}/boards{}'.format(API, org['id'], auth)
        org_boards_data[org['name']] = requests.get(boards_url).json()

    for org, boards in org_boards_data.items():
        mkdir(org)
        os.chdir(org)
        boards = filter_boards(boards, args.closed_boards)
        for board in boards:
            backup_board(board, args)
        os.chdir('..')

    print('Trello Full Backup Completed!')


if __name__ == '__main__':
    cli()
