#!/usr/bin/env python3
# Database manipulation module

import os
import sqlite3

from twitchy import twitchy_api
from twitchy.twitchy_config import Colors, YouAndTheHorseYouRodeInOn

location_prefix = os.path.expanduser('~') + '/.config/twitchy3/'


class DatabaseInit:
    def __init__(self):
        self.database_path = location_prefix + 'twitchy.db'
        self.database_path_old = os.path.expanduser('~') + '/.config/twitchy/twitchy.db'

        if is_test():
            return

        if not os.path.exists(self.database_path):
            if not os.path.exists(self.database_path_old):
                print(
                    Colors.CYAN +
                    ' Creating database: Add channels with -a or -s' +
                    Colors.ENDC)
                self.create_database()
                exit()
            else:
                print(
                    Colors.CYAN +
                    ' Found old database. Rebuilding from existing values.' +
                    Colors.ENDC)
                self.create_database()
                self.rebuild_database()
                exit()

    def create_database(self):
        database = sqlite3.connect(self.database_path)

        database.execute(
            "CREATE TABLE channels \
            (id INTEGER PRIMARY KEY, Name TEXT, ChannelID INTEGER, TimeWatched INTEGER,\
            DisplayName TEXT, AltName TEXT, IsPartner TEXT)")
        database.execute(
            "CREATE TABLE games \
            (id INTEGER PRIMARY KEY, Name TEXT, GameID INTEGER, TimeWatched INTEGER,\
            AltName TEXT)")

    def rebuild_database(self):
        database_new = sqlite3.connect(self.database_path)
        database_new.execute(f"ATTACH '{self.database_path_old}' as DBOLD")

        # Copy the channels and games tables
        for i in ['games', 'channels']:
            database_new.execute(
                f"INSERT INTO main.{i} (Name,TimeWatched,AltName) "
                f"SELECT Name,TimeWatched,AltName FROM DBOLD.{i}")
        database_new.commit()

        # Iterate over the new tables and fill in missing values
        def fill_in_the_blanks(table):
            name_data = database_new.execute(f"SELECT Name FROM {table}").fetchall()
            valid_entries = twitchy_api.name_id_translate(table, 'id_from_name', name_data)

            if table == 'games':
                # In this case, valid_entries is a list
                # that contains 2 entires
                # 0 is the id number
                # 1 is the game name
                for i in valid_entries:
                    game_id = i[0]
                    game_name = i[1]
                    sql_command = (
                        f"UPDATE games SET GameID = '{game_id}' WHERE Name = '{game_name}'")
                    database_new.execute(sql_command)

                database_new.execute(
                    f"DELETE FROM games WHERE GameID is NULL")

            elif table == 'channels':
                # In this case, valid_entires is a dictionary
                # That contains broadcaster_type, display_name, and id
                # couples to each channel name
                for i in valid_entries.items():
                    channel_name = i[0]
                    display_name = i[1]['display_name']
                    channel_id = i[1]['id']
                    is_partner = False
                    if i[1]['broadcaster_type'] == 'partner':
                        is_partner = True

                    sql_command = (
                        f"UPDATE channels SET "
                        f"ChannelID = '{channel_id}', DisplayName = '{display_name}', "
                        f"IsPartner = '{is_partner}' "
                        f"WHERE Name = '{channel_name}'")
                    database_new.execute(sql_command)

                database_new.execute(
                    f"DELETE FROM channels WHERE ChannelID is NULL")

            database_new.commit()

        fill_in_the_blanks('channels')
        fill_in_the_blanks('games')

    def remove_database(self):
        os.remove(self.database_path)


class DatabaseFunctions:
    def __init__(self):
        if is_test():
            return

        self.database_path = location_prefix + 'twitchy.db'
        self.database = sqlite3.connect(self.database_path)

    def add_channels(self, data):
        # Used for -a and -s
        # That's addition and syncing
        # data is a dictionary that will be iterated upon
        added_channels = []
        for channel_data in data.items():

            channel_name = channel_data[0]
            channel_id = channel_data[1]['id']
            display_name = channel_data[1]['display_name']
            is_partner = True
            if channel_data[1]['broadcaster_type'] != 'partner':
                is_partner = False

            sql_command_exist = f"SELECT Name FROM channels WHERE Name = '{channel_name}'"
            does_it_exist = self.database.execute(
                sql_command_exist).fetchone()

            if not does_it_exist:
                sql_command_add = (
                    f"INSERT INTO channels "
                    f"(Name,ChannelID,TimeWatched,DisplayName,IsPartner) VALUES "
                    f"('{channel_name}',{channel_id},0,'{display_name}','{is_partner}')")

                self.database.execute(sql_command_add)
                added_channels.append(channel_name)

        self.database.commit()
        return added_channels

    def add_games(self, game_name, game_id):
        # Used for addition of a game that is seen at initial listing
        # Does not need to return anything
        # Checking is no longer required either because it is now
        # taken care of in the twitchy_api module
        sql_command_add = (
            f"INSERT INTO games (Name,GameID,Timewatched) VALUES ('{game_name}',{game_id},0)")
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
        sql_commands = []

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

            sql_commands.append(
                f"UPDATE {table} SET AltName = {new_name} WHERE Name = '{old_name}'")

        if mode == 'delete':
            # In this case, criteria is a single string
            sql_commands.append(
                f"DELETE FROM {table} WHERE Name = '{criteria}'")

        if mode == 'update_time':
            # In this case, criteria is expected to be a dictionary containing
            # the new time_watched values for both the channel and the game
            # Therefore, table is None
            channel_name = criteria['channel_name']
            channel_time = criteria['new_time_channel']
            game_name = criteria['game_name']
            game_time = criteria['new_time_game']

            sql_commands.append(
                f"UPDATE channels SET TimeWatched = {channel_time} WHERE Name = '{channel_name}'")
            sql_commands.append(
                f"UPDATE games SET TimeWatched = {game_time} WHERE Name = '{game_name}'")

        for i in sql_commands:
            self.database.execute(i)
        self.database.commit()
        self.database.execute('VACUUM')


def is_test():
    config_path = location_prefix + os.sep + 'twitchy.cfg'
    with open(config_path) as current_config:
        first_line = current_config.readlines()[0]

    if first_line == '# TEST CONFIG FILE\n':
        return True
    return False
