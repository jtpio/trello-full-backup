import sys
import itertools
import os
import argparse
import re
import datetime
import requests
import json

ATTACHMENT_BYTE_LIMIT = 50000000

def sanitize_file_name(name):
	return re.sub(r'[<>:\/\|\?\*]', '_', name)

def write_file(file_name, obj, dumps=True):
	with open(file_name, 'w') as f:
		to_write = json.dumps(obj, indent=4) if dumps else obj
		f.write(to_write)

parser = argparse.ArgumentParser(description='Trello Full Backup Command Line Parameters')
parser.add_argument('-d', metavar='DEST', nargs='?', help='Destination folder')
parser.add_argument('--skip-archived-boards', nargs='?', default=False, help='Destination folder')
args = parser.parse_args()

dest_dir = datetime.datetime.now().isoformat('_').replace(':', '_').split('.')[0]

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
boards = [b['id'] for b in boards_meta]

for board in boards_meta:
	board_details = requests.get(TRELLO_API + 'boards/' + board['id'] + auth + '&'+
		'actions=all&' +
		'actions_limit=1000&' +
		'cards=all&' +
		'card_attachments=true&' +
		'lists=all&' +
		'members=all&' +
		'member_fields=all&' +
		'checklists=all&' +
		'fields=all'
	).json()

	board_dir = sanitize_file_name(board_details['name'])

	# Make and enter sub directory
	os.mkdir(board_dir)
	os.chdir(board_dir)

	file_name = board_dir + '_full.json'
	print('Saving full json for board', board_details['name'], 'with id', board['id'], 'to', file_name)
	write_file(file_name, board_details)

	lists = {}
	for list_id, cards in itertools.groupby(board_details['cards'], key=lambda x: x['idList']):
		lists[list_id] = list(cards)

	for ls in board_details['lists']:
		list_name = str(ls['pos']) + '_' + ls['name']
		os.mkdir(list_name)
		os.chdir(list_name)
		cards = lists[ls['id']]
		for c in cards:
			card_name = str(c['pos']) + '_' + c['name']
			os.mkdir(card_name)
			os.chdir(card_name)
			meta_file_name = 'card.json'
			description_file_name = 'description.md'
			write_file(meta_file_name, c)
			write_file(description_file_name, c['desc'], dumps=False)

			# Download attachments
			os.mkdir('attachments')
			os.chdir('attachments')
			attachments = [a for a in c['attachments'] if a['bytes'] < ATTACHMENT_BYTE_LIMIT]
			for attachment in attachments:
				attachment_name = attachment['id'] + '_' + attachment['name']
				print('Saving attachment', attachment_name)
				attachment_content = requests.get(attachment['url'], stream=True)
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

	break

print('Trello Full Backup Completed!')