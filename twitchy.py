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

from twitchy_config import Colors

from pprint import pprint

twitchy_database.DatabaseInit()
twitchy_config.ConfigInit()

Options = twitchy_config.Options()

# In case of addition, all that needs to be done is pass
# the name of the channel to the api module
# Acutal addition to the database is carried out by the
# relevant function in the aforementioned module

def channel_addition(option, channels):
    # option is either 'add' for -a
    # OR 'sync' for -s
    # -s accepts only a string
    # TODO Respond to the datatype of channels after writing main()
    # Everything is converted to lowercase in the relevant function

    print(' ' + Colors.YELLOW + 'Additions to database:' + Colors.ENDC)

    if option == 'add':
        valid_channels = twitchy_api.add_to_database(channels)
    elif option == 'sync':
        valid_channels = twitchy_api.sync_from_id(channels)

    if not valid_channels:
        print(Colors.RED + ' No valid channels found' + Colors.ENDC)
        exit(1)

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
        database_search)

    # We're going to change it into a dictionary using
    # the black magic fuckery that is dictionary comprehension
    # channel_data_dict is then passed to the table generation function
    channel_data_dict = {i[0]: dict(timewatched=i[1], alt_name=i[2]) for i in channel_data}
    pprint(channel_data_dict)

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
        database_search)

    id_string_list = [str(i[0]) for i in channel_data]
    channels_online = twitchy_api.GetOnlineStatus(id_string_list).check_channels()
    final_selection = twitchy_display.GenerateTable(channels_online).watch()
    pprint(final_selection)

watch_channel()
