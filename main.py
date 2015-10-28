#!/usr/bin/env python

import sys
import itertools
import os
import argparse
import re
import datetime
import requests
import json

# do not download files over 100 MB by default
ATTACHMENT_BYTE_LIMIT = 1e8
ATTACHMENT_REQUEST_TIMEOUT = 30 # seconds
FILE_NAME_MAX_LENGTH = 255
FILTERS = ['open', 'all']

def sanitize_file_name(name):
	return re.sub(r'[<>:\/\|\?\*]', '_', name)[-FILE_NAME_MAX_LENGTH:]

def write_file(file_name, obj, dumps=True):
	with open(file_name, 'w') as f:
		to_write = json.dumps(obj, indent=4) if dumps else obj
		f.write(to_write)

parser = argparse.ArgumentParser(description='Trello Full Backup Command Line Parameters')
parser.add_argument('-d', metavar='DEST', nargs='?', help='Destination folder')
parser.add_argument('-B', '--closed-boards', dest='closed_boards', action='store_const', default=0, const=1, help='Backup closed board')
parser.add_argument('-L', '--archived-lists', dest='archived_lists', action='store_const', default=0, const=1, help='Backup archived lists')
parser.add_argument('-C', '--archived-cards', dest='archived_cards', action='store_const', default=0, const=1, help='Backup archived cards')
args = parser.parse_args()

dest_dir = datetime.datetime.now().isoformat('_').replace(':', '-').split('.')[0] + '_backup'

if args.d:
	dest_dir = args.d

if os.access(dest_dir, os.R_OK):
	print('Folder', dest_dir, 'already exists')
	sys.exit(1)

os.mkdir(dest_dir)
os.chdir(dest_dir)

TRELLO_API = 'https://api.trello.com/1/'

# Read the API keys from the environment variables
TRELLO_API_KEY = os.getenv('TRELLO_API_KEY', '')
TRELLO_API_SECRET = os.getenv('TRELLO_API_SECRET', '')
TRELLO_TOKEN = os.getenv('TRELLO_TOKEN', '')

auth = '?key=' + TRELLO_API_KEY + '&token=' + TRELLO_TOKEN

boards_meta = requests.get(TRELLO_API + 'members/me/boards' + auth).json()
boards = [ b['id'] for b in boards_meta if not (args.closed_boards and b['closed']) ]

for board in boards_meta:
	board_details = requests.get(TRELLO_API + 'boards/' + board['id'] + auth + '&'+
		'actions=all&' +
		'actions_limit=1000&' +
		'cards=' + FILTERS[args.archived_cards] + '&' +
		'card_attachments=true&' +
		'lists=' + FILTERS[args.archived_lists] + '&' +
		'members=all&' +
		'member_fields=all&' +
		'checklists=all&' +
		'fields=all'
	).json()

	board_dir = sanitize_file_name(board_details['name'])

	os.mkdir(board_dir)

	# Enter board directory
	os.chdir(board_dir)

	file_name = board_dir + '_full.json'
	print('Saving full json for board', board_details['name'], 'with id', board['id'], 'to', file_name)
	write_file(file_name, board_details)

	lists = {}
	for list_id, cards in itertools.groupby(board_details['cards'], key=lambda x: x['idList']):
		lists[list_id] = sorted(list(cards), key=lambda card: card['pos'])

	for id_list, ls in enumerate(board_details['lists']):
		list_name = sanitize_file_name(str(id_list) + '_' + ls['name'])
		os.mkdir(list_name)

		# Enter list directory
		os.chdir(list_name)
		cards = lists[ls['id']] if ls['id'] in lists else []

		for id_card, c in enumerate(cards):
			card_name = sanitize_file_name(str(id_card) + '_' + c['name'])
			os.mkdir(card_name)

			# Enter card directory
			os.chdir(card_name)

			meta_file_name = 'card.json'
			description_file_name = 'description.md'

			print('Saving', card_name)
			print('Saving', meta_file_name, 'and', description_file_name)
			write_file(meta_file_name, c)
			write_file(description_file_name, c['desc'], dumps=False)

			# Only download attachments below the size limit
			attachments = [a for a in c['attachments'] if a['bytes'] != None and a['bytes'] < ATTACHMENT_BYTE_LIMIT]

			if len(attachments) > 0:
				# Enter attachments directory
				os.mkdir('attachments')
				os.chdir('attachments')

				# Download attachments
				for id_attachment, attachment in enumerate(attachments):
					attachment_name = sanitize_file_name(str(id_attachment) + '_' + attachment['name'])

					print('Saving attachment', attachment_name)
					attachment_content = requests.get(attachment['url'], stream=True, timeout=ATTACHMENT_REQUEST_TIMEOUT)
					with open(attachment_name, 'wb') as f:
						for chunk in attachment_content.iter_content(chunk_size=1024):
							if chunk:
								f.write(chunk)

				# Exit attachments directory
				os.chdir('..')

			# Exit card directory
			os.chdir('..')

		# Exit list directory
		os.chdir('..')

	# Exit sub directory
	os.chdir('..')

print('Trello Full Backup Completed!')