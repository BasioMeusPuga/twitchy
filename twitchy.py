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


twitchy_database.DatabaseInit()
twitchy_config.ConfigInit()

Options = twitchy_config.Options()

# In case of addition, all that needs to be done is pass
# the name of the channel to the api module
# Acutal addition to the database is carried out by the
# relevant function in the aforementioned module

def channel_addition(option, channels):
    # Common function for -s and -a
    # Channels is supposed to be a list
    # -s accepts only a string
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

def database_modification(database_search=None):
    # Common for -d, -an, and -n
    # That's deletion, alternate naming, and notifications

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

    # channel_data should now be passed to the function that generates tables
    # That belongs in the twitchy.py file

# database_modification('sav')
