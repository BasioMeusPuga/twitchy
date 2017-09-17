#!/usr/bin/env python3
# Database manipulation module

import os
import sqlite3

import twitchy_api
from twitchy_config import Colors


location_prefix = os.path.expanduser('~') + '/.config/twitchy3/'


class DatabaseInit:
    def __init__(self):
        self.database_path = location_prefix + 'twitchy.db'
        if not os.path.exists(self.database_path):
            print(Colors.CYAN +
                  ' Creating database: Add channels with -a or -s' +
                  Colors.ENDC)
            print()
            self.create_database()


    def create_database(self):
        database = sqlite3.connect(self.database_path)

        database.execute(
            "CREATE TABLE channels \
            (id INTEGER PRIMARY KEY, Name TEXT, ChannelID INTEGER, TimeWatched INTEGER,\
            AltName TEXT)")
        database.execute(
            "CREATE TABLE games \
            (id INTEGER PRIMARY KEY, Name TEXT, TimeWatched INTEGER, AltName TEXT)")
        database.execute(
            "CREATE TABLE miscellaneous \
            (id INTEGER PRIMARY KEY, Name TEXT, Value TEXT)")


    def remove_database(self):
        os.remove(self.database_path)


class DatabaseFunctions:
    def __init__(self):
        self.database_path = location_prefix + 'twitchy.db'
        self.database = sqlite3.connect(self.database_path)

    def add_channels(self, data):
        # Used for -a and -s
        # That's addition and syncing
        # data is a list containing tuples

        added_channels = []
        for channel_data in data:
            channel_name = channel_data[0]
            channel_id = channel_data[1]

            sql_command_exist = f"SELECT Name FROM channels WHERE Name = '{channel_name}'"
            does_it_exist = self.database.execute(
                sql_command_exist).fetchone()
            if not does_it_exist:
                sql_command_add = (
                    f"INSERT INTO channels "
                    f"(Name,ChannelID,TimeWatched) VALUES ('{channel_name}',{channel_id},0)")
                self.database.execute(sql_command_add)
                added_channels.append(channel_name)

        self.database.commit()
        return added_channels

    def fetch_data(self, columns, table, selection_criteria=None):
        # columns is a tuple that will be passed as a comma separated list
        # table is a string that will be used as is
        # selection_criteria is a dictionary which contains the name of a column linked
        # to a corresponding value for selection

        column_list = ','.join(columns)
        sql_command_fetch = f"SELECT {column_list} FROM {table}"
        if selection_criteria:
            sql_command_fetch += " WHERE"
            for i in selection_criteria.keys():
                search_parameter = "'%" + selection_criteria[i] + "%'"
                sql_command_fetch += f" {i} LIKE {search_parameter} OR"
            sql_command_fetch = sql_command_fetch[:-3]  # Truncate the last OR

        # channel data is returned as a list of tuples
        channel_data = self.database.execute(sql_command_fetch).fetchall()
        return channel_data
# Name and AltName are expected to be the same
# sel_dict = {
#     'Name': 'sav',
#     'AltName': 'sav'
# }
# aa = DatabaseFunctions().fetch_data(('Name',), 'channels', sel_dict)
