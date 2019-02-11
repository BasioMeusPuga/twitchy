#!/usr/bin/env python3
# Requirements: streamlink, requests

# Standard imports
import sys
import argparse

# Exit if version requirements are not met
if sys.version_info < (3, 6):
    print(' Python 3.6 or greater required.')
    exit(1)

# Custom imports
from twitchy import twitchy_config  # This import also creates the path
from twitchy.twitchy_config import Colors, YouAndTheHorseYouRodeInOn
twitchy_config.ConfigInit()

# Everything will error out unless
# both the config and the database files exist
from twitchy import twitchy_database
twitchy_database.DatabaseInit()

from twitchy import twitchy_api
from twitchy import twitchy_display
from twitchy import twitchy_play

# All database functions are methods in database_instance
database_instance = twitchy_database.DatabaseFunctions()

Options = twitchy_config.Options()
Options.parse_options()


def channel_addition(option, channels):
    # option is either 'add' for -a
    # -a expects a list
    # OR 'sync' for -s
    # -s accepts only a string
    # Everything is converted to lowercase in the relevant function

    print(' ' + Colors.YELLOW + 'Additions to database:' + Colors.ENDC)

    # Get the numeric id of each channel that is to be added to the database
    if option == 'add':
        valid_channels = twitchy_api.name_id_translate(
            'channels', 'id_from_name', [channels])
    elif option == 'sync':
        valid_channels = twitchy_api.sync_from_id(channels)

    if not valid_channels:
        raise YouAndTheHorseYouRodeInOn(' No valid channels.')

    # Actual addition to the database takes place here
    added_channels = twitchy_database.DatabaseFunctions().add_channels(
        valid_channels)

    if not added_channels:
        raise YouAndTheHorseYouRodeInOn(' No valid channels.')
    else:
        for i in added_channels:
            print(' ' + i)


def database_modification(option, database_search=None):
    # option is either 'delete' for -d
    # OR 'alternate_name' for -an

    try:
        table_wanted = input(' Modify (s)treamer or (g)ame name? ')
    except (KeyboardInterrupt, EOFError):
        exit(1)

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
        raise YouAndTheHorseYouRodeInOn(' No matching records.')

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


def watch_channel(mode, database_search=None):
    if mode == 'watch':
        # database_search is expected to be a list
        # exact names of the channels the user wants to watch

        # Watch times are NOT tracked with -w
        # This greatly decreases the number of special conditions
        # that need to be accounted for
        twitchy_config.time_tracking = False

        id_string_list = []
        not_in_database = []

        database_search = [i.lower() for i in database_search]
        for i in database_search:
            search_criteria = {
                'Name': i}

            channel_data = database_instance.fetch_data(
                ('ChannelID',),
                'channels',
                search_criteria,
                'EQUALS',
                True)

            if channel_data:
                # Channel data is expected as a string
                id_string_list.append(str(channel_data))
            else:
                not_in_database.append(i)

        if not_in_database:
            get_ids_from_api = twitchy_api.name_id_translate(
                'channels', 'id_from_name', [not_in_database])

            ids_only = [i[1]['id'] for i in get_ids_from_api.items()]
            id_string_list.extend(ids_only)

        if not id_string_list:
            raise YouAndTheHorseYouRodeInOn(' No valid channels.')

    else:
        # This is the standard watch() function
        # It expects only one argument
        if database_search:
            database_search = {
                'Name': database_search,
                'AltName': database_search}

        channel_data = database_instance.fetch_data(
            ('ChannelID',),
            'channels',
            database_search,
            'LIKE')

        if channel_data:
            id_string_list = [str(i[0]) for i in channel_data]
        else:
            raise YouAndTheHorseYouRodeInOn(' Database query returned nothing.')

    print(' ' + Options.colors.numbers +
          f'Checking {len(id_string_list)} channel(s)...' +
          Colors.ENDC)

    channels_online = twitchy_api.GetOnlineStatus(
        id_string_list).check_channels()
    if not channels_online:
        raise YouAndTheHorseYouRodeInOn(' All channels offline.')

    final_selection = twitchy_display.GenerateWatchTable(
        channels_online).begin()
    print(' q / Ctrl + C to quit \n Now watching:')
    twitchy_play.play_instance_generator(final_selection)


def watch_vods(channel_name):
    channel_data = twitchy_api.name_id_translate(
        'channels', 'id_from_name', [channel_name])

    try:
        channel_id = channel_data[channel_name[0]]['id']
        display_name = channel_data[channel_name[0]]['display_name']
    except KeyError:
        raise YouAndTheHorseYouRodeInOn(' Invalid name.')

    vod_list = twitchy_api.get_vods(channel_id)
    print(' ' + Options.colors.numbers +
          f'VODs for {display_name}:' +
          Colors.ENDC)

    if not vod_list:
        raise YouAndTheHorseYouRodeInOn(' No VODs found.')

    final_selection = {
        display_name: twitchy_display.GenerateVODTable(vod_list).begin()}
    twitchy_config.time_tracking = False
    twitchy_config.vod_mode = True

    print(' q / Ctrl + C to quit \n Now watching:')
    twitchy_play.play_instance_generator(final_selection)


def non_interactive(mode, channel_name=None, delimiter=None):
    if mode == 'get_online':
        # Output format:
        # Game name, Game display name (if present)...
        # Channel name, Channel display name (always present)
        channel_data = database_instance.fetch_data(
            ('ChannelID',),
            'channels',
            None,
            'LIKE')

        # Database is empty and no output must be issued
        if not channel_data:
            return

        id_string_list = [str(i[0]) for i in channel_data]
        channels_online = twitchy_api.GetOnlineStatus(
            id_string_list).check_channels()

        # All standard channel parameters are available
        for i in channels_online.items():
            return_list = []
            config_correlate = {
                'GameName': i[1]['game'],
                'GameAltName': str(i[1]['game_display_name']),
                'ChannelName': i[0],
                'ChannelAltName': i[1]['display_name'],
                'Status': i[1]['status'],
                'Viewers': str(i[1]['viewers']),
                'Uptime': twitchy_display.time_convert(i[1]['uptime'])}

            for j in Options.non_int_display_scheme:
                return_list.append(config_correlate[j])

            if delimiter is None:
                delimiter = Options.non_int_delimiter

            print(delimiter.join(return_list))

    if mode == 'kickstart':
        # Skip selection and just pass the channel name to the play module
        # All output is disabled except for error messages
        # Time tracking is disabled
        twitchy_config.print_to_stdout = False
        twitchy_config.time_tracking = False
        twitchy_config.non_interactive_mode = True

        if not channel_name:
            exit(1)

        try:
            api_reply = twitchy_api.name_id_translate(
                'channels', 'id_from_name', [channel_name])
            channel_id = api_reply[channel_name]['id']

            channel_status = twitchy_api.GetOnlineStatus(
                [channel_id]).check_channels()
            # The video is started in default quality
            channel_status[channel_name]['quality'] = Options.video.default_quality
            twitchy_play.play_instance_generator(channel_status)
        except KeyError:
            exit()


def nuke_it_from_orbit():
    print('Are you sure you want to remove the database and start over?')
    confirmation = Colors.RED + 'KappaKeepoPogChamp' + Colors.ENDC
    confirm = input(f'Please type {confirmation} to continue: ')
    if confirm == 'KappaKeepoPogChamp':
        twitchy_database.DatabaseInit().remove_database()
        twitchy_config.ConfigInit().remove_config()
        print(' Done.')


def main():
    parser = argparse.ArgumentParser(
        description='Watch twitch.tv from your terminal. IT\'S THE FUTURE.',
        add_help=False)

    parser.add_argument(
        'searchfor', type=str, nargs='?',
        help='Search for channel name in database',
        metavar='*searchstring*')

    parser.add_argument(
        '-h', '--help',
        help='This helpful message', action='help')

    parser.add_argument(
        '-a', type=str, nargs='+',
        help='Add channel name(s) to database',
        metavar='')

    parser.add_argument(
        '-an', type=str, nargs='?', const='Null',
        help='Set/Unset alternate names',
        metavar='*searchstring*')

    parser.add_argument(
        '--configure', action='store_true', help='Configure options')

    parser.add_argument(
        '-d', type=str, nargs='?', const='Null',
        help='Delete channel(s) from database',
        metavar='*searchstring*')

    parser.add_argument(
        '--hanselgretel', action='store_true', help='Abandon children')

    parser.add_argument(
        '--non-interactive', type=str, nargs='?',
        help='Generate parsable data for integration elsewhere',
        const='go',
        metavar='go / kickstart')

    parser.add_argument(
        '--delimiter', type=str, nargs='?', help=argparse.SUPPRESS)

    parser.add_argument(
        '--reset', action='store_true', help='Start over')

    parser.add_argument(
        '-s', type=str,
        help='Sync username\'s followed accounts to local database',
        metavar='username')

    parser.add_argument(
        '-v', type=str, nargs='+',
        help='Watch VODs',
        metavar='<channel>')

    parser.add_argument(
        '-w', type=str, nargs='+',
        help='Watch specified channel(s)',
        metavar='<channel>')

    args = parser.parse_args()

    if (args.s or args.v) and args.searchfor:
        parser.error('Only one argument allowed with -s')
        exit(1)

    if args.hanselgretel:
        twitchy_config.disown = True

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

    elif args.non_interactive:
        if args.non_interactive == 'go':
            non_interactive('get_online', delimiter=args.delimiter)
        elif args.non_interactive == 'kickstart':
            non_interactive('kickstart', args.searchfor)

    elif args.reset:
        nuke_it_from_orbit()

    elif args.s:
        channel_addition('sync', args.s)

    elif args.searchfor:
        watch_channel(None, args.searchfor)

    elif args.v:
        watch_vods(args.v)

    elif args.w:
        watch_channel('watch', args.w)

    else:
        watch_channel(None)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
