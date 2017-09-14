#!/usr/bin/env python3

import datetime

from pprint import pprint
from twitchy_config import Colors

try:
    import requests
except ImportError:
    print(Colors.RED + ' requests not installed. Exiting.' + Colors.ENDC)
    exit(1)


def api_call(url, arguments=None):
    try:
        headers = {
            'Accept': 'application/vnd.twitchtv.v5+json',
            'Client-ID': 'guulhcvqo9djhuyhb2vi56wqnglc351'}

        params = None
        if arguments:
            params = (('login', ','.join(arguments)),)

        r = requests.get(
            url,
            headers=headers,
            params=params)

        return r.json()

    except requests.exceptions.ConnectionError:
        print(Colors.RED + ' Unable to connect to Twitch.' + Colors.ENDC)
        exit(1)


def get_id(channels):
    # channels is expected to be a list

    # All API calls are now based on the presence of
    # an _id field. This needs to be derived first
    # if only the username is present
    id_dict = {}

    api_endpoint = 'https://api.twitch.tv/kraken/users'
    stream_data = api_call(
        api_endpoint,
        channels)

    for i in stream_data['users']:
        id_dict[i['name']] = i['_id']

    return id_dict

# ___ Everything above this is called by everything below this ___
# Don't touch anything above this


def add_to_database(channels):
    # channels is expected to be a list in lowercase
    channels = [i.lower() for i in channels]
    api_response = get_id(channels)

    valid_channels = []
    for i in channels:
        if i in api_response.keys():
            valid_channels.append((i, api_response[i]))
        else:
            # TODO - issue a proper error
            print(i + ' Not found')

    # valid_channels is a list
    # It contains tuples which contain the name of
    # the requisite channel, as well as the
    # corresponding channel_id
    return valid_channels


def sync_from_id(username):
    # username is expected to be a string in lowecase
    # Make sure this is set in the initiating function

    username_id = get_id([username.lower()])
    if username_id:
        username_id = username_id[username]
    else:
        # In case no id is returned by get_id
        return

    # Get total number of followed channels
    api_endpoint = f'https://api.twitch.tv/kraken/users/{username_id}/follows/channels'
    stream_data = api_call(
        api_endpoint)
    total_followed = stream_data['_total']

    # Redo the entire sync with the total number
    # of channels in mind
    offset = 0
    valid_channels = []
    while total_followed > 0:
        api_endpoint = (
            f'https://api.twitch.tv/kraken/users/{username_id}/follows/channels'
            f'?limit=100&offset={offset}')
        stream_data = api_call(
            api_endpoint)
        total_followed -= 100
        offset += 100

        for i in stream_data['follows']:
            valid_channels.append((
                i['channel']['name'],
                i['channel']['_id']))

    # Same as the valid_channels list in case of the
    # add_to_database function
    return valid_channels

# pprint(sync_from_id('cohhcarnage'))

class GetOnlineStatus:
    def __init__(self, channels):
        # Again, channels is expected to be a list
        # containing the _id as a string
        # More than 100 channels will be paginated
        self.channels = channels
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


    def check_channels(self):
        # The API imposes an upper limit of 100 channels
        # checked at once. Pagination is required, as usual.
        while self.channels:
            channel_checklist = ','.join(self.channels[:100])
            del self.channels[:100]
            api_endpoint = (
                f'https://api.twitch.tv/kraken/streams/?limit=100&channel={channel_checklist}')
            stream_data = api_call(
                api_endpoint)

            # The stream data dictionary is
            # Key: name
            # Value: as below
            # Partner status will have to come from another endpoint
            # Time watched is a database function - See if it
            # needs to be integrated here
            for i in stream_data['streams']:
                self.online_channels[i['channel']['name']] = {
                    'game': i['game'],
                    'status': i['channel']['status'],
                    'viewers': i['viewers'],
                    'display_name': i['channel']['display_name'],
                    'uptime': self.parse_uptime(i['created_at'])}


# channels = GetOnlineStatus(['22588033', '26610234'])
# channels.check_channels()
# pprint(channels.online_channels)
