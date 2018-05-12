#!/usr/bin/env python3
# Twitch API interaction module

import os
import ast
import time
import datetime

from twitchy import twitchy_database
from twitchy.twitchy_config import YouAndTheHorseYouRodeInOn, location_prefix, Options

Options = Options()
Options.parse_options()

try:
    import requests
except ImportError:
    raise YouAndTheHorseYouRodeInOn(' requests not installed.')


def api_call(url, params=None):
    try:
        headers = {
            'Client-ID': 'guulhcvqo9djhuyhb2vi56wqnglc351'}

        def make_request():
            r = requests.get(
                url,
                headers=headers,
                params=params)

            my_json = r.json()

            try:
                status = my_json['status']
                if status == 429:
                    # Wait for 2 seconds in case of an API overload
                    # Hopefully the recursion doesn't end the universe
                    time.sleep(2)
                    make_request()
            except KeyError:
                return my_json

        return make_request()

    except requests.exceptions.ConnectionError:
        raise YouAndTheHorseYouRodeInOn(' Unable to connect to Twitch.')


def name_id_translate(data_type, mode, data):
    # data is expected to be a list
    # data_type is either 'games' or 'channels'

    # All API calls are now based on the presence of
    # an id field. This needs to be derived first

    # The new API also returns the display_name value here
    # in case of channel names
    # This will have to be cached in the database

    # Returns a dictionary

    # Set the default value for params
    # This is for 'name_from_id'
    # for either data_type
    params = (('id', data),)

    if data_type == 'games':
        api_endpoint = 'https://api.twitch.tv/helix/games'
        if mode == 'id_from_name':
            params = (('name', data),)

    elif data_type == 'channels':
        api_endpoint = 'https://api.twitch.tv/helix/users'
        if mode == 'id_from_name':
            if len(data) > 1:
                data = [i[0].lower() for i in data]
            params = (('login', data),)

    stream_data = api_call(
        api_endpoint,
        params)

    if data_type == 'channels':
        return_dict = {}

        for i in stream_data['data']:
            channel_params = {
                'id': i['id'],
                'broadcaster_type': i['broadcaster_type'],
                'display_name': i['display_name'],
                'profile_image_url': i['profile_image_url']}

            return_dict[i['login']] = channel_params

        return return_dict

    if data_type == 'games':
        return_list = []

        for i in stream_data['data']:
            game_params = {
                'id': i['id'],
                'name': i['name']}

            return_list.append(
                [game_params['id'], game_params['name']])

        return return_list


def sync_from_id(username):
    # username is expected to be a string in lowecase
    # Make sure this is set in the initiating function
    # Example: sync_from_id('<username>')
    followed_channels = {}

    username_id = name_id_translate(
        'channels', 'id_from_name', [username.lower()])
    if username_id:
        username_id = username_id[username]['id']
    else:
        # In case no id is returned by name_id_translate
        return

    followed_channels_ids = []
    params = (
        ('from_id', username_id),
        ('first', 100))
    while True:
        results_expected = 100
        api_endpoint = 'https://api.twitch.tv/helix/users/follows'

        stream_data = api_call(
            api_endpoint,
            params)

        followed_channels_ids = [i['to_id'] for i in stream_data['data']]
        if not followed_channels_ids:
            return

        # Since we're nesting these API calls, no separate pagination is
        # required
        followed_channels_returned_dict = name_id_translate(
            'channels', 'name_from_id', followed_channels_ids)

        for i in followed_channels_returned_dict.items():
            followed_channels[i[0]] = i[1]

        results_acquired = len(stream_data['data'])
        if results_acquired < results_expected:
            break
        else:
            params = (
                ('from_id', username_id),
                ('first', 100),
                ('after', stream_data['pagination']['cursor']))

    return followed_channels


def get_vods(channel_id):
    # Returns a list of VODS
    # Only the first 100 will ever be queried
    # so no need for pagination here

    params = (
        ('user_id', channel_id),
        ('first', 100))
    api_endpoint = 'https://api.twitch.tv/helix/videos'

    vod_data = api_call(
        api_endpoint,
        params)

    return_list = []
    # Since the API returns a list of videos that are sorted
    # by date, additional sorting isn't required
    # All that is needed is conversion of the TZ string into
    # its corresponding date
    for i in vod_data['data']:
        creation_time = datetime.datetime.strptime(
            i['created_at'],
            '%Y-%m-%dT%H:%M:%SZ')

        creation_date = creation_time.strftime('%d %B %Y')

        vod_title = i['title'].replace('\n', '')
        if len(vod_title) > Options.display.truncate_status:
            vod_title = vod_title[:Options.display.truncate_status] + '...'

        return_list.append([
            creation_date,
            vod_title,
            i['url']])

    return_list = return_list[::-1]
    return return_list


def get_profile_image(channel_names):
    # channel_names is a list

    # Download the profile image (logo) of the channel
    # This is currently only for the albert plugin
    # If this function is being called, assume the
    # requisite image does not exist and query for it
    # from the API

    link_dict = {}
    while channel_names:
        followed_channels_returned_dict = name_id_translate(
            'channels', 'id_from_name', [channel_names[:100]])

        for i in followed_channels_returned_dict.items():
            link_dict[i[0]] = i[1]['profile_image_url']

        del channel_names[:100]

    for i in link_dict.items():
        image_path = location_prefix + 'images/' + i[0]
        r = requests.get(i[1], stream=True)
        with open(image_path, 'wb') as image_file:
            for chunk in r.iter_content(1024):
                image_file.write(chunk)


class GetOnlineStatus:
    def __init__(self, channels):
        # Again, channels is expected to be a tuple
        # containing the _id as a string
        # More than 100 channels will be paginated
        # Example:
        # channels = GetOnlineStatus(['22588033', '26610234'])
        # channels.check_channels()
        # print(channels.online_channels)
        self.channels = channels
        self.no_profile_images = []
        self.online_channels = {}

    def parse_uptime(self, start_time):
        # Uptime is returned in seconds
        # We'll be using twitchy_display.time_convert()
        # to... convert this into what will be
        # displayed according to the sort order
        datetime_start_time = datetime.datetime.strptime(
            start_time,
            '%Y-%m-%dT%H:%M:%SZ')
        stream_uptime_seconds = (
            datetime.datetime.utcnow() -
            datetime_start_time).seconds

        return stream_uptime_seconds

    def get_game(self, game_id):
        # The game_id is expected to be an integer
        # The idea is to check the database for said integer
        # and return data accordingly
        # If nothing is found, create a new entry within the database
        # and put them newly discovered details here
        # Whoever thought of 2 endpoints for this
        # can walk on broken glass
        try:
            game_name = twitchy_database.DatabaseFunctions().fetch_data(
                ('Name', 'AltName'),
                'games',
                {'GameID': game_id},
                'EQUALS')[0]
            return game_name
        except TypeError:
            # Implies the game is not in the database
            # Its name will have to be fetched from the API
            # It will then be added to the database to prevent
            # repeated API calls
            # This means that all games EVER seen will be in the database now
            # Fuck whoever thought of this
            try:
                game_details = name_id_translate('games', 'name_from_id', (game_id,))
                game_name = game_details[0][1].replace("'", "")
                twitchy_database.DatabaseFunctions().add_games(game_name, game_id)
                return (game_name, None)
            except IndexError:
                # In the event the streamer gets lazy and does not set a game
                return ('No game set', None)

    def check_channels(self):
        # The API imposes an upper limit of 100 channels
        # checked at once. Pagination is required, as usual.
        while self.channels:
            api_endpoint = 'https://api.twitch.tv/helix/streams'

            params = (
                ('first', 100),
                ('user_id', self.channels[:100]))

            del self.channels[:100]
            stream_data = api_call(
                api_endpoint,
                params)

            # The API currently does NOT return the game_name
            # It does return a game_id. In case you intend to go
            # forward with that at this time, the game_id will have
            # to be cached in the database along with its name

            # The stream data dictionary is
            # Key: name
            # Value: as below
            # Partner status will have to come from another endpoint
            # Time watched is a database function - See if it
            # needs to be integrated here

            for i in stream_data['data']:

                user_id = i['user_id']
                try:
                    channel_details = twitchy_database.DatabaseFunctions().fetch_data(
                        ('Name', 'DisplayName', 'AltName', 'IsPartner'),
                        'channels',
                        {'ChannelID': user_id},
                        'EQUALS')[0]

                    channel_name = channel_details[0]
                    # Set the display name to a preset AltName if possible
                    # Or go back to the display name set by the channel
                    channel_display_name = channel_details[2]
                    if not channel_display_name:
                        channel_display_name = channel_details[1]

                    # Partner status is returned as string True
                    # This is clearly unacceptable for anyone who
                    # doesn't sleep in a dumpster
                    is_partner = ast.literal_eval(channel_details[3])

                    # Download images in case they aren't found
                    # No extension is needed
                    # Will only really be slow the first time
                    profile_image = location_prefix + 'images/' + channel_name
                    if not os.path.exists(profile_image):
                        self.no_profile_images.append(channel_name)

                except TypeError:
                    # Implies that the channel is not present in the database
                    # and its details will have to be queried from the API
                    # This should only get triggered in case of -w
                    # This will *really* slow down if multiple non database channels
                    # are put into -w since all of them are checked individually
                    # A pox upon thee, Twitch API developers
                    channel_details = name_id_translate(
                        'channels', 'name_from_id', [user_id])

                    for j in channel_details.items():
                        channel_name = j[0]
                        channel_display_name = j[1]['display_name']
                        is_partner = False
                        if j[1]['broadcaster_type'] == 'partner':
                            is_partner = True

                uptime = self.parse_uptime(i['started_at'])

                # Game name and any alternate names will have to be correlated
                # to the game_id that's returned by the API
                # Whoever thought this was a good idea can sit on it and rotate

                game_id = i['game_id']
                if not game_id or game_id == '':
                    game_name = game_display_name = 'IDK'
                else:
                    game_data = self.get_game(game_id)
                    game_name = game_display_name = game_data[0]
                    if game_data[1]:
                        game_display_name = game_data[1]

                self.online_channels[channel_name] = {
                    'game': game_name,
                    'game_id': game_id,
                    'game_display_name': game_display_name,
                    'status': i['title'].replace('\n', ''),
                    'viewers': i['viewer_count'],
                    'display_name': channel_display_name,
                    'uptime': uptime,
                    'is_partner': is_partner}

        get_profile_image(self.no_profile_images)
        return self.online_channels
