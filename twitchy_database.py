#!/usr/bin/env python3
# Database manipulation module

import os
import sqlite3

from twitchy_config import Colors, YouAndTheHorseYouRodeInOn

location_prefix = os.path.expanduser('~') + '/.config/twitchy3/'


class DatabaseInit:
    def __init__(self):
        self.database_path = location_prefix + 'twitchy.db'
        if not os.path.exists(self.database_path):
            print(Colors.CYAN +
                  ' Creating database: Add channels with -a or -s' +
                  Colors.ENDC)
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

    def add_games(self, game_name):
        # Used for addition of a game that is started in the play module
        # Does not need to return anything
        sql_command_exist = f"SELECT Name FROM games WHERE Name = '{game_name}'"
        does_it_exist = self.database.execute(
            sql_command_exist).fetchone()
        if not does_it_exist:
            sql_command_add = (
                f"INSERT INTO games (Name,Timewatched) VALUES ('{game_name}',0)")
            self.database.execute(sql_command_add)
            self.database.commit()

    def fetch_data(self, columns, table, selection_criteria, equivalence, fetch_one=False):
        # columns is a tuple that will be passed as a comma separated list
        # table is a string that will be used as is
        # selection_criteria is a dictionary which contains the name of a column linked
        # to a corresponding value for selection

        # Example:
        # Name and AltName are expected to be the same
        # sel_dict = {
        #     'Name': 'sav',
        #     'AltName': 'sav'
        # }
        # data = DatabaseFunctions().fetch_data(('Name',), 'channels', sel_dict)
        try:
            column_list = ','.join(columns)
            sql_command_fetch = f"SELECT {column_list} FROM {table}"
            if selection_criteria:
                sql_command_fetch += " WHERE"

                if equivalence == 'EQUALS':
                    for i in selection_criteria.keys():
                        search_parameter = selection_criteria[i]
                        sql_command_fetch += f" {i} = '{search_parameter}' OR"

                elif equivalence == 'LIKE':
                    for i in selection_criteria.keys():
                        search_parameter = "'%" + selection_criteria[i] + "%'"
                        sql_command_fetch += f" {i} LIKE {search_parameter} OR"

                sql_command_fetch = sql_command_fetch[:-3]  # Truncate the last OR

            # channel data is returned as a list of tuples
            channel_data = self.database.execute(sql_command_fetch).fetchall()

            if channel_data:
                # Because this is the result of a fetchall(), we need an
                # ugly hack (tm) to get correct results for anything that
                # isn't a database id search
                # This will cause issues in case someone wants to refer to
                # streamers and games as digits. We don't need that shit here.

                # Another consideration is returns for time watched
                # In that case, just go 0 of 0
                if fetch_one:
                    return channel_data[0][0]

                return channel_data
            else:
                return None

        except sqlite3.OperationalError:
            raise YouAndTheHorseYouRodeInOn(' Database error.')

    def modify_data(self, mode, table, criteria):
        if mode == 'alternate_name':
            # criteria in this case is expected to be a dictionary containing
            # new_name and old_name keys corresponding to their values
            old_name = criteria['old_name']
            new_name = criteria['new_name']
            if not new_name or new_name == '':
                # NULL is the sql equivalent of NoneType
                new_name = 'NULL'
            else:
                # Encapsulate in single quotes to form valid SQL
                new_name = f"'{new_name}'"

            sql_command = f"UPDATE {table} SET AltName = {new_name} WHERE Name = '{old_name}'"
            self.database.execute(sql_command)
            self.database.commit()

        if mode == 'delete':
            # In this case, criteria is a single string
            sql_command = f"DELETE FROM {table} WHERE Name = '{criteria}'"
            self.database.execute(sql_command)
            self.database.commit()

        if mode == 'update_time':
            # In this case, criteria is expected to be a dictionary containing
            # the new time_watched values for both the channel and the game
            # Therefore, table is None
            channel_name = criteria['channel_name']
            channel_time = criteria['new_time_channel']
            game_name = criteria['game_name']
            game_time = criteria['new_time_game']

            sql_command_channel = (
                f"UPDATE channels SET TimeWatched = {channel_time} WHERE Name = '{channel_name}'")
            self.database.execute(sql_command_channel)

            sql_command_game = (
                f"UPDATE games SET TimeWatched = {game_time} WHERE Name = '{game_name}'")
            self.database.execute(sql_command_game)
            self.database.commit()
