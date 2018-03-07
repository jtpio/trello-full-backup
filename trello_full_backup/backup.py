import argparse
import json
import logging
import os
import sys

import requests

from datetime import datetime

API = 'https://api.trello.com/1/'

# Do not download files over 100 MB by default
ATTACHMENT_BYTE_LIMIT = 100000000
ATTACHMENT_REQUEST_TIMEOUT = 30  # 30 seconds

# Read the API keys from the environment variables and build the authentication
API_KEY = os.getenv('TRELLO_API_KEY', '')
API_TOKEN = os.getenv('TRELLO_TOKEN', '')
AUTH = '?key={}&token={}'.format(API_KEY, API_TOKEN)


def _get_filter(archived=False):
    return 'all' if archived else 'open'


def _write_file(file_name, obj, dumps=True):
    with open(file_name, 'w', encoding='utf-8') as f:
        to_write = json.dumps(obj, indent=4, sort_keys=True) if dumps else obj
        f.write(to_write)


def _get_organization_boards(options):
    org_boards_data = {}
    my_boards_url = '{}members/me/boards{}'.format(API, AUTH)
    org_boards_data['me'] = requests.get(my_boards_url).json()

    orgs = []
    if options.organizations:
        org_url = '{}members/me/organizations{}'.format(API, AUTH)
        orgs = requests.get(org_url).json()

    for org in orgs:
        boards_url = '{}organizations/{}/boards{}'.format(API, org['id'], AUTH)
        org_boards_data[org['id']] = requests.get(boards_url).json()

    return org_boards_data


def _get_full_board(board_id, archived_lists, archived_cards):
    board_details = requests.get(''.join((
        '{}boards/{}{}&'.format(API, board_id, AUTH),
        'actions=all&actions_limit=1000&',
        'cards={}&'.format(_get_filter(archived_cards)),
        'card_attachments=true&',
        'labels=all&',
        'lists={}&'.format(_get_filter(archived_lists)),
        'members=all&',
        'member_fields=all&',
        'checklists=all&',
        'fields=all'
    ))).json()
    return board_details


def _mkdir(name):
    if not os.access(name, os.R_OK):
        os.mkdir(name)


def _get_attachments(board, options):
    for card in board['cards']:
        for attachment in card['attachments']:
            if attachment['bytes'] is None or attachment['bytes'] >= options.attachment_size:
                continue
            yield attachment['id'], attachment['url']


def _save_to_disk(options):

    def _log(message):
        if options.dry_run:
            message = 'DRY RUN: {}'.format(message)
        logging.info(message)

    now = datetime.today().strftime('%Y%m%d_%H%M%S')
    destination = options.destination or os.path.join(os.getcwd(), now)

    if not options.dry_run:
        _mkdir(destination)
    _log('Create folder {}'.format(destination))

    boards = _get_organization_boards(options)
    for organization, board_list in boards.items():
        organization_folder = os.path.join(destination, organization)

        if not options.dry_run:
            _mkdir(organization_folder)
        _log('Create folder {}'.format(organization_folder))

        _log('Saving organization {} to {}'.format(organization, organization_folder))
        for board in board_list:
            if board['closed'] and not options.closed_boards:
                continue

            full_board = _get_full_board(board['id'], options.archived_lists, options.archived_cards)

            # TODO: _get_attachments(full_board, options)

            board_file = os.path.join(destination, organization, '{}.json'.format(board['id']))
            if not options.dry_run:
                _write_file(board_file, full_board, dumps=True)
            _log('Saved board {} to {}'.format(board['name'], board_file))


def _parse_args():
    parser = argparse.ArgumentParser(description='Trello Full Backup')

    parser.add_argument('-d', '--destination-folder',
                        dest='destination',
                        nargs='?',
                        help='Destination folder')

    parser.add_argument('-B', '--closed-boards',
                        dest='closed_boards',
                        action='store_const',
                        default=0,
                        const=1,
                        help='Backup closed board')

    parser.add_argument('-L', '--archived-lists',
                        dest='archived_lists',
                        action='store_const',
                        default=0,
                        const=1,
                        help='Backup archived lists')

    parser.add_argument('-C', '--archived-cards',
                        dest='archived_cards',
                        action='store_const',
                        default=0,
                        const=1,
                        help='Backup archived cards')

    parser.add_argument('-o', '--organizations',
                        dest='organizations',
                        action='store_const',
                        default=False,
                        const=True,
                        help='Backup organizations')

    parser.add_argument('--dry-run',
                        dest='dry_run',
                        action='store_const',
                        default=False,
                        const=True,
                        help='Dry Run (do not write to disk)')

    parser.add_argument('-v', '--verbose',
                        dest='verbose',
                        action='store_const',
                        default=False,
                        const=True,
                        help='Verbose mode')

    parser.add_argument('-a', '--attachment-size',
                        dest='attachment_size',
                        nargs='?',
                        default=ATTACHMENT_BYTE_LIMIT,
                        type=int,
                        help='Attachment size limit in bytes. ' +
                             'Set to -1 to disable the limit')

    args = parser.parse_args()

    return args


def _setup_logger(options):
    level = logging.INFO if options.verbose else logging.ERROR
    logging.basicConfig(level=level, format='%(asctime)s - %(message)s')


def _validate_credentials():
    return len(API_KEY) > 0 and len(API_TOKEN) > 0


def cli():
    options = _parse_args()

    _setup_logger(options)

    if not _validate_credentials():
        logging.error('Please provide TRELLO_API_KEY and TRELLO_TOKEN as environment variables')
        return 1

    logging.info('Backup Started...')
    _save_to_disk(options)

    logging.info('Backup Complete!')
    return 0


if __name__ == '__main__':
    ret = cli()
    sys.exit(ret)
