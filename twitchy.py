#!/usr/bin/python3
# Requires: python3, livestreamer, requests
# rev = 51


import sys
import json
import shlex
import atexit
import select
import locale
import sqlite3
import requests
import argparse
import webbrowser
import subprocess

from time import time, sleep, strftime
from shutil import which, get_terminal_size
from random import randrange
from ast import literal_eval
from os import remove
from os.path import expanduser, exists, realpath, dirname


# Color code declaration
class Colors:
	CYAN = '\033[96m'
	YELLOW = '\033[93m'
	GREEN = '\033[92m'
	RED = '\033[91m'
	WHITE = '\033[97m'
	ENDC = '\033[0m'


# Options
def configure_options(special_occasion):
	try:
		print(Colors.CYAN + ' Configure:' + Colors.ENDC)
		player = input(' Media player [mpv]: ')
		if which(player) is None:
			if which('mpv') is not None:
				player = 'mpv'
			else:
				print(Colors.RED + ' ' + player + Colors.ENDC + ' is not in $PATH. Please check if this is what you want.')
				raise

		mpv_hardware_acceleration = False
		if player == 'mpv' and sys.platform == 'linux':
			mpv_option = input(' Use hardware acceleration (vaapi) with mpv [y/N]: ')
			if mpv_option == 'yes' or mpv_option == 'Y' or mpv_option == 'y':
				mpv_hardware_acceleration = True

		default_quality = input(' Default stream quality [low/medium/HIGH/source]: ')
		if default_quality == '' or (default_quality != 'low' and default_quality != 'medium' and default_quality != 'source'):
			default_quality = 'high'

		truncate_status_at = input(' Truncate stream status at [AUTO]: ')
		if truncate_status_at == '':
			truncate_status_at = 'Auto'
		else:
			truncate_status_at = int(truncate_status_at)

		""" The number of favorites displayed no longer includes offline channels.
		i.e. setting this value to n will display - in descending order of time watched,
		the first n ONLINE channels in the database """
		number_of_faves_displayed = input(' Number of favorites to display [5]: ')
		if number_of_faves_displayed == '':
			number_of_faves_displayed = 5
		else:
			number_of_faves_displayed = int(number_of_faves_displayed)

		chat_for_MT = input(' Display chat for multiple Twitch streams [y/N]: ')
		if chat_for_MT == '' or chat_for_MT == 'N' or chat_for_MT == 'n' or chat_for_MT == 'no':
			display_chat_for_multiple_twitch_streams = False
		else:
			display_chat_for_multiple_twitch_streams = True

		check_int = input(' Interval (seconds) in between channel status checks [60]: ')
		if check_int == '':
			check_interval = 60
		else:
			check_interval = int(check_int)

		print('\n' + Colors.CYAN + ' Current Settings:' + Colors.ENDC)
		penultimate_check = """ Media Player: {0}
 Default Quality: {1}
 Truncate status at: {2}
 Number of faves: {3}
 Display chat for multiple streams: {4}
 Check interval: {5}""".format(Colors.YELLOW + player + Colors.ENDC, Colors.YELLOW + default_quality + Colors.ENDC, Colors.YELLOW + str(truncate_status_at) + Colors.ENDC, Colors.YELLOW + str(number_of_faves_displayed) + Colors.ENDC, Colors.YELLOW + str(display_chat_for_multiple_twitch_streams) + Colors.ENDC, Colors.YELLOW + str(check_interval) + Colors.ENDC)

		print(penultimate_check)

		do_we_like = input(' Does this look correct to you? [Y/n]: ')
		if do_we_like == 'Y' or do_we_like == 'yes' or do_we_like == 'y' or do_we_like == '':
			options_to_insert = [['player', player], ['mpv_hardware_acceleration', mpv_hardware_acceleration], ['default_quality', default_quality], ['truncate_status_at', truncate_status_at], ['number_of_faves_displayed', number_of_faves_displayed], ['display_chat_for_multiple_twitch_streams', display_chat_for_multiple_twitch_streams], ['check_interval', check_interval]]

			database = sqlite3.connect(database_path)
			if special_occasion == 'FirstRun':
				database.execute("CREATE TABLE channels (id INTEGER PRIMARY KEY, Name TEXT, TimeWatched INTEGER, AltName TEXT)")
				database.execute("CREATE TABLE games (id INTEGER PRIMARY KEY, Name TEXT, TimeWatched INTEGER, AltName TEXT)")
				database.execute("CREATE TABLE miscellaneous (id INTEGER PRIMARY KEY, Name TEXT, Value TEXT)")
				database.execute("CREATE TABLE options (id INTEGER PRIMARY KEY, Name TEXT, Value TEXT)")

			elif special_occasion == 'TheDudeAbides':
				database.execute("DELETE FROM options")

			for i in options_to_insert:
				database.execute("INSERT INTO options (Name,Value) VALUES ('{0}','{1}')".format(i[0], str(i[1])))
			database.commit()
		else:
			raise
	except:
		final_decision = input(Colors.RED + ' Do you wish to restart? [y/N]: ' + Colors.ENDC)
		if final_decision == 'Y' or final_decision == 'yes' or final_decision == 'y':
			print()
			configure_options(special_occasion)
		else:
			exit()


# Stuff that isn't options. Or optional. Lel.
""" Check for requirements """
if which('livestreamer') is None:
	print(Colors.RED + ' livestreamer ' + Colors.ENDC + 'is not installed. FeelsBadMan.')
	exit()

""" Existential doubts go here """
database_path = expanduser('~') + '/.twitchy.db'
if not exists(database_path):
	print(Colors.CYAN + ' First run. Creating db and running configure.' + Colors.ENDC)
	configure_options('FirstRun')
	exit()
database = sqlite3.connect(database_path)

""" Set locale for comma placement """
locale.setlocale(locale.LC_ALL, '')


# The classy choice
class Options:
	try:
		options_from_database = database.execute("SELECT Value FROM options").fetchall()
		""" Database options scheme:
		0: player
		1: mpv_hardware_acceleration
		2: default_quality
		3: truncate_status_at
		4: number_of_faves_displayed
		5: display_chat_for_multiple_twitch_streams
		6: check_interval """

		player = options_from_database[0][0]
		mpv_hardware_acceleration = literal_eval(options_from_database[1][0])
		if player == 'mpv' and mpv_hardware_acceleration is True:
			player_final = 'mpv --hwdec=vaapi --vo=vaapi --cache 8192'
		else:
			player_final = 'mpv --cache 8192'

		default_quality = options_from_database[2][0]
		truncate_status_at = options_from_database[3][0]
		number_of_faves_displayed = int(options_from_database[4][0])
		display_chat_for_multiple_twitch_streams = literal_eval(options_from_database[5][0])
		check_interval = int(options_from_database[6][0])

		""" Run time option """
		conky_run = False
	except:
		print(Colors.RED + ' Error getting options. Running --configure:' + Colors.ENDC)
		configure_options('TheDudeAbides')
		exit()


# Fondle the Twitch API gently
def api_request(url):
	http_header = {'Client-ID': 'guulhcvqo9djhuyhb2vi56wqnglc351'}
	try:
		r = requests.get(url, headers=http_header)
		stream_data = json.loads(r.text)
		return stream_data
	except requests.exceptions.ConnectionError:
		print(Colors.RED + ' Unable to connect to Twitch.' + Colors.ENDC)
		exit()


# Display template mapping for extra spicy output
def template_mapping(called_from):

	third_column = 20
	""" Preceding specification is mostly pointless as long as it's non zero """

	if called_from == 'list':
		first_column = 25
		second_column = 40
	elif called_from == 'listnocolor':
		first_column = 25
		second_column = 31
	elif called_from == 'gameslist':
		first_column = 50
		second_column = 55
	elif called_from == 'gameslistnocolor':
		first_column = 50
		second_column = 46
	elif called_from == 'watch':
		first_column = 25
		second_column = 15
		third_column = 100
	elif called_from == 'vods':
		first_column = 40
		second_column = 60

	template = '{0:%s}{1:%s}{2:%s}' % (first_column, second_column, third_column)
	return template


# Convert time in seconds to a more human readable format. This doesn't mean you're human.
def time_convert(seconds):
	seconds = int(seconds)
	m, s = divmod(seconds, 60)
	h, m = divmod(m, 60)
	d, h = divmod(h, 24)

	if d > 0:
		time_converted = '%dd %dh %dm' % (d, h, m)
	elif h > 0:
		time_converted = '%dh %dm' % (h, m)
	elif m > 0:
		time_converted = '%dm' % m
	else:
		time_converted = '%ds' % s

	return time_converted


# Emotes - Kappa? Kappa.
def emote():
	kappa = (
		' ░░░░░░░░░░░░░░░░░░░░\n'
		' ░░░░▄▀▀▀▀▀█▀▄▄▄▄░░░░\n'
		' ░░▄▀▒▓▒▓▓▒▓▒▒▓▒▓▀▄░░\n'
		' ▄▀▒▒▓▒▓▒▒▓▒▓▒▓▓▒▒▓█░\n'
		' █▓▒▓▒▓▒▓▓▓░░░░░░▓▓█░\n'
		' █▓▓▓▓▓▒▓▒░░░░░░░░▓█░\n'
		' ▓▓▓▓▓▒░░░░░░░░░░░░█░\n'
		' ▓▓▓▓░░░░▄▄▄▄░░░▄█▄▀░\n'
		' ░▀▄▓░░▒▀▓▓▒▒░░█▓▒▒░░\n'
		' ▀▄░░░░░░░░░░░░▀▄▒▒█░\n'
		' ░▀░▀░░░░░▒▒▀▄▄▒▀▒▒█░\n'
		' ░░▀░░░░░░▒▄▄▒▄▄▄▒▒█░\n'
		' ░░░▀▄▄▒▒░░░░▀▀▒▒▄▀░░\n'
		' ░░░░░▀█▄▒▒░░░░▒▄▀░░░\n'
		' ░░░░░░░░▀▀█▄▄▄▄▀░░░░\n')

	print('\n' + kappa)


# Add to database. Call with '-a' or '-s'
def add_to_database(channel_input, argument):
	final_addition_streams = []

	def final_addition(final_addition_input):
		something_added = False
		print(' ' + Colors.YELLOW + 'Additions to database:' + Colors.ENDC)
		for channel_name in final_addition_input:
			does_it_exist = database.execute("SELECT Name FROM channels WHERE Name = '%s'" % channel_name.lower()).fetchone()
			if does_it_exist is None:
				something_added = True
				database.execute("INSERT INTO channels (Name,TimeWatched) VALUES ('%s',0)" % channel_name.lower())
				print(" " + channel_name)
		database.commit()
		if something_added is False:
			print(' ' + Colors.RED + 'None' + Colors.ENDC)

	if argument == 's':
		username = channel_input[0]

		stream_data = api_request('https://api.twitch.tv/kraken/users/%s/follows/channels' % username)

		try:
			total_followed = stream_data['_total']
			stream_data = api_request('https://api.twitch.tv/kraken/users/%s/follows/channels?limit=%s' % (username, str(total_followed)))
			for i in range(0, total_followed):
				final_addition_streams.append(stream_data['follows'][i]['channel']['name'].lower())
			final_addition(final_addition_streams)
		except:
			print(' ' + username + ' doesn\'t exist')

	if argument == 'a':
		for names_for_addition in channel_input:
			stream_data = api_request('https://api.twitch.tv/kraken/streams/' + names_for_addition)

			try:
				stream_data['error']
				print(' ' + names_for_addition + ' doesn\'t exist')
			except:
				final_addition_streams.append(names_for_addition)
		final_addition(final_addition_streams)


# Obscurely named function. Call with '-d', '-an' or '-n'
def read_modify_deletefrom_database(channel_input, whatireallywant_ireallyreallywant, argument):
	if whatireallywant_ireallyreallywant == 'ItsHammerTime':
		table_wanted = 'channels'
	else:
		table_wanted = input(' Modify (s)treamer or (g)ame name? ')
		if table_wanted == 's':
			table_wanted = 'channels'
		elif table_wanted == 'g':
			table_wanted = 'games'
		else:
			exit()

	if channel_input == 'BlankForAllIntensivePurposes':
		relevant_list = database.execute("SELECT Name, TimeWatched, AltName FROM %s" % table_wanted).fetchall()
	else:
		relevant_list = database.execute("SELECT Name, TimeWatched, AltName FROM '{0}' WHERE Name LIKE '{1}'".format(table_wanted, ('%' + channel_input + '%'))).fetchall()

	if len(relevant_list) == 0:
		print(Colors.RED + ' Database query returned nothing.' + Colors.ENDC)
		exit()

	relevant_list.sort()
	""" List Scheme of Tuples
	0: Name
	1: TimeWatched
	2: AltName """

	display_number = 1
	total_streams_digits = len(str(len(relevant_list)))
	for i in relevant_list:
		if i[2] is not None:
			if table_wanted == 'channels':
				template = template_mapping('list')
			elif table_wanted == 'games':
				template = template_mapping('gameslist')

			if i[1] == 0:
				print(' ' + Colors.YELLOW + str(display_number).rjust(total_streams_digits) + Colors.ENDC + ' ' + template.format(i[0], Colors.CYAN + str(i[2]) + Colors.RED, '  Unwatched' + Colors.ENDC))
			else:
				time_watched = time_convert(i[1]).rjust(11)
				print(' ' + Colors.YELLOW + str(display_number).rjust(total_streams_digits) + Colors.ENDC + ' ' + template.format(i[0], Colors.CYAN + str(i[2]) + Colors.ENDC, time_watched))
		else:
			if table_wanted == 'channels':
				template = template_mapping('listnocolor')
			elif table_wanted == 'games':
				template = template_mapping('gameslistnocolor')

			if i[1] == 0:
				print(' ' + Colors.YELLOW + str(display_number).rjust(total_streams_digits) + Colors.RED + ' ' + template.format(i[0], str(i[2]), '  Unwatched') + Colors.ENDC)
			else:
				time_watched = time_convert(i[1]).rjust(11)
				print(' ' + Colors.YELLOW + str(display_number).rjust(total_streams_digits) + Colors.ENDC + ' ' + template.format(i[0], str(i[2]), time_watched))
		display_number += 1

	final_selection = input(' Stream / Channel number(s)? ')

	if argument == 'd':
		try:
			print(' ' + Colors.YELLOW + 'Deleted from database:' + Colors.ENDC)
			entered_numbers = [int(i) for i in final_selection.split()]
			for j in entered_numbers:
				print(' ' + relevant_list[j - 1][0])
				database.execute("DELETE FROM '{0}' WHERE Name = '{1}'".format(table_wanted, relevant_list[j - 1][0]))
			database.commit()
		except IndexError:
			print(Colors.RED + ' How can columns be real if our databases aren\'t real?' + Colors.ENDC)

	if argument == 'an':
		try:
			old_name = relevant_list[int(final_selection) - 1][0]
			new_name = input(' Replace ' + old_name + ' with? ')

			if new_name == '':
				database.execute("UPDATE '{0}' SET AltName = NULL WHERE Name = '{1}'".format(table_wanted, old_name))
			else:
				database.execute("UPDATE '{0}' SET AltName = '{1}' WHERE Name = '{2}'".format(table_wanted, new_name, old_name))
			database.commit()
		except:
			print(Colors.RED + ' OH MY GOD WHAT IS THAT BEHIND YOU?' + Colors.ENDC)

	if argument == 'n':
		watch_list = []
		try:
			entered_numbers = [int(i) for i in final_selection.split()]
			watch_list = [relevant_list[j - 1][0] for j in entered_numbers]
		except:
			print(Colors.RED + ' Yerr a wizard, \'arry' + Colors.ENDC)
			exit()

		if len(watch_list) == 0:
			exit()
		print(' ' + Colors.YELLOW + 'Now monitoring:' + Colors.ENDC)
		watch_list = list(set(watch_list))
		watch_list.sort()
		print(Colors.WHITE + ' ' + ', '.join(watch_list) + Colors.ENDC)
		vigilo_confido(watch_list)


# Watches channels into the night. Like a silent protector.
def vigilo_confido(monitor_deez):
	player = Options.player_final

	channel_list_conky = ", ".join(monitor_deez)
	database.execute("INSERT INTO miscellaneous (Name,Value) VALUES ('%s','%s')" % ('BellatorInMachina', channel_list_conky))
	database.commit()

	while len(monitor_deez) > 0:
		channel_list = ','.join(monitor_deez)

		stream_data = api_request('https://api.twitch.tv/kraken/streams/' + '?limit=100' + '&channel=' + channel_list)
		total = stream_data['_total']

		for i in range(0, total):
			channel_name = stream_data['streams'][i]['channel']['name']
			print(' ' + Colors.GREEN + channel_name + Colors.ENDC + ' online @ ' + strftime('%H:%M'), end='')
			monitor_deez.remove(channel_name)

			channel_list_conky = ", ".join(monitor_deez)
			database.execute("UPDATE miscellaneous set Value = '%s' WHERE Name = 'BellatorInMachina'" % (channel_list_conky))
			database.commit()

			if len(channel_list_conky) > 0:
				print(' | Waiting for: ' + Colors.WHITE + channel_list_conky + Colors.ENDC)
			else:
				print()

			if player == 'vlc':
				player = 'cvlc'

			if which('notify-send') is not None:
				args_to_subprocess = 'notify-send --urgency=critical -i \'dialog-information\' \'Twitchy\' \'{0} is online\''.format(channel_name)
				args_to_subprocess = shlex.split(args_to_subprocess)
				subprocess.Popen(args_to_subprocess, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

			# Account for the possibility of being installed as well as being cloned
			script_dir = dirname(realpath(__file__))
			if exists(script_dir + '/alarm.mp3'):
				sound_dir = script_dir
			else:
				sound_dir = '/usr/share/twitchy'
			args_to_subprocess = '{0} {1}/alarm.mp3'.format(player, sound_dir)
			args_to_subprocess = shlex.split(args_to_subprocess)
			subprocess.run(args_to_subprocess, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

		if len(monitor_deez) > 0:
			sleep(Options.check_interval)


# Much VOD such wow
def vod_watch(channel_input):
	channel_input = channel_input[0].lower()
	i_wanna_see = input(' Watch (b)roadcasts or (h)ighlights: ')

	broadcast_string = ''
	if i_wanna_see == 'b':
		broadcast_string = '?broadcasts=true'

	stream_data = api_request('https://api.twitch.tv/kraken/channels/{0}/videos{1}'.format(channel_input, broadcast_string))

	try:
		totalvids = str(stream_data['_total'])
		if int(totalvids) == 0:
			raise
	except:
		print(Colors.RED + ' Channel does not exist or No VODs found.' + Colors.ENDC)
		exit()

	display_name = database.execute("SELECT AltName FROM channels WHERE Name = '%s'" % channel_input).fetchone()
	try:
		display_name = display_name[0]
		if display_name is None:
			raise
	except:
		display_name = stream_data['videos'][0]['channel']['display_name']

	""" Default to source quality in case the channel is not a Twitch partner """
	stream_data_partner = api_request('https://api.twitch.tv/kraken/channels/' + channel_input)

	ispartner = stream_data_partner['partner']
	if ispartner is False:
		default_quality = 'source'
		display_name_show = display_name + '*'
	else:
		default_quality = Options.default_quality
		display_name_show = display_name

	if broadcast_string == '':
		limit_string = '?limit=' + totalvids
		print(' Highlights for ' + Colors.YELLOW + display_name_show + Colors.ENDC + ':')
	else:
		limit_string = '&limit=' + totalvids
		print(' Past broadcasts for ' + Colors.YELLOW + display_name_show + Colors.ENDC + ':')

	stream_data = api_request('https://api.twitch.tv/kraken/channels/{0}/videos{1}{2}'.format(channel_input, broadcast_string, limit_string))

	vod_links = []
	total_streams_digits = len(str(len(stream_data['videos'])))
	for display_number, i in enumerate(stream_data['videos']):
		template = template_mapping('vods')
		creation_time = i['created_at'].split('T')[0]
		video_title = i['title']
		if len(video_title) > 55:
			video_title = i['title'][:55] + '...'
		if i_wanna_see == 'b':
			print(' ' + Colors.YELLOW + str(display_number + 1).rjust(total_streams_digits) + Colors.ENDC + ' ' + template.format(i['game'], video_title, creation_time))
		else:
			print(' ' + Colors.YELLOW + str(display_number + 1).rjust(total_streams_digits) + Colors.ENDC + ' ' + template.format(video_title, creation_time, ''))
		vod_links.append([i['url'], i['game'], video_title])

	vod_select = int(input(' VOD number: '))
	video_final = vod_links[vod_select - 1][0]
	game_name = vod_links[vod_select - 1][1]
	title_final = vod_links[vod_select - 1][2]

	playtime_instances([[video_final, default_quality, display_name, game_name, [channel_input, title_final]]])


# Generate stuff for livestreamer to agonize endless over. Is it fat? It's a program so no.
def watch(channel_input, argument):
	database_status = database.execute("SELECT Name,AltName FROM channels").fetchall()
	if not database_status:
		print(Colors.RED + ' Database is currently empty: Please run with -a or -s' + Colors.ENDC)
		exit()

	# Generate list of channels to be checked
	if argument == '' or argument[:5] == 'conky':
		status_check_required = database_status
	elif argument == 'w':
		status_check_required = []
		for j in channel_input:
			try:
				status_check_required.append((j, database.execute("SELECT AltName FROM channels WHERE Name = '%s'" % j).fetchone()[0]))
			except:
				status_check_required.append((j, None))
	elif argument == 'f':
		status_check_required = database.execute("SELECT Name,AltName,TimeWatched FROM channels WHERE TimeWatched > 0").fetchall()
	elif argument == 'search':
		status_check_required = database.execute("SELECT Name,AltName FROM channels WHERE Name LIKE '{0}' or AltName LIKE '{1}'".format(('%' + channel_input + '%'), ('%' + channel_input + '%'))).fetchall()

	if argument[:5] != 'conky':
		print(' ' + Colors.YELLOW + 'Checking {0} channel(s)...'.format(len(status_check_required)) + Colors.ENDC)

	stream_status = []

	def get_status(status_check_required):
		""" Queries to the Twitch API are limited to 100 results at a time
		Hence the dwindling """
		dwindler = [names[0] for names in status_check_required]
		while len(dwindler) > 0:
			try:
				channel_list = ','.join(dwindler[:100])
				del dwindler[:100]
			except:
				len_dwindler = len(dwindler)
				channel_list = ','.join(dwindler[:len_dwindler])
				del dwindler[:len_dwindler]

			stream_data = api_request('https://api.twitch.tv/kraken/streams/' + '?limit=100&channel=' + channel_list)
			total = stream_data['_total']

			for i in range(0, total):
				channel_name = stream_data['streams'][i]['channel']['name']
				game_name_formatted = str(stream_data['streams'][i]['channel']['game']).replace('\'', '')

				if Options.truncate_status_at == 'Auto':
					truncate_status_at = get_terminal_size().columns - 44
				else:
					truncate_status_at = int(Options.truncate_status_at)
				status_message = str(stream_data['streams'][i]['channel']['status'])
				if len(status_message) > truncate_status_at:
					status_message = status_message[0:truncate_status_at - 3] + '...'

				alt_name = [v[1] for i, v in enumerate(status_check_required) if v[0] == channel_name][0]
				if alt_name is None:
					alt_name = stream_data['streams'][i]['channel']['display_name']

				timewatched = 0
				if argument == 'f':
					timewatched = [v[2] for i, v in enumerate(status_check_required) if v[0] == channel_name][0]

				stream_status.append([channel_name, game_name_formatted, status_message, stream_data['streams'][i]['viewers'], alt_name, stream_data['streams'][i]['channel']['partner'], timewatched])
				""" List Scheme
				0: Channel name
				1: Game name
				2: Status message
				3: Viewers
				4: Display name
				5: Partner status - Boolean
				6: Time Watched - Should be zero if not explicitly queried"""

	get_status(status_check_required)

	""" Return online channels for conky
	Terminate the watch() function """
	if argument[:5] == 'conky':
		output = ''
		for i in stream_status:
			if argument == 'conky_go':
				output = i[4] + ', ' + output
			elif argument == 'conky_csv':
				""" The omission of the space is intentional """
				output = i[0] + ',' + output
		output = output.strip()[:-1]
		return output

	""" Continuation of the standard watch() function """
	if len(stream_status) > 0:
		if argument == 'f':
			""" The display list is now sorted in descending order """
			stream_status = sorted(stream_status, key=lambda x: x[6], reverse=True)

			""" Get ranks to display for -f """
			all_seen = database.execute("SELECT TimeWatched,Name FROM channels WHERE TimeWatched > 0").fetchall()
			all_seen.sort(reverse=True)
			names_only = [el[1] for el in all_seen]
		else:
			stream_status = sorted(stream_status, key=lambda x: (x[1], -x[3]))
	else:
		print(Colors.RED + ' All channels offline' + Colors.ENDC)
		exit()

	stream_final = []
	games_shown = []

	# Display table of online channels
	total_streams_digits = len(str(len(stream_status)))
	for display_number, i in enumerate(stream_status):
		try:
			display_name_game = database.execute("SELECT AltName FROM games WHERE Name = '%s'" % i[1]).fetchone()[0]
			if display_name_game is None:
				raise
		except:
			display_name_game = i[1]

		if i[5] is True:
			display_name_strimmer = i[4]
		else:
			display_name_strimmer = i[4] + '*'

		stream_final.insert(display_number, [i[0], i[1], i[4], i[5]])
		""" List scheme
		0: Channel Name
		1: Game Name
		2: Display Name
		3: Partner status - Boolean """
		template = template_mapping('watch')

		""" We need special formatting in case of -f """
		if argument == 'f':
			column_3_display = Colors.CYAN + str(display_name_game) + Colors.GREEN + ' - ' + i[2]
			if len(column_3_display) + 45 >= get_terminal_size().columns:
				column_3_display = column_3_display[0:get_terminal_size().columns - 40] + '...'
			rank = str(names_only.index(i[0]) + 1)
			print(' ' + Colors.YELLOW + (str(display_number + 1).rjust(total_streams_digits) + Colors.ENDC) + ' ' + (Colors.GREEN + template.format(display_name_strimmer + ' (' + rank + ')', time_convert(i[6]).rjust(11), column_3_display) + Colors.ENDC))
			if display_number == Options.number_of_faves_displayed - 1:
				break
		else:
			if display_name_game not in games_shown:
				print(' ' * total_streams_digits + Colors.CYAN + str(display_name_game) + Colors.ENDC)
				games_shown.append(display_name_game)
			print(' ' + Colors.YELLOW + (str(display_number + 1).rjust(total_streams_digits) + Colors.ENDC) + ' ' + (Colors.GREEN + template.format(display_name_strimmer, str(format(i[3], 'n')).rjust(8), i[2]) + Colors.ENDC))

	# Parse user input
	try:
		stream_select = input(' Channel number(s)? ')

		watch_input_final = []
		final_selection = []
		default_quality = Options.default_quality

		entered_numbers = stream_select.split()
		if not entered_numbers:
			# Select a random channel in case input is a blank line
			emote()
			entered_numbers.append(str(randrange(0, display_number + 1)))
		for a in entered_numbers:
			watch_input_final.append(a.split('-'))

		for j in watch_input_final:
			ispartner = stream_final[int(j[0]) - 1][3]
			if ispartner is True:
				if len(j) == 1:
					final_selection.append([stream_final[int(j[0]) - 1][0], default_quality, stream_final[int(j[0]) - 1][2], stream_final[int(j[0]) - 1][1], None])
				else:
					if j[1] == 'l':
						custom_quality = 'low'
					elif j[1] == 'm':
						custom_quality = 'medium'
					elif j[1] == 'h':
						custom_quality = 'high'
					elif j[1] == 's':
						custom_quality = 'source'
					else:
						custom_quality = default_quality
					final_selection.append([stream_final[int(j[0]) - 1][0], custom_quality, stream_final[int(j[0]) - 1][2], stream_final[int(j[0]) - 1][1], None])
			elif ispartner is False:
					final_selection.append([stream_final[int(j[0]) - 1][0], 'source', stream_final[int(j[0]) - 1][2], stream_final[int(j[0]) - 1][1], None])

		playtime_instances(final_selection)
	except (IndexError, ValueError):
		print(Colors.RED + ' Huh? Wut? Lel? Kappa?' + Colors.ENDC)


# Takes care of the livestreamer process(es) as well as time tracking
class Playtime:
	def __init__(self, final_selection, stream_quality, display_name, game_name, show_chat, channel_name_if_vod):
		self.final_selection = final_selection
		self.stream_quality = stream_quality
		self.display_name = display_name
		self.game_name = game_name
		self.show_chat = show_chat
		if channel_name_if_vod is not None:
			self.channel_name_if_vod = channel_name_if_vod[0]
			self.video_title_if_vod = channel_name_if_vod[1]
		else:
			self.channel_name_if_vod = None

	def play(self):
		self.start_time = time()

		""" Add game name to database after it's been started at least once """
		does_it_exist = database.execute("SELECT Name FROM games WHERE Name = '%s'" % self.game_name).fetchone()
		if does_it_exist is None:
			database.execute("INSERT INTO games (Name,Timewatched,AltName) VALUES ('%s',0,NULL)" % self.game_name)

		""" For conky output - Populate the miscellaneous table with the display name and start time """
		database.execute("INSERT INTO miscellaneous (Name,Value) VALUES ('%s','%s')" % (self.display_name, self.start_time))
		database.commit()

		if self.show_chat is True:
			try:
				webbrowser.get('chromium').open_new('--app=http://www.twitch.tv/%s/chat?popout=' % self.final_selection)
			except:
				webbrowser.open_new('http://www.twitch.tv/%s/chat?popout=' % self.final_selection)

		if self.channel_name_if_vod is None:
			print(' ' + Colors.WHITE + self.display_name + Colors.ENDC + ' | ' + Colors.WHITE + self.stream_quality.title() + Colors.ENDC)
			player_final = Options.player_final + ' --title ' + self.display_name.replace(' ', '')
			self.args_to_subprocess = "livestreamer twitch.tv/'{0}' '{1}' --player '{2}' --hls-segment-threads 3 --http-header Client-ID=guulhcvqo9djhuyhb2vi56wqnglc351".format(self.final_selection, self.stream_quality, player_final)
		else:
			print(' ' + Colors.WHITE + self.display_name + ': ' + self.video_title_if_vod + Colors.ENDC + ' | ' + Colors.WHITE + self.stream_quality.title() + Colors.ENDC)
			player_final = Options.player_final + ' --title ' + self.display_name
			self.args_to_subprocess = "livestreamer '{0}' '{1}' --player '{2}' --hls-segment-threads 3 --player-passthrough=hls --http-header Client-ID=guulhcvqo9djhuyhb2vi56wqnglc351".format(self.final_selection, self.stream_quality, player_final)

		self.args_to_subprocess = shlex.split(self.args_to_subprocess)
		self.livestreamer_process = subprocess.Popen(self.args_to_subprocess, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

	def time_tracking(self):
		end_time = time()
		time_watched = int(end_time - self.start_time)

		database = sqlite3.connect(database_path)

		""" Set name for VODs to enable time tracking """
		if self.channel_name_if_vod is not None:
			self.final_selection = self.channel_name_if_vod

		""" Update time watched for a channel that exists in the database (avoids exceptions due to -w) """
		channel_record = database.execute("SELECT Name,TimeWatched FROM channels WHERE Name = '%s'" % self.final_selection).fetchone()
		final_name = None
		if channel_record is not None:
			total_time_watched = channel_record[1] + time_watched
			database.execute("UPDATE channels set TimeWatched = '{0}' WHERE Name = '{1}'".format(total_time_watched, self.final_selection))

			all_seen = database.execute("SELECT TimeWatched,Name FROM channels WHERE TimeWatched > 0").fetchall()
			all_seen.sort(reverse=True)
			names_only = [el[1] for el in all_seen]
			rank = str(names_only.index(self.final_selection) + 1)
			final_name = Colors.WHITE + self.display_name + Colors.ENDC + ': ' + time_convert(total_time_watched) + ' (' + rank + ')'

		""" Update time watched for game. All game names will already be in the database. """
		game_details = database.execute("SELECT TimeWatched,Name,AltName FROM games WHERE Name = '%s'" % self.game_name).fetchone()
		total_time_watched = game_details[0] + time_watched
		database.execute("UPDATE games set TimeWatched = '{0}' WHERE Name = '{1}'".format(total_time_watched, self.game_name))

		all_seen = database.execute("SELECT TimeWatched,Name FROM games WHERE TimeWatched > 0").fetchall()
		all_seen.sort(reverse=True)
		names_only = [el[1] for el in all_seen]
		rank = str(names_only.index(self.game_name) + 1)
		if game_details[2] is None:
			game_display_name = game_details[1]
		else:
			game_display_name = game_details[2]
		final_game = Colors.WHITE + game_display_name + Colors.ENDC + ': ' + time_convert(total_time_watched) + ' (' + rank + ')'

		if final_name is None:
			print(' ' + final_game)
		else:
			print(' ' + final_name + ' | ' + final_game)

		database.execute("DELETE FROM miscellaneous WHERE Name = '{0}'".format(self.display_name))
		database.commit()


# Instantiate classes according to selection(s)
def playtime_instances(final_selection):
	""" Incoming list:
	0: Channel Name
	1: Quality
	2: Display Name
	3: Game Name
	4: VOD title (None if not required) """

	playtime_instance = {}
	total_streams = len(final_selection)

	show_chat = False
	if total_streams == 1:
		channel_name_if_vod = final_selection[0][4]
		if channel_name_if_vod is None:
			show_chat = True
			print(' q / Ctrl + C to quit | m to identify music ')
	elif total_streams > 1:
		print(' q / Ctrl + C to quit ')
		if Options.display_chat_for_multiple_twitch_streams is True:
			show_chat = True

	print(' Now watching:')
	for count, i in enumerate(final_selection):
		playtime_instance[count] = Playtime(i[0], i[1], i[2], i[3], show_chat, i[4])
		playtime_instance[count].play()

	playing_streams = [j for j in range(total_streams)]
	while playing_streams:
		for k in playing_streams:
			playtime_instance[k].livestreamer_process.poll()
			""" returncode does nothing without polling
			A delay in the while loop is introduced by the select method below """
			if playtime_instance[k].livestreamer_process.returncode is not None:
				if playtime_instance[k].livestreamer_process.returncode == 1:
					stream_error = playtime_instance[k].livestreamer_process.stdout.read().decode('utf-8').split('\n')
					error_message = [er for er in stream_error if 'error:' in er]
					print(' ' + Colors.RED + playtime_instance[k].display_name + Colors.ENDC + ' (' + error_message[0] + ')')
					# print(' ' + Colors.RED + playtime_instance[k].display_name + Colors.ENDC + ' (' + ' '.join(playtime_instance[k].args_to_subprocess) + ')')
					database.execute("DELETE FROM miscellaneous WHERE Name = '{0}'".format(playtime_instance[k].display_name))
					database.commit()
				else:
					playtime_instance[k].time_tracking()
				playing_streams.remove(k)
		try:
			keypress, o, e = select.select([sys.stdin], [], [], 0.8)
			if keypress:
				keypress_made = sys.stdin.readline().strip()
				if keypress_made == "q":
					raise KeyboardInterrupt
				elif keypress_made == "m" and total_streams == 1:
					webbrowser.open('http://www.twitchecho.com/%s' % playtime_instance[0].final_selection)
		except KeyboardInterrupt:
			for k in playing_streams:
				playtime_instance[k].time_tracking()
				playtime_instance[k].livestreamer_process.terminate()
			playing_streams.clear()


# Update the script to the latest git revision
def update_script():
	print(' ' + Colors.YELLOW + 'Checking for update...' + Colors.ENDC)
	script_path = realpath(__file__)

	with open(script_path) as script_text:
		the_lines = script_text.readlines()
	current_revision = the_lines[2].replace('\n', '')
	script_text.close()

	script_git_list = []
	script_git = requests.get('https://raw.githubusercontent.com/BasioMeusPuga/twitchy/master/twitchy.py', stream=True)
	for x in script_git.iter_lines():
		script_git_list.append(x)
	git_revision = script_git_list[2].decode('utf-8')

	if current_revision == git_revision:
		print(' ' + Colors.GREEN + 'Already at latest revision.' + Colors.ENDC)
	else:
		script_path = open(realpath(__file__), mode='w')
		script_git = requests.get('https://raw.githubusercontent.com/BasioMeusPuga/twitchy/master/twitchy.py', stream=True)
		script_path.write(script_git.text)
		print(' ' + Colors.GREEN + 'Updated to Revision' + git_revision.split('=')[1] + Colors.ENDC)


# Get output for a conky instance
def firefly_needed_another_6_seasons(at_least):
	Options.conky_run = True

	output = []
	if at_least == 'go':
		print(watch(None, 'conky_go'))
		exit()
	elif at_least == 'csvnames':
		print(watch(None, 'conky_csv'))
		exit()

	database = sqlite3.connect(database_path)

	play_status = database.execute("SELECT Name,Value FROM miscellaneous").fetchall()
	number_playing = len(play_status)
	if number_playing == 0:
		exit(1)
	else:
		if play_status[0][0] == 'BellatorInMachina':
			""" Monitor """
			print('(M) ' + play_status[0][1])
		else:
			""" Any channels being watched """
			for i in play_status:
				current_time = time()
				start_time = float(play_status[0][1])
				time_watched = time_convert(current_time - start_time)
				output.append(i[0] + ' (' + time_watched + ')')
			print(' | '.join(output))


# Or maybe it's this one.
def nuke_it_from_orbit():
	print('Are you sure you want to remove the database and start over?')
	confirm = input('Please type ' + Colors.RED + 'KappaKeepoPogChamp' + Colors.ENDC + ' to continue: ')
	if confirm == 'KappaKeepoPogChamp':
		remove(database_path)


# On Exit
def thatsallfolks():
	if Options.conky_run is False:
		try:
			database.execute("DELETE FROM miscellaneous")
			database.commit()
			database.close()
		except:
			pass


# Parse CLI input
def main():
	atexit.register(thatsallfolks)

	parser = argparse.ArgumentParser(description='Watch twitch.tv from your terminal. IT\'S THE FUTURE.', add_help=False)
	parser.add_argument('searchfor', type=str, nargs='?', help='Search for channel name in database', metavar='*searchstring*')
	parser.add_argument('-h', '--help', help='This helpful message', action='help')
	parser.add_argument('-a', type=str, nargs='+', help='Add channel name(s) to database', metavar='')
	parser.add_argument('-an', type=str, nargs='?', const='BlankForAllIntensivePurposes', help='Set/Unset alternate names', metavar='*searchstring*')
	parser.add_argument('--configure', action='store_true', help='Configure options')
	parser.add_argument('--conky', type=str, nargs='?', const='BlankForAllIntensivePurposes', help='Generate data for conky', metavar='<none> / go / csvnames')
	parser.add_argument('-d', type=str, nargs='?', const='BlankForAllIntensivePurposes', help='Delete channel(s) from database', metavar='*searchstring*')
	parser.add_argument('-f', action='store_true', help='Check if your favorite channels are online')
	parser.add_argument('-n', type=str, nargs='?', const='BlankForAllIntensivePurposes', help='Notify when online', metavar='*searchstring*')
	parser.add_argument('--reset', action='store_true', help='Start over')
	parser.add_argument('-s', type=str, nargs=1, help='Sync username\'s followed accounts to local database', metavar='username')
	parser.add_argument('--update', action='store_true', help='Update to git master')
	parser.add_argument('-v', type=str, nargs=1, help='Watch VODs', metavar='')
	parser.add_argument('-w', type=str, nargs='+', help='Watch specified channel(s)', metavar='')
	args = parser.parse_args()

	if (args.s or args.v) and args.searchfor:
		parser.error('Only one argument allowed with -s and -v')
		exit()

	if args.a:
		add_to_database(args.a, 'a')
	elif args.an:
		read_modify_deletefrom_database(args.an, 'CantTouchThis', 'an')
	elif args.configure:
		configure_options('TheDudeAbides')
	elif args.conky:
		firefly_needed_another_6_seasons(args.conky)
	elif args.d:
		read_modify_deletefrom_database(args.d, 'CantTouchThis', 'd')
	elif args.f:
		watch(None, 'f')
	elif args.n:
		read_modify_deletefrom_database(args.n, 'ItsHammerTime', 'n')
	elif args.reset:
		nuke_it_from_orbit()
	elif args.s:
		add_to_database(args.s, 's')
	elif args.update:
		update_script()
	elif args.v:
		vod_watch(args.v)
	elif args.w:
		watch(args.w, 'w')
	elif args.searchfor:
		watch(args.searchfor, 'search')
	else:
		watch(None, '')


if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		thatsallfolks()
