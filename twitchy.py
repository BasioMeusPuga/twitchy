#!/usr/bin/python

import requests
import json
import sqlite3
import sys
import argparse

from multiprocessing.dummy import Pool as ThreadPool 
from os.path import expanduser, exists
from os import system

database_path = str(expanduser("~") + '/.twitchy.db')
if not exists(database_path):
	print (" First run. Creating db and exiting")
	database = sqlite3.connect(database_path)
	database.execute("CREATE TABLE channels (id INTEGER PRIMARY KEY, Name TEXT, TimeWatched INTEGER, AltName TEXT)")
	database.execute("CREATE TABLE games (id INTEGER PRIMARY KEY, Name TEXT, AltName TEXT)")
	database.close()
	exit()
database = sqlite3.connect(database_path)
dbase = database.cursor()

class colors:
	GAMECYAN = '\033[96m'
	NUMBERYELLOW = '\033[93m'
	ONLINEGREEN = '\033[92m'
	OFFLINERED = '\033[91m'
	TEXTWHITE = '\033[97m'
	ENDC = '\033[0m'
    
# Functions
## Display template mapping for extra spicy output
def template_mapping(display_number, called_from):
	global template
	first_column = 25
	third_column = 25
	
	if called_from == "list":
		second_column = 40
	elif called_from == "listnocolor":
		second_column = 31
	elif called_from == "watch":
		second_column = 20
		third_column = 100

	template = "{0:%s}{1:%s}{2:%s}" % (first_column, second_column, third_column)
	if display_number >= 10:
		template = "{0:%s}{1:%s}{2:%s}" % (first_column - 1, second_column, third_column)		
	elif display_number >= 100:
		template = "{0:%s}{1:%s}{2:%s}" % (first_column - 2, second_column, third_column)

## Add to database. Call with "-a" or "-s". Haha I said ass.
def add_to_database(channel_input):
	final_addition_streams = []

	def final_addition (final_addition_input):
		something_added = False
		print (" " + colors.NUMBERYELLOW + "Additions to database:" + colors.ENDC)
		for channel_name in final_addition_input:
			does_it_exist = dbase.execute("SELECT Name FROM channels WHERE Name = '%s'" % channel_name).fetchone()
			if str(does_it_exist) == "None":
				something_added = True
				database.execute("INSERT INTO channels (Name,TimeWatched) VALUES ('%s',0)" % channel_name)
				print(" " + channel_name)
		database.commit()
		if something_added == False:
			print (" " + colors.OFFLINERED + "None" + colors.ENDC)

	if sys.argv[1] == "-s":
		username = channel_input[0]
		r = requests.get('https://api.twitch.tv/kraken/users/%s/follows/channels' % username)
		stream_data = json.loads(r.text)
		
		try:
			total_followed = stream_data['_total']
			r = requests.get('https://api.twitch.tv/kraken/users/%s/follows/channels?limit=%s' % (username, str(total_followed)))
			stream_data = json.loads(r.text)
			sync_run_once = True
			for i in range(0,total_followed):
				final_addition_streams.append(stream_data['follows'][i]['channel']['name'].lower())
			final_addition(final_addition_streams)
		except:
			print(" " + username + " doesn't exist")

	if sys.argv[1] == "-a":
		for names_for_addition in channel_input:
			r = requests.get('https://api.twitch.tv/kraken/streams/' + names_for_addition)
			stream_data = json.loads(r.text)
			try:
				stream_data['error']
				print(" " + names_for_addition + " doesn't exist")
			except:
				final_addition_streams.append(names_for_addition)
		final_addition(final_addition_streams)

	database.close()
	exit()

## Brilliantly named function. Call with "-d", "-an" or "-n"
def read_modify_deletefrom_database(channel_input):
	if channel_input == "BlankForAllIntensivePurposes":
		relevant_list = dbase.execute('SELECT Name, TimeWatched, AltName FROM channels').fetchall()
	else:
		relevant_list = dbase.execute("SELECT Name, TimeWatched, AltName FROM channels WHERE Name LIKE ?", ('%'+channel_input+'%',)).fetchall()
	relevant_list.sort()

	display_number = 1
	for i in relevant_list:
		if str(i[2]) != "None":
			template_mapping(display_number, "list")
			print (" " + colors.NUMBERYELLOW + str(display_number) +  colors.ENDC + " " + template.format(i[0],  colors.GAMECYAN + str(i[2]) + colors.ENDC, str(i[1])))
		else:
			template_mapping(display_number, "listnocolor")
			if i[1] == 0:
				print (" " + colors.NUMBERYELLOW + str(display_number) + colors.OFFLINERED + " " + template.format(i[0], str(i[2]), str(i[1])))
			else:
				print (" " + colors.NUMBERYELLOW + str(display_number) + colors.ENDC + " " + template.format(i[0], str(i[2]), str(i[1])))
		display_number = display_number + 1

	if sys.argv[1] == "-d":
		try:
			stream_select = input(" Channel number(s)? ")
			print (" " + colors.NUMBERYELLOW + "Deleted from database:" + colors.ENDC)
			mynums = [int(i) for i in stream_select.split()]
			for j in mynums:
				print (" " + relevant_list[j -1][0])
				database.execute("DELETE FROM channels WHERE Name = '%s'" % relevant_list[j -1][0])
			database.commit()
		except IndexError:
			print (" You high, bro?")

	elif sys.argv[1] == "-an":
		print ("In Progress...")

	database.close()	 
	exit()

## Livestreamer called here with "-w", "-c" or our carefully chosen input string
def watch(channel_input):
	database.row_factory = lambda cursor, row: row[0]
	dbase = database.cursor()

	print (" " + colors.NUMBERYELLOW + "Checking channels..." + colors.ENDC)
	if channel_input == "BlankForAllIntensivePurposes":
		status_check_required = dbase.execute('SELECT name FROM channels').fetchall()
	elif sys.argv[1] == "-c":
		status_check_required = dbase.execute("SELECT name FROM channels WHERE name LIKE ?", ('%'+channel_input+'%',)).fetchall()
	else:
		status_check_required = channel_input
	
	database.close()
	stream_status = []
	def get_status(channel_name):
		r = requests.get('https://api.twitch.tv/kraken/streams/' + channel_name)
		stream_data = json.loads(r.text)

		try:
			stream_data['error']
		except:
			if str(stream_data['stream']) != "None":
				stream_status.append([stream_data['stream']['channel']['name'], str(stream_data['stream']['channel']['game']), str(stream_data['stream']['channel']['status']), stream_data['stream']['viewers'], stream_data['stream']['channel']['partner']])
		"""Dictionary Scheme
		List0: Display name
		List1: Game Name
		List2: Stream Status
		List3: Viewers
		List4: Partner Status"""

	pool = ThreadPool(30)
	results = pool.map(get_status, status_check_required)
	pool.close()
	pool.join()

	if len(stream_status) > 0:
		stream_status = sorted(stream_status, key=lambda x: (x[1], -x[3]))
	else:
		print (" All channels offline")
		exit()

	stream_final = []
	games_shown = []
	display_number = 1

	for i in stream_status:
		if i[1] not in games_shown:
			print (" " + colors.GAMECYAN + i[1] + colors.ENDC)
			games_shown.append(i[1])
		
		stream_final.insert(display_number - 1, i[0])
		template_mapping(display_number, "watch")
		print (" " + colors.NUMBERYELLOW + (str(display_number) + colors.ENDC) + " " + (colors.ONLINEGREEN + template.format(i[0], str(i[3]), i[2]) + colors.ENDC))
		display_number = display_number + 1

	try:
		stream_select = int(input(" Channel number? "))
		final_selection = stream_final[stream_select - 1]
		print (" Now watching " + final_selection)
		system('livestreamer twitch.tv/' + final_selection + ' high --player mpv --hls-segment-threads 3')
	except IndexError:
		print (" Seriously, bro, you high?")

# Parse CLI input
def main():
	parser = argparse.ArgumentParser(description='Watch twitch.tv from your terminal. IT\'S THE FUTURE.', add_help = False)
	parser.add_argument('-h', '--help', help='This helpful message', action='help')
	parser.add_argument('-a', type=str, nargs='+', help='Add channel name(s) to database', metavar = "", required=False)
	parser.add_argument('-an', type=str, nargs = '?', const = 'BlankForAllIntensivePurposes', help='Set/Unset alternate names', required=False)
	parser.add_argument('-d', type=str, nargs = '?', const = 'BlankForAllIntensivePurposes', help='Delete channel(s) from database', required=False)
	parser.add_argument('-c', type=str, help='Search string in database', metavar = "", required=False)
	parser.add_argument('-s', type=str, nargs = 1, help='Sync username\'s followed accounts to local database', metavar = "username", required=False)
	parser.add_argument('-w', type=str, nargs='+', help='Watch specified channel(s)', metavar = "", required=False)
	args = parser.parse_args()

	if args.a:
		add_to_database(args.a)
	elif args.an:
		read_modify_deletefrom_database(args.an)
	elif args.c:
		watch(args.c)
	elif args.d:
		read_modify_deletefrom_database(args.d)
	elif args.s:
		add_to_database(args.s)
	elif args.w:
		watch(args.w)
	else:
		watch("BlankForAllIntensivePurposes")

try: 
	main()
except KeyboardInterrupt:
	database.close()
	exit()