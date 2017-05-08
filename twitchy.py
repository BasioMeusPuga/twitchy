#!/usr/bin/env python3
# Requires: python3, livestreamer, requests
# rev = 133


import sys
import json
import shlex
import atexit
import select
import locale
import sqlite3
import requests
import datetime
import argparse
import webbrowser
import subprocess
import configparser

from time import time, sleep, strftime
from shutil import which, get_terminal_size
from random import randrange
from os import remove, makedirs
from os.path import expanduser, exists, realpath, dirname


# Color code declaration for initial configuration and Options
class Colors:
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    WHITE = '\033[97m'
    ENDC = '\033[0m'


# Create database
def create_database(database_path):
    database = sqlite3.connect(database_path)

    database.execute("CREATE TABLE channels (id INTEGER PRIMARY KEY, Name TEXT, TimeWatched INTEGER, AltName TEXT)")
    database.execute("CREATE TABLE games (id INTEGER PRIMARY KEY, Name TEXT, TimeWatched INTEGER, AltName TEXT)")
    database.execute("CREATE TABLE miscellaneous (id INTEGER PRIMARY KEY, Name TEXT, Value TEXT)")


# Option configuration using something that vaguely resembles a wizard
# Options are saved to ~/.twitchy.cfg by default. There are MANY more options over there
def configure_options():
    try:
        # Turns out, we don't actually need a no_default
        yes_default = ['y', 'Y', 'yes', 'YES']

        print(Colors.CYAN + ' Configure:' + Colors.ENDC)

        backend = input(' Backend: (s)treamlink / (l)ivestreamer ')
        if backend != 'l':
            backend = 'streamlink'

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
            if mpv_option in yes_default:
                mpv_hardware_acceleration = True

        default_quality = input(' Default stream quality [low/medium/HIGH/source]: ')
        if default_quality == '' or default_quality not in ['low', 'medium', 'source']:
            default_quality = 'high'

        truncate_status_at = input(' Truncate stream status at [AUTO]: ')
        if truncate_status_at == '':
            truncate_status_at = 0
        else:
            truncate_status_at = int(truncate_status_at)

        # The number of favorites displayed does not include offline channels.
        # i.e. setting this value to n will display - in descending order of time watched,
        # the first n ONLINE channels in the database
        number_of_faves_displayed = input(' Number of favorites to display [5]: ')
        if number_of_faves_displayed == '':
            number_of_faves_displayed = 5
        else:
            number_of_faves_displayed = int(number_of_faves_displayed)

        chat_for_mt = input(' Display chat for multiple Twitch streams [y/N]: ')
        if chat_for_mt in yes_default:
            display_chat_for_multiple_twitch_streams = True
        else:
            display_chat_for_multiple_twitch_streams = False

        check_int = input(' Interval (seconds) in between channel status checks [60]: ')
        if check_int == '':
            check_interval = 60
        else:
            check_interval = int(check_int)

        print('\n' + Colors.CYAN + ' Current Settings:' + Colors.ENDC)
        penultimate_check = (' Backend: {6}\n'
                             ' Media Player: {0}\n'
                             ' Default Quality: {1}\n'
                             ' Truncate status at: {2}\n'
                             ' Number of faves: {3}\n'
                             ' Display chat for multiple streams: {4}\n'
                             ' Check interval: {5}').format(
            Colors.YELLOW + player + Colors.ENDC,
            Colors.YELLOW + default_quality + Colors.ENDC,
            Colors.YELLOW + str(truncate_status_at) + Colors.ENDC,
            Colors.YELLOW + str(number_of_faves_displayed) + Colors.ENDC,
            Colors.YELLOW + str(display_chat_for_multiple_twitch_streams) + Colors.ENDC,
            Colors.YELLOW + str(check_interval) + Colors.ENDC,
            Colors.YELLOW + backend + Colors.ENDC)

        print(penultimate_check)

        do_we_like = input(' Does this look correct to you? [Y/n]: ')
        if do_we_like == '' or do_we_like in yes_default:
            options_to_insert = [player,
                                 mpv_hardware_acceleration,
                                 default_quality,
                                 truncate_status_at,
                                 number_of_faves_displayed,
                                 display_chat_for_multiple_twitch_streams,
                                 check_interval,
                                 backend]

            write_to_config_file(options_to_insert)

        else:
            raise
    except KeyboardInterrupt:
        try:
            final_decision = input(Colors.RED + ' Do you wish to restart? [y/N]: ' + Colors.ENDC)
            if final_decision in yes_default:
                print()
                configure_options()
            else:
                exit()
        except KeyboardInterrupt:
            exit()


def write_to_config_file(options_from_wizard):
    player = options_from_wizard[0]
    mpv_hardware_acceleration = options_from_wizard[1]
    default_quality = options_from_wizard[2]
    truncate_status_at = options_from_wizard[3]
    number_of_faves_displayed = options_from_wizard[4]
    display_chat_for_multiple_twitch_streams = options_from_wizard[5]
    check_interval = options_from_wizard[6]
    backend = options_from_wizard[7]

    config_string = ('# Twitchy configuration file\n'
                     '\n'
                     '[VIDEO]\n'
                     '# Valid options are: streamlink, livestreamer\n'
                     'Backend = {0}\n'
                     'Player = {1}\n'
                     '# This is only valid if using mpv. VAAPI is only supported on Linux.\n'
                     'MPVHardwareAcceleration = {2}\n'
                     '# Valid options are: low, mid, high, source\n'
                     'DefaultQuality = {3}\n'
                     '\n'
                     '\n'
                     '[COLUMNS]\n'
                     '# Valid options are: ChannelName, Viewers, Uptime, StreamStatus, GameName\n'
                     '# Columns do not auto resize so be gentle with what you use for Column 2\n'
                     'Column1 = ChannelName\n'
                     'Column2 = Viewers\n'
                     'Column3 = StreamStatus\n'
                     '\n'
                     '\n'
                     '[DISPLAY]\n'
                     '# Valid options are: 1, 2, 3 or GameName\n'
                     'SortBy = GameName\n'
                     '# Shows the name of each column in case sorting is not by GameName\n'
                     'ColumnNames = False\n'
                     '# Set to 0 for auto truncation. Any other positive integer for manual control\n'
                     'TruncateStatus = {4}\n'
                     'NumberOfFaves = {5}\n'
                     'CheckInterval = {6}\n'
                     '\n'
                     '\n'
                     '[COLORS]\n'
                     '# Valid colors are: black, gray, white and dark(red, green, yellow, blue, magenta, cyan)\n'
                     'Numbers = yellow\n'
                     'GameName = cyan\n'
                     'Column1 = green\n'
                     'Column2 = green\n'
                     'Column3 = green\n'
                     '\n'
                     '\n'
                     '[CHAT]\n'
                     'Enable = True\n'
                     'EnableForMultiTwitch = {7}\n'.format(
                         backend,
                         player,
                         mpv_hardware_acceleration,
                         default_quality,
                         truncate_status_at,
                         number_of_faves_displayed,
                         check_interval,
                         display_chat_for_multiple_twitch_streams))

    with open(config_path, 'w') as config_file:
        config_file.write(config_string)
        print()
        print(Colors.CYAN + ' Options written to {}. Please read for additional settings.'.format(config_path) + Colors.ENDC)


# Check for requirements
if which('livestreamer') is None and which('streamlink') is None:
    print(Colors.RED + ' livestreamer / streamlink' + Colors.ENDC + ' not installed. FeelsBadMan.')
    exit()

# Both the config file and the directory are going to go in their own directory in .config
# First we'll see if the config directory exists, if it doesn't, well, everything goes right back to $HOME
if exists(expanduser('~') + '/.config'):
    location_prefix = expanduser('~') + '/.config/twitchy/'
    if not exists(location_prefix):
        makedirs(location_prefix)
else:
    location_prefix = expanduser('~') + '/.'

# Names of the actual files
database_path = location_prefix + 'twitchy.db'
config_path = location_prefix + 'twitchy.cfg'

# Create the database and config files in case they don't exist
if not exists(database_path):
    print(Colors.CYAN + ' Creating database: Add channels with -a or -s' + Colors.ENDC)
    create_database(database_path)
    if exists(config_path):
        exit()
database = sqlite3.connect(database_path)

if not exists(config_path):
    print(Colors.CYAN + ' Config file not found. Running --configure' + Colors.ENDC)
    configure_options()
    exit()

# Set locale for comma placement
locale.setlocale(locale.LC_ALL, '')


# The classy choice
class Options:
    try:
        # Get options from the config file
        # The only things we want in all the following cases are the values in the dictionary
        config = configparser.ConfigParser()
        config.read(config_path)

        # Video options
        video_section = config['VIDEO']

        backend = video_section.get('Backend', 'streamlink')
        if backend not in ['streamlink', 'livestreamer']:
            raise

        player = video_section.get('Player', 'mpv')
        hw_accel = video_section.getboolean('MPVHardwareAcceleration', False)
        if player == 'mpv' and hw_accel is True:
            player_final = 'mpv --hwdec=vaapi --vo=vaapi --cache 8192'
        else:
            player_final = 'mpv --cache 8192'

        default_quality = video_section.get('DefaultQuality', 'high')
        if default_quality not in ['low', 'medium', 'high', 'source']:
            default_quality = 'high'

        video = dict(backend=backend,
                     default_quality=default_quality,
                     player_final=player_final)

        # Which columns to display
        columns_section = config['COLUMNS']
        columns = dict(column1=columns_section.get('Column1', 'ChannelName'),
                       column2=columns_section.get('Column2', 'Viewers'),
                       column3=columns_section.get('Column3', 'StreamStatus'))

        # Display options
        display_section = config['DISPLAY']
        sort_by = display_section.get('SortBy', 'GameName')
        if sort_by not in ['1', '2', '3', 'GameName']:
            sort_by = 'GameName'
        display = dict(sort_by=sort_by,
                       column_names=display_section.getboolean('ColumnNames', False),
                       truncate_status=display_section.getint('TruncateStatus', 0),
                       faves_displayed=display_section.getint('NumberOfFaves', 10),
                       check_interval=display_section.getint('CheckInterval', 60))

        # How to color everything
        colors_section = config['COLORS']
        numbers = colors_section.get('Numbers', 'yellow')
        game_name = colors_section.get('GameName', 'cyan')
        column1 = colors_section.get('Column1', 'green')
        column2 = colors_section.get('Column2', 'green')
        column3 = colors_section.get('Column3', 'green')

        # Generate escape codes per color
        escape_codes = {
            'black': '\033[30m',
            'darkgray': '\033[90m',
            'darkred': '\033[31m',
            'red': '\033[91m',
            'darkgreen': '\033[32m',
            'green': '\033[92m',
            'darkyellow': '\033[33m',
            'yellow': '\033[93m',
            'darkblue': '\033[34m',
            'blue': '\033[94m',
            'darkmagenta': '\033[35m',
            'magenta': '\033[95m',
            'darkcyan': '\033[36m',
            'cyan': '\033[96m',
            'gray': '\033[37m',
            'white': '\033[97m',
            'end': '\033[0m'}

        try:
            colors = dict(numbers=escape_codes[numbers],
                          game_name=escape_codes[game_name],
                          column1=escape_codes[column1],
                          column2=escape_codes[column2],
                          column3=escape_codes[column3])
        except KeyError:
            print(Colors.RED + ' You know it\'s possible you don\'t know how to spell the names of colors.' + Colors.ENDC)
            raise

        # When do we want to display chat
        chat_section = config['CHAT']
        chat = dict(enable=chat_section.getboolean('Enable', True),
                    for_multi_twitch=chat_section.getboolean('EnableForMultiTwitch', False))

        # Required only at runtime in case values for a conky instance are needed
        conky_run = False

        # Map to the new alternate quality settings that Twitch has introduced
        # This adds a little time to the initial start but saves on a lot of confusion and errors
        alternate_quality = {
            'low': '360p',
            'medium': '480p',
            'high': '720p',
            'source': 'best'}

    except:
        print(Colors.RED + ' Error getting options. Running --configure:' + Colors.ENDC)
        configure_options()
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
    # Preceding specification is mostly pointless as long as it's non zero
    # If however, it exceeds the column number of the terminal, we'll get the unenviable
    # free line breaks. That's just silly.

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
        second_column = 20
    elif called_from == 'vods':
        first_column = 40
        second_column = 60

    template = '{0:%s}{1:%s}{2:%s}' % (first_column, second_column, third_column)
    return template


# Convert time in seconds to a more human readable format,
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
            does_it_exist = database.execute("SELECT Name FROM channels WHERE Name = '%s'" % channel_name).fetchone()
            if does_it_exist is None:
                something_added = True
                database.execute("INSERT INTO channels (Name,TimeWatched) VALUES ('%s',0)" % channel_name)
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
                final_addition_streams.append(stream_data['follows'][i]['channel']['name'])
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
        if table_wanted.lower() == 's':
            table_wanted = 'channels'
        elif table_wanted.lower() == 'g':
            table_wanted = 'games'
        else:
            exit()

    if channel_input == 'BlankForAllIntensivePurposes':
        relevant_list = database.execute("SELECT Name, TimeWatched, AltName FROM %s" % table_wanted).fetchall()
    else:
        relevant_list = database.execute("SELECT Name, TimeWatched, AltName FROM '{0}' WHERE Name LIKE '{1}' OR AltName LIKE '{1}'".format(
            table_wanted, ('%' + channel_input + '%'))).fetchall()

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
                print(' ' + Options.colors['numbers'] + str(display_number).rjust(total_streams_digits) + Colors.ENDC + ' '
                      + template.format(i[0], Colors.CYAN + str(i[2]) + Colors.RED, '  Unwatched' + Colors.ENDC))
            else:
                time_watched = time_convert(i[1]).rjust(11)
                print(' ' + Options.colors['numbers'] + str(display_number).rjust(total_streams_digits) + Colors.ENDC + ' '
                      + template.format(i[0], Colors.CYAN + str(i[2]) + Colors.ENDC, time_watched))
        else:
            if table_wanted == 'channels':
                template = template_mapping('listnocolor')
            elif table_wanted == 'games':
                template = template_mapping('gameslistnocolor')

            if i[1] == 0:
                print(' ' + Options.colors['numbers'] + str(display_number).rjust(total_streams_digits) + Colors.RED + ' '
                      + template.format(i[0], str(i[2]), '  Unwatched') + Colors.ENDC)
            else:
                time_watched = time_convert(i[1]).rjust(11)
                print(' ' + Options.colors['numbers'] + str(display_number).rjust(total_streams_digits) + Colors.ENDC + ' '
                      + template.format(i[0], str(i[2]), time_watched))
        display_number += 1

    final_selection = input(' Stream / Channel number(s)? ')

    if argument == 'd':
        try:
            print(' ' + Options.colors['numbers'] + 'Deleted from database:' + Colors.ENDC)
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
        print(' ' + Options.colors['numbers'] + 'Now monitoring:' + Colors.ENDC)
        watch_list = list(set(watch_list))
        watch_list.sort()
        print(Colors.WHITE + ' ' + ', '.join(watch_list) + Colors.ENDC)
        vigilo_confido(watch_list)


# Watches channels into the night. Like a silent protector.
def vigilo_confido(monitor_deez):
    player = Options.video['player_final']

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
            database.execute("UPDATE miscellaneous set Value = '%s' WHERE Name = 'BellatorInMachina'" % channel_list_conky)
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
            sleep(Options.display['check_interval'])


# Much VOD such wow
def vod_watch(channel_input):
    channel_input = channel_input[0]
    i_wanna_see = input(' Watch (b)roadcasts or (h)ighlights: ')

    broadcast_string = ''
    if i_wanna_see == 'b':
        broadcast_string = '?broadcasts=true'

    stream_data = api_request('https://api.twitch.tv/kraken/channels/{0}/videos{1}'.format(channel_input, broadcast_string))

    try:
        totalvids = str(stream_data['_total'])
        if int(totalvids) == 0:
            raise
        elif int(totalvids) > 100:
            # We're currently limiting the number of VODs displayed to the 100 most recent entries
            # Honestly, I'm not sure if I want to take it much beyond that.
            totalvids = '100'
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

    # Default to source quality in case the channel is not a Twitch partner
    stream_data_partner = api_request('https://api.twitch.tv/kraken/channels/' + channel_input)
    ispartner = stream_data_partner['partner']
    if ispartner is False:
        default_quality = 'source'
        display_name_show = display_name + '*'
    else:
        default_quality = Options.video['default_quality']
        display_name_show = display_name

    if broadcast_string == '':
        limit_string = '?limit=' + totalvids
        print(' Highlights for ' + Options.colors['numbers'] + display_name_show + Colors.ENDC + ':')
    else:
        limit_string = '&limit=' + totalvids
        print(' Past broadcasts for ' + Options.colors['numbers'] + display_name_show + Colors.ENDC + ':')

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
            print(' ' + Options.colors['numbers'] + str(display_number + 1).rjust(total_streams_digits) + Colors.ENDC + ' '
                  + template.format(i['game'], video_title, creation_time))
        else:
            print(' ' + Options.colors['numbers'] + str(display_number + 1).rjust(total_streams_digits) + Colors.ENDC + ' '
                  + template.format(video_title, creation_time, ''))
        vod_links.append([i['url'], i['game'], video_title])

    vod_select = int(input(' VOD number: '))
    video_final = vod_links[vod_select - 1][0]
    game_name = vod_links[vod_select - 1][1]
    title_final = vod_links[vod_select - 1][2]

    playtime_instances([[video_final, default_quality, display_name, game_name, [channel_input, title_final]]])


# Generate stuff for livestreamer / streamlink to agonize endless over. Is it fat? It's a program so no.
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
        status_check_required = database.execute("SELECT Name,AltName FROM channels WHERE Name LIKE '{0}' or AltName LIKE '{1}'".format(
            ('%' + channel_input + '%'), ('%' + channel_input + '%'))).fetchall()

    if argument[:5] != 'conky':
        print(' ' + Options.colors['numbers'] + 'Checking {0} channel(s)...'.format(len(status_check_required)) + Colors.ENDC)

    stream_status = []

    def get_status(status_check_required):
        # Queries to the Twitch API are limited to 100 results at a time
        # Hence the dwindling
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

                # Get stream uptime by subtracting stream creation time from current UTC provided by the datetime module
                # It's better to keep this in seconds to allow for sorting later
                start_time = str(stream_data['streams'][i]['created_at'])
                datetime_start_time = datetime.datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%SZ')
                stream_uptime_seconds = (datetime.datetime.utcnow() - datetime_start_time).seconds

                # Generate status truncation
                if Options.display['truncate_status'] == 0:
                    truncate_status_at = get_terminal_size().columns - 44
                else:
                    truncate_status_at = int(Options.display['truncate_status'])
                status_message = str(stream_data['streams'][i]['channel']['status'])
                if len(status_message) > truncate_status_at:
                    status_message = status_message[0:truncate_status_at - 3] + '...'

                alt_name = [v[1] for i, v in enumerate(status_check_required) if v[0] == channel_name][0]
                if alt_name is None:
                    alt_name = stream_data['streams'][i]['channel']['display_name']

                # Reserved only for the -f argument - Should be 0 if not explicitly queried
                timewatched = 0
                if argument == 'f':
                    timewatched = [v[2] for i, v in enumerate(status_check_required) if v[0] == channel_name][0]

                stream_status.append([
                    channel_name,
                    game_name_formatted,
                    status_message,
                    stream_data['streams'][i]['viewers'],
                    alt_name,
                    stream_data['streams'][i]['channel']['partner'],
                    timewatched,
                    stream_uptime_seconds])
                """ List Scheme
                0: Channel name
                1: Game name
                2: Status message
                3: Viewers
                4: Display name
                5: Partner status - Boolean
                6: Time Watched
                7: Stream uptime in seconds"""

    get_status(status_check_required)
    # Map the stream_status list to the names of custom columns
    custom_columns = dict(GameName=1,
                          StreamStatus=2,
                          Viewers=3,
                          ChannelName=4,
                          Uptime=7)

    # Return online channels for conky
    # Terminate the watch() function
    if argument[:5] == 'conky':
        output = ''
        for i in stream_status:
            if argument == 'conky_go':
                output = i[4] + ', ' + output
            elif argument == 'conky_csv':
                # The omission of the space is intentional
                output = i[0] + ',' + output
        output = output.strip()[:-1]
        return output

    # Continuation of the standard watch() function
    # The list is sorted according to specifications in twitchy.cfg
    if len(stream_status) > 0:
        if argument == 'f':
            # The display list is now sorted in descending order
            stream_status = sorted(stream_status, key=lambda x: x[6], reverse=True)

            # Get ranks to display for -f
            all_seen = database.execute("SELECT TimeWatched,Name FROM channels WHERE TimeWatched > 0").fetchall()
            all_seen.sort(reverse=True)
            names_only = [el[1] for el in all_seen]
        else:
            if Options.display['sort_by'] == 'GameName':
                # By default, streams are first sorted by the game name (0), and then by the number of viewers (3)
                stream_status = sorted(stream_status, key=lambda x: (x[1], -x[3]))
            else:
                # If some other column is specified in twitchy.cfg, sorting happens by way of its integer value
                sorting_column = int(Options.display['sort_by'])
                if sorting_column == 1:
                    sorting_key = custom_columns[Options.columns['column1']]
                elif sorting_column == 2:
                    sorting_key = custom_columns[Options.columns['column2']]
                else:
                    sorting_key = custom_columns[Options.columns['column3']]
                stream_status = sorted(stream_status, key=lambda x: x[sorting_key], reverse=True)

    else:
        print(Colors.RED + ' All channels offline' + Colors.ENDC)
        exit()

    stream_final = []
    games_shown = []

    # Special formatting in case ColumnNames is enabled
    # AND the game name is not displayed
    # AND we're not in favorite mode
    if Options.display['column_names'] is True and Options.display['sort_by'] != 'GameName' and argument != 'f':
        column_template = '{0:%s}{1:%s}{2:100}' % (35 - len(Options.columns['column2']), 7 + len(Options.columns['column2']))
        print()
        print(' ' + column_template.format(Options.colors['game_name'] + Options.columns['column1'],
              Options.columns['column2'],
              Options.columns['column3'] + Colors.ENDC))

    # Map out the template for the online stream table
    template = template_mapping('watch')
    total_streams_digits = len(str(len(stream_status)))

    # Display table of online channels
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

        # Special formatting in the case of -f
        if argument == 'f':
            column_3_display = Options.colors['game_name'] + str(display_name_game) + Options.colors['column3'] + ' - ' + i[2]
            if len(column_3_display) + 45 >= get_terminal_size().columns:
                column_3_display = column_3_display[0:get_terminal_size().columns - 45] + '...'
            rank = str(names_only.index(i[0]) + 1)
            print(' ' + Options.colors['numbers'] + (str(display_number + 1).rjust(total_streams_digits) + Colors.ENDC) + ' '
                  + (template.format(Options.colors['column1'] + display_name_strimmer + ' (' + rank + ')',
                                     Options.colors['column2'] + time_convert(i[6]).rjust(11),
                                     column_3_display)) + Colors.ENDC)
            if display_number == Options.display['faves_displayed'] - 1:
                break

        # This is the table the user will see under most circumstances
        else:

            # These are only for the default display. -f is a separate entity except for the colors
            column_display = [Options.columns['column1'],
                              Options.columns['column2'],
                              Options.columns['column3']]

            columns_final = []
            for column in column_display:
                if column == 'GameName':
                    columns_final.append(display_name_game)
                elif column == 'StreamStatus':
                    columns_final.append(i[2])
                elif column == 'Viewers':
                    columns_final.append(str(format(i[3], 'n')))
                elif column == 'ChannelName':
                    columns_final.append(display_name_strimmer)
                elif column == 'Uptime':
                    columns_final.append(time_convert(i[7]))

            if display_name_game not in games_shown:
                # Show the game name only if the list has been sorted by it
                if Options.display['sort_by'] == 'GameName':
                    print(' ' * total_streams_digits + Options.colors['game_name'] + str(display_name_game) + Colors.ENDC)
                games_shown.append(display_name_game)
            print(' ' + Options.colors['numbers'] + (str(display_number + 1).rjust(total_streams_digits) + Colors.ENDC) + ' '
                  + template.format(Options.colors['column1'] + columns_final[0],
                                    Options.colors['column2'] + columns_final[1].rjust(8),
                                    Options.colors['column3'] + columns_final[2]) + Colors.ENDC)

    # Parse user input
    try:
        stream_select = input(' Channel number(s)? ')

        watch_input_final = []
        final_selection = []
        default_quality = Options.video['default_quality']

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
                    final_selection.append([stream_final[int(j[0]) - 1][0],
                                            default_quality,
                                            stream_final[int(j[0]) - 1][2],
                                            stream_final[int(j[0]) - 1][1],
                                            None])
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
                    final_selection.append([stream_final[int(j[0]) - 1][0],
                                            custom_quality,
                                            stream_final[int(j[0]) - 1][2],
                                            stream_final[int(j[0]) - 1][1],
                                            None])
            elif ispartner is False:
                    final_selection.append([stream_final[int(j[0]) - 1][0],
                                            'source',
                                            stream_final[int(j[0]) - 1][2],
                                            stream_final[int(j[0]) - 1][1],
                                            None])

        playtime_instances(final_selection)
    except (IndexError, ValueError):
        print(Colors.RED + ' Huh? Wut? Lel? Kappa?' + Colors.ENDC)


# Takes care of the livestreamer / streamlink process(es) as well as time tracking
class Playtime:
    def __init__(self, final_selection, stream_quality, display_name, game_name, show_chat, channel_name_if_vod):
        self.final_selection = final_selection
        self.stream_quality = stream_quality
        self.stream_quality_alternate = Options.alternate_quality[self.stream_quality]
        self.alternate_quality_tried = False  # In case the alternate quality doesn't work either
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

        # Add game name to database after it's been started at least once
        does_it_exist = database.execute("SELECT Name FROM games WHERE Name = '%s'" % self.game_name).fetchone()
        if does_it_exist is None:
            database.execute("INSERT INTO games (Name,Timewatched,AltName) VALUES ('%s',0,NULL)" % self.game_name)

        # For conky output - Populate the miscellaneous table with the display name and start time
        database.execute("INSERT INTO miscellaneous (Name,Value) VALUES ('%s','%s')" % (self.display_name, self.start_time))
        database.commit()

        # It is now possible to override chat window display even for a single streamer
        if self.show_chat is True and Options.chat['enable'] is True:
            try:
                webbrowser.get('chromium').open_new('--app=http://www.twitch.tv/%s/chat?popout=' % self.final_selection)
            except webbrowser.Error:
                webbrowser.open_new('http://www.twitch.tv/%s/chat?popout=' % self.final_selection)

        if self.channel_name_if_vod is None:
            print(' ' + Colors.WHITE + self.display_name + Colors.ENDC + ' | ' + Colors.WHITE + self.stream_quality.title() + Colors.ENDC)
            player_final = Options.video['player_final'] + ' --title ' + self.display_name.replace(' ', '')

            self.args_to_subprocess = "{3} twitch.tv/'{0}' '{1}' --player '{2}' --hls-segment-threads 3 --http-header Client-ID=guulhcvqo9djhuyhb2vi56wqnglc351".format(
                self.final_selection, self.stream_quality, player_final, Options.video['backend'])

            # Alternate quality in case the default one errors out
            self.args_to_subprocess_alternate = "{3} twitch.tv/'{0}' '{1}' --player '{2}' --hls-segment-threads 3 --http-header Client-ID=guulhcvqo9djhuyhb2vi56wqnglc351".format(
                self.final_selection, self.stream_quality_alternate, player_final, Options.video['backend'])
        else:
            print(' ' + Colors.WHITE + self.display_name + ': ' + self.video_title_if_vod + Colors.ENDC + ' | ' + Colors.WHITE + self.stream_quality.title() + Colors.ENDC)
            player_final = Options.video['player_final'] + ' --title ' + self.display_name

            self.args_to_subprocess = "{3} '{0}' '{1}' --player '{2}' --hls-segment-threads 3 --player-passthrough=hls --http-header Client-ID=guulhcvqo9djhuyhb2vi56wqnglc351".format(
                self.final_selection, self.stream_quality, player_final, Options.video['backend'])

            # Alternate quality in case the default one errors out
            self.args_to_subprocess_alternate = "{3} '{0}' '{1}' --player '{2}' --hls-segment-threads 3 --player-passthrough=hls --http-header Client-ID=guulhcvqo9djhuyhb2vi56wqnglc351".format(
                self.final_selection, self.stream_quality_alternate, player_final, Options.video['backend'])

        self.args_to_subprocess = shlex.split(self.args_to_subprocess)
        self.args_to_subprocess_alternate = shlex.split(self.args_to_subprocess_alternate)

        # Starts with the default quality setting
        self.livestreamer_process = subprocess.Popen(self.args_to_subprocess, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    def time_tracking(self):
        end_time = time()
        time_watched = int(end_time - self.start_time)

        database = sqlite3.connect(database_path)

        # Set name for VODs to enable time tracking
        if self.channel_name_if_vod is not None:
            self.final_selection = self.channel_name_if_vod

        # Update time watched for a channel that exists in the database (avoids exceptions due to -w)
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

        # Update time watched for game. All game names will already be in the database.
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
    print(' q / Ctrl + C to quit ')
    if total_streams == 1:
        channel_name_if_vod = final_selection[0][4]
        if channel_name_if_vod is None:
            show_chat = True
    if total_streams > 1 and Options.chat['for_multi_twitch'] is True:
        show_chat = True

    print(' Now watching:')
    for count, i in enumerate(final_selection):
        playtime_instance[count] = Playtime(i[0], i[1], i[2], i[3], show_chat, i[4])
        playtime_instance[count].play()

    playing_streams = [j for j in range(total_streams)]
    while playing_streams:
        for k in playing_streams:
            playtime_instance[k].livestreamer_process.poll()
            # returncode does nothing without polling
            # A delay in the while loop is introduced by the select method below
            if playtime_instance[k].livestreamer_process.returncode is not None:
                if playtime_instance[k].livestreamer_process.returncode == 1:
                    stream_error = playtime_instance[k].livestreamer_process.stdout.read().decode('utf-8').split('\n')
                    error_message = [er for er in stream_error if 'error:' in er]

                    # This hack is needed because the Twitch API does not give quality settings
                    # We move on to the alternate quality settings specified in the Options class
                    # OR we error out. It's a good day to die.
                    if error_message[0][:30] == 'error: The specified stream(s)' and playtime_instance[k].alternate_quality_tried is False:
                        playtime_instance[k].livestreamer_process = subprocess.Popen(
                            playtime_instance[k].args_to_subprocess_alternate, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                        playtime_instance[k].alternate_quality_tried = True
                    else:
                        print(' ' + Colors.RED + playtime_instance[k].display_name + Colors.ENDC + ' (' + error_message[0] + ')')
                        database.execute("DELETE FROM miscellaneous WHERE Name = '{0}'".format(playtime_instance[k].display_name))
                        database.commit()
                        playing_streams.remove(k)
                else:
                    playtime_instance[k].time_tracking()
                    playing_streams.remove(k)
        try:
            keypress, o, e = select.select([sys.stdin], [], [], 0.8)
            if keypress:
                keypress_made = sys.stdin.readline().strip()
                if keypress_made == "q":
                    raise KeyboardInterrupt
        except KeyboardInterrupt:
            for k in playing_streams:
                playtime_instance[k].time_tracking()
                playtime_instance[k].livestreamer_process.terminate()
            playing_streams.clear()


# Update the script to the latest git revision
def update_script():
    print(' ' + Options.colors['numbers'] + 'Checking for update...' + Colors.ENDC)
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
            # Monitor
            print('(M) ' + play_status[0][1])
        else:
            # Any channels being watched
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
        remove(config_path)
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
    parser.add_argument('-v', type=str, nargs=1, help='Watch VODs', metavar='<channel>')
    parser.add_argument('-w', type=str, nargs='+', help='Watch specified channel(s)', metavar='<channel>')
    args = parser.parse_args()

    if (args.s or args.v) and args.searchfor:
        parser.error('Only one argument allowed with -s and -v')
        exit()

    # Relevant inputs below have been converted to lower case as per their type
    if args.a:
        args.a = [lc_args.lower() for lc_args in args.a]
        add_to_database(args.a, 'a')

    elif args.an:
        if args.an != 'BlankForAllIntensivePurposes':
            args.an = args.an.lower()
        read_modify_deletefrom_database(args.an, 'CantTouchThis', 'an')

    elif args.configure:
        configure_options()

    elif args.conky:
        firefly_needed_another_6_seasons(args.conky)

    elif args.d:
        if args.d != 'BlankForAllIntensivePurposes':
            args.d = args.d.lower()
        read_modify_deletefrom_database(args.d, 'CantTouchThis', 'd')

    elif args.f:
        watch(None, 'f')

    elif args.n:
        if args.n != 'BlankForAllIntensivePurposes':
            args.n = args.n.lower()
        read_modify_deletefrom_database(args.n, 'ItsHammerTime', 'n')

    elif args.reset:
        nuke_it_from_orbit()

    elif args.s:
        args.s = [lc_args.lower() for lc_args in args.s]
        add_to_database(args.s, 's')

    elif args.update:
        update_script()

    elif args.v:
        args.v = [lc_args.lower() for lc_args in args.v]
        vod_watch(args.v)

    elif args.w:
        args.w = [lc_args.lower() for lc_args in args.w]
        watch(args.w, 'w')

    elif args.searchfor:
        args.searchfor = args.searchfor.lower()
        watch(args.searchfor, 'search')

    else:
        watch(None, '')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        thatsallfolks()
