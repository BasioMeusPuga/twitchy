#!/bin/env python
# Requirements: streamlink, requests

""" TODO:
    Look up packaging
    Debug logging - Make this a switch
    Switch to v5 of the API
    Alternate color coding
    Try not to have anything here except code that displays shit
    Use the livestreamer module instead of subprocess
    Switch to explicit imports instead of from * import *
    Explicit exception naming
    Shift to string literals: Python 3.6 and above
    Shift to the new quality settings as the default
"""

# Standard imports
import os

# Custom imports
import twitchy_api
import twitchy_config  # This import also creates the path
import twitchy_display
import twitchy_database
import twitchy_play

from twitchy_config import Colors

from pprint import pprint

twitchy_database.DatabaseInit()
twitchy_config.ConfigInit()

Options = twitchy_config.Options()
Options.parse_options()


def channel_addition(option, channels):
    # option is either 'add' for -a
    # OR 'sync' for -s
    # -s accepts only a string
    # TODO Respond to the datatype of channels after writing main()
    # Everything is converted to lowercase in the relevant function

    print(' ' + Colors.YELLOW + 'Additions to database:' + Colors.ENDC)

    # Get the numeric id of each channel that is to be added to the database
    if option == 'add':
        valid_channels = twitchy_api.add_to_database(channels)
    elif option == 'sync':
        valid_channels = twitchy_api.sync_from_id(channels)

    if not valid_channels:
        print(Colors.RED + ' No valid channels found' + Colors.ENDC)
        exit(1)

    # Actual addition to the database takes place here
    added_channels = twitchy_database.DatabaseFunctions().add_channels(valid_channels)
    for i in added_channels:
        print(' ' + i)

# channel_addition('add', ['hsdogdog', 'reynad27', 'AMAzHs', 'ajdk342m'])
# channel_addition('sync', 'cohhcarnage')


def database_modification(option, database_search=None):
    # option is either 'delete' for -d
    # OR 'alternate_name' for -an

    table_wanted = input(' Modify (s)treamer or (g)ame name? ')
    if table_wanted.lower() == 's':
        table_wanted = 'channels'
    elif table_wanted.lower() == 'g':
        table_wanted = 'games'

    if database_search:
        database_search = {
            'Name': database_search,
            'AltName': database_search}

    channel_data = twitchy_database.DatabaseFunctions().fetch_data(
        ('Name', 'TimeWatched', 'AltName'),
        table_wanted,
        database_search,
        'LIKE')

    final_selection = twitchy_display.GenerateTable(channel_data).database()

    if option == 'delete':
        yes_default = ['y', 'Y', 'yes', 'YES']
        for i in final_selection:
            confirm_delete = input(
                f' Delete {Colors.YELLOW + i + Colors.ENDC} ')

            if confirm_delete in yes_default:
                twitchy_database.DatabaseFunctions().modify_data(
                    'delete',
                    table_wanted,
                    i)

    elif option == 'alternate_name':
        for i in final_selection:
            new_name = input(
                f' Alternate name for {Colors.YELLOW + i + Colors.ENDC} ')
            criteria_dict = {
                'old_name': i,
                'new_name': new_name}

            twitchy_database.DatabaseFunctions().modify_data(
                'alternate_name',
                table_wanted,
                criteria_dict)

# database_modification('delete')
# database_modification('delete', 'fa')

def watch_channel(option=None, database_search=None):
    # Option is either 'watch' for -w
    # 'favorites' for -f
    # OR None for no special case

    if database_search:
        database_search = {
            'Name': database_search,
            'AltName': database_search}

    channel_data = twitchy_database.DatabaseFunctions().fetch_data(
        ('ChannelID',),
        'channels',
        database_search,
        'LIKE')

    id_string_list = [str(i[0]) for i in channel_data]
    print(' ' + Options.colors.numbers +
          f'Checking {len(id_string_list)} channels...' +
          Colors.ENDC)
    channels_online = twitchy_api.GetOnlineStatus(id_string_list).check_channels()
    final_selection = twitchy_display.GenerateTable(channels_online).online_channels()
    twitchy_play.play_instance_generator(final_selection)

#watch_channel(None, 'dog')
watch_channel()
