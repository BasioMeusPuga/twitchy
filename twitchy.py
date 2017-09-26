#!/bin/env python
# Requirements: streamlink, requests

""" TODO:
    ✓ Switch to v5 of the API
    ✓ Try not to have anything here except code that displays shit
    ✓ Switch to explicit imports instead of from * import *
    ✓ Explicit exception naming
    ✓ Shift to string literals: Python 3.6 and above
    ✓ Shift to the new quality settings as the default
    Alternate color coding
    Look up packaging
    Implement a proper non interactive mode
    Start channel without confirmation when in non interactive mode
    x Debug logging - Make this a switch
    x Use the streamlink module instead of subprocess
"""

# Standard imports
import sys
import argparse

# Custom imports
import twitchy_api
import twitchy_config  # This import also creates the path
from twitchy_config import Colors
import twitchy_display
import twitchy_database
import twitchy_play

twitchy_database.DatabaseInit()
twitchy_config.ConfigInit()

# All database functions are an attribute of database_instance
database_instance = twitchy_database.DatabaseFunctions()

Options = twitchy_config.Options()
Options.parse_options()

# Exit if version requirements are not met
if sys.version_info < (3, 6):
    print(Colors.RED + ' Python 3.6 or greater required.' + Colors.ENDC)
    exit()


def channel_addition(option, channels):
    # option is either 'add' for -a
    # -a expects a list
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
    if not added_channels:
        print(Colors.RED + ' No valid channels found' + Colors.ENDC)
        exit(1)


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

    channel_data = database_instance.fetch_data(
        ('Name', 'TimeWatched', 'AltName'),
        table_wanted,
        database_search,
        'LIKE')

    if not channel_data:
        print(
            Colors.RED + ' No matching records.' + Colors.ENDC)
        exit(1)

    final_selection = twitchy_display.GenerateDatabaseTable(
        channel_data, table_wanted).begin()

    if option == 'delete':
        yes_default = ['y', 'Y', 'yes', 'YES']
        confirmed_deletions = []
        for i in final_selection:
            confirm_delete = input(
                f' Delete {Colors.YELLOW + i + Colors.ENDC} (y/N) ')

            if confirm_delete in yes_default:
                confirmed_deletions.append(i)
                database_instance.modify_data(
                    'delete',
                    table_wanted,
                    i)

        if confirmed_deletions:
            print(
                ' Deleted: ' +
                Colors.RED + ', '.join(confirmed_deletions) +
                Colors.ENDC)

    elif option == 'alternate_name':
        for i in final_selection:
            new_name = input(
                f' Alternate name for {Colors.YELLOW + i + Colors.ENDC} ')
            criteria_dict = {
                'old_name': i,
                'new_name': new_name}

            database_instance.modify_data(
                'alternate_name',
                table_wanted,
                criteria_dict)


def watch_channel(option=None, database_search=None):
    # TODO
    # Option is either 'watch' for -w
    # 'favorites' for -f
    # OR None for no special case

    if database_search:
        database_search = {
            'Name': database_search,
            'AltName': database_search}

    channel_data = database_instance.fetch_data(
        ('ChannelID',),
        'channels',
        database_search,
        'LIKE')

    id_string_list = [str(i[0]) for i in channel_data]
    print(' ' + Options.colors.numbers +
          f'Checking {len(id_string_list)} channel(s)...' +
          Colors.ENDC)
    channels_online = twitchy_api.GetOnlineStatus(id_string_list).check_channels()
    if not channels_online:
        print(
            Colors.RED + ' All channels offline' + Colors.ENDC)
        exit()

    final_selection = twitchy_display.GenerateWatchTable(
        channels_online).begin()
    twitchy_play.play_instance_generator(final_selection)


def non_interactive(mode=None):
    # mode is None in case data is required about the currently playing channel
    # or 'get_online' to get a list of online channels
    # or 'kick_start' to skip selection and just pass the channel name to the
    # play module

    if mode == 'get_online':
        # Prints game name, channel_name for all channels found online in the
        # database
        channel_data = database_instance.fetch_data(
            ('ChannelID',),
            'channels',
            None,
            'LIKE')

        id_string_list = [str(i[0]) for i in channel_data]
        channels_online = twitchy_api.GetOnlineStatus(id_string_list).check_channels()

        # All standard channel parameters are available
        return_list = []
        for i in channels_online.items():
            return_list.append([
                i[1]['game'], i[0], i[1]['display_name']])

        return_list.sort()
        for i in return_list:
            print(','.join(i))


# non_interactive('get_online')
def main():
    parser = argparse.ArgumentParser(
        description='Watch twitch.tv from your terminal. IT\'S THE FUTURE.', add_help=False)

    parser.add_argument(
        'searchfor', type=str, nargs='?',
        help='Search for channel name in database', metavar='*searchstring*')

    parser.add_argument(
        '-h', '--help',
        help='This helpful message', action='help')

    parser.add_argument(
        '-a', type=str, nargs='+', help='Add channel name(s) to database', metavar='')

    parser.add_argument(
        '-an', type=str, nargs='?', const='Null',
        help='Set/Unset alternate names', metavar='*searchstring*')

    parser.add_argument(
        '--configure', action='store_true', help='Configure options')

    parser.add_argument(
        '-d', type=str, nargs='?', const='Null',
        help='Delete channel(s) from database', metavar='*searchstring*')

    parser.add_argument(
        '--reset', action='store_true', help='Start over')

    parser.add_argument(
        '-s', type=str,
        help='Sync username\'s followed accounts to local database', metavar='username')

    args = parser.parse_args()

    if args.s and args.searchfor:
        parser.error('Only one argument allowed with -s and -v')
        exit(1)

    if args.a:
        channel_addition('add', args.a)

    elif args.an:
        arg = args.an
        if args.an == 'Null':
            arg = None
        database_modification('alternate_name', arg)

    elif args.configure:
        twitchy_config.ConfigInit().configure_options()

    elif args.d:
        arg = args.d
        if args.d == 'Null':
            arg = None
        database_modification('delete', arg)

    elif args.reset:
        pass

    elif args.s:
        channel_addition('sync', args.s)

    elif args.searchfor:
        watch_channel(None, args.searchfor)

    else:
        watch_channel()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
