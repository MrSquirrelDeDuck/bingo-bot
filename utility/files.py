"""Contains functions for loading and saving to files."""

import os
import datetime
import json
import typing
import traceback
from os.path import sep as SLASH
import copy

class DatabaseInterface:
    """Interface that deals with the database.
    
    An instance of this class should be set to an attribute of the bot so the cogs can use it."""

    database = {}

    def __init__(self) -> None:
        """Interface that deals with the database.
    
        An instance of this class should be set to an attribute of the bot so the cogs can use it."""
        self.load_database()
    
    def save_database(self, make_backup: bool = False) -> None:
        """Saves the database to database.json.

        Args:
            make_backup (bool, optional): Whether to make a backup of the database. Defaults to False.
        """
        print("Saving database.")
        self.save_json_file("database.json", self.database)

        if make_backup:
            self.make_backup()
    
    def make_backup(self) -> None:
        """Creates a backup of the database in the backup folder."""
        print("Making backup.")
        folder_path = "backups/"
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        file_name = (datetime.datetime.now().strftime('database_backup_%Y:%m:%d_%X.json')).replace(":", "-")
        print("Saving backup to " + folder_path + file_name)
        self.save_json_file(folder_path + file_name, self.database)
        print("Saved backup.")

        # Remove files beyond the last 196 backups.
        files = os.listdir(folder_path)
        files.sort(reverse=True)
        for file_name in files[196:]:
            print(f"Backup clearing. Removed {folder_path + file_name}")
            os.remove(folder_path + file_name)
    
    def load_database(self) -> None:
        """Loads the database from file.
        
        # This will overwrite the current stored database, so be careful."""
        print("Loading database.")
        self.database = self.load_json_file("database.json", default={})
    
    ######################################################################################################################################################
    ##### Getting and saving data ########################################################################################################################
    ######################################################################################################################################################
        
    def load(self: typing.Self, *keys: str, default: typing.Any = None) -> dict | list:
        """Returns a value from the database.

        Args:
            *keys (str): The key(s) to fetch. Provide multiple keys to get nested values. Example: `database.load('key', 'nested_key', 'double_nested_key')`
            default (typing.Any, optional): What to return if any key does not exist. Defaults to None.

        Returns:
            dict | list: The value from the database.
        """
        val = self.database.get(keys[0], default)

        try:
            for key in keys[1:]:
                val = val.get(key, default)
        except AttributeError:
            return default
        
        return copy.deepcopy(val)
    
    def save(self, *keys: str, data: dict | list) -> None:
        """Saves a dict or list to the database.

        Args:
            data (dict | list): The data to save.
            *keys (str): The key(s) of the path to save to. Provide multiple keys to save nested values. Example: `database.save('key', 'nested_key', 'double_nested_key', data=['example'])`
        """
        if len(keys) == 1:
            self.database[keys[0]] = data
            return

        val = self.database[keys[0]]

        for key in keys[1:-1]:
            val = val[key]
        
        val[keys[-1]] = data

    ######################################################################################################################################################
    ##### Dealing with files. ############################################################################################################################
    ######################################################################################################################################################

    def load_json_file(self,
            file_path: str,
            default: typing.Any = None,
            replace_slash: bool = False
        ) -> list | dict:
        """Loads a json file and returns the contents.

        Args:
            file_path (str): The path to the file.
            default (typing.Any, optional): The value to return if the file does not exist. Defaults to None.
            replace_slash (bool, optional): Whether to replace all slashes in the given path with os.path.sep. Defaults to False.

        Returns:
            list | dict: The contents of the file.
        """
        if replace_slash:
            file_path = file_path.replace("/", SLASH)

        try:
            with open(file_path, "r", encoding="utf8") as file_load:
                return json.load(file_load)
        except:
            return default
    
    def save_json_file(self,
            file_path: str,
            data: dict | list,
            replace_slash: bool = False
        ) -> None:
        """Saves a dict or list to a file. Will create the file if it doesn't exist.
        Will load the file before saving, and if there is an error while saving it will revert it.        

        Args:
            file_path (str): The path to the file to save.
            data (dict | list): The data to save.
            replace_slash (bool, optional): Whether to replace all slashes in the given path with os.path.sep. Defaults to False.
        """
        if replace_slash:
            file_path = file_path.replace("/", SLASH)

        backup = self.load_json_file(file_path, default=type(data)())

        with open(file_path, "w+") as file_write:
            try:
                json.dump(data, file_write, indent=4)
            except TypeError: # Likely an object that can't be saved via the json library.
                print(traceback.format_exc())
                json.dump(backup, file_write, indent=4)

    ######################################################################################################################################################
    ##### Daily counters. ################################################################################################################################
    ######################################################################################################################################################
    
    def get_daily_counter(self,
            counter_name: str,
            default: int = 0
        ) -> int:
        """Gets a daily counter from the daily counters section.

        Args:
            counter_name (str): The name of the counter to fetch.
            default (int, optional): What to return if the counter does not exist. Defaults to 0.

        Returns:
            int: The counter's current value.
        """
        return self.load("daily_counters", default=dict()).get(counter_name, default)
    
    def set_daily_counter(self,
            counter_name: str,
            value: int
        ) -> None:
        """Sets a daily counter in the daily counters section.

        Args:
            counter_name (str): The name of the counter to update.
            value (int): The value to set the counter to.
        """
        data = self.load("daily_counters", default=dict())

        data[counter_name] = value

        self.save("daily_counters", data=data)

    def increment_daily_counter(self,
            counter_name: str,
            amount: int = 1
        ) -> None:
        """Increments a daily counter by a specified amount.

        Args:
            counter_name (str): The name of the counter to increment.
            amount (int, optional): The amount to increment the counter by. Defaults to 1.
        """
        data = self.load("daily_counters", default=dict())

        data[counter_name] += amount

        self.save("daily_counters", data=data)


    ######################################################################################################################################################
    ##### Ping lists. ####################################################################################################################################
    ######################################################################################################################################################
    
    def get_ping_list_file(self) -> dict[str, list[typing.Optional[int]]]:
        """Returns the raw ping list data.

        Returns:
            dict[str, list[typing.Optional[int]]]: The raw ping list data.
        """
        return self.load("ping_lists")

    def set_ping_list_file(self,
            data: dict[str, list[typing.Optional[int]]]
        ) -> None:
        """Saves the raw ping list data.

        Args:
            data (dict[str, list[typing.Optional[int]]]): The full ping list data to save.
        """
        self.save("ping_lists", data=data)

    def get_ping_list(self,
            ping_list_name: str
        ) -> list[typing.Optional[int]]:
        """Gets a ping list from the ping list file.

        Args:
            ping_list_name (str): The key of the ping list.

        Returns:
            list[typing.Optional[int]]: A list of user ids that are on the ping list, or an empty list if the ping list does not exist (or nobody is on it :( )
        """
        ping_list_file = self.get_ping_list_file()

        if ping_list_name in ping_list_file:
            return ping_list_file[ping_list_name]
        
        return []

    def user_on_ping_list(self,
            ping_list_name: str,
            user_id: int
        ) -> bool:
        """Returns a boolean for whether a user is on a specific ping list.

        Args:
            ping_list_name (str): The name of the ping list to check.
            user_id (int): The id of the user to check.

        Returns:
            bool: Whether the user is on the ping list.
        """
        return user_id in self.get_ping_list_file().get(ping_list_name, [])

    def update_ping_list(self,
            ping_list_name: str,
            user_id: int,
            new_state: bool
        ) -> None:
        """Modifies the state of a ping list.

        Args:
            ping_list_name (str): The name of the ping list to modify.
            user_id (int): The id of the user to modify.
            new_state (bool): Whether the player should be on it, True for yes, False for no.
        """
        ping_list_file = self.get_ping_list_file()

        if ping_list_name not in ping_list_file:
            if new_state:
                ping_list_file[ping_list_name] = [user_id]
            else:
                ping_list_file[ping_list_name] = []

            self.set_ping_list_file(ping_list_file)
            return
        
        if new_state:
            if user_id in ping_list_file[ping_list_name]:
                return
            
            ping_list_file[ping_list_name].append(user_id)
            self.set_ping_list_file(ping_list_file)
            return
        
        if user_id not in ping_list_file[ping_list_name]:
            return
        
        ping_list_file[ping_list_name].remove(user_id)
        self.set_ping_list_file(ping_list_file)
        return
    
    ######################################################################################################################################################
    ##### AskOuija. ######################################################################################################################################
    ######################################################################################################################################################
    
    def get_ouija_data(self,
            channel_id: typing.Union[str, int]
        ) -> dict[str, typing.Union[str, int, bool]]:
        """Gets ouija data.

        Args:
            channel_id (typing.Union[str, int]): Channel id, as a string or an int.

        Returns:
            dict[str, typing.Union[str, int, bool]]: The found data.
        """
        ouija_data = self.load("askouija")

        return ouija_data.get(str(channel_id), {"active": False, "letters": "", "message_id": None, "author_id": None})
    
    def set_ouija_data(self,
            channel_id: typing.Union[str, int],
            active: bool = None,
            letters: str = None,
            message_id: int = None,
            author_id: int = None
        ) -> dict[str, typing.Union[str, int, bool]]:
        """Modifies a piece of ouija data.

        Args:
            channel_id (typing.Union[str, int]): The channel id, as a string or an int.
            active (bool, optional): New active setting. Defaults to None.
            letters (str, optional): New letters. Defaults to None.
            message_id (int, optional): New message id. Defaults to None.
            author_id (int, optional): New author id. Defaults to None.

        Returns:
            dict[str, typing.Union[str, int, bool]]: The updated dict for the channel.
        """
        ouija_data = self.load("askouija")

        if str(channel_id) not in ouija_data:
            new = {
                "active": active,
                "letters": letters,
                "message_id": message_id,
                "author_id": author_id
            }
            ouija_data[str(channel_id)] = new
            self.save("askouija", data=ouija_data)
            return new
        
        new = {}

        if active is not None:
            new["active"] = active
        if letters is not None:
            new["letters"] = letters
        if message_id is not None:
            new["message_id"] = message_id
        if author_id is not None:
            new["author_id"] = author_id
        
        ouija_data[str(channel_id)].update(new)
        self.save("askouija", data=ouija_data)
        return ouija_data[str(channel_id)]
    
    ######################################################################################################################################################
    ##### Counting. ######################################################################################################################################
    ######################################################################################################################################################
    
    def get_counting_data(self,
            channel_id: typing.Union[str, int]
        ) -> dict[str, typing.Union[str, int, bool]]:
        """Gets counting data.

        Args:
            channel_id (typing.Union[str, int]): Channel id, as a string or an int.

        Returns:
            dict[str, typing.Union[str, int, bool]]: The found data.
        """
        counting_data = self.load("counting_data")

        return counting_data.get(str(channel_id), {"count": 0, "sender": 0})
    
    def set_counting_data(self, 
            channel_id: typing.Union[str, int],
            count: int = None,
            sender: int = None
        ) -> dict[str, typing.Union[str, int, bool]]:
        """Modifies a piece of counting data.

        Args:
            channel_id (typing.Union[str, int]): The channel id, as a string or an int.
            count (int, optional): New count. Defaults to None.
            sender (int, optional): New sender id. Defaults to None.

        Returns:
            dict[str, typing.Union[str, int, bool]]: The updated dict for the channel.
        """
        counting_data = self.load("counting_data")

        if str(channel_id) not in counting_data:
            new = {
                "count": count,
                "sender": sender
            }
            counting_data[str(channel_id)] = new
            self.save("counting_data", data=counting_data)
            return new
        
        new = {}

        if count is not None:
            new["count"] = count
        if sender is not None:
            new["sender"] = sender
        
        counting_data[str(channel_id)].update(new)
        self.save("counting_data", data=counting_data)
        return counting_data[str(channel_id)]

        


def load(
        path: str,
        default: typing.Any = None,
        replace_slash: bool = False
    ) -> dict | list:
    """Loads a json file.

    Args:
        path (str): The path to the file to load.
        default (typing.Any, optional): What to return if the file does not exist. Defaults to None.
        replace_slash (bool, optional): Whether to replace all slashes in the given path with os.path.sep. Defaults to False.

    Returns:
        dict | list: The data inside the loaded file.
    """
    if replace_slash:
        path = path.replace("/", SLASH)
    
    try:
        with open(path, "r", encoding="utf8") as file_load:
            return json.load(file_load)
    except:
        return default

def save(
        path: str,
        data: dict | list,
        replace_slash: bool = False
    ) -> None:
    """Saves a dict or list to a file. Will create a file if it does not already exist.

    Args:
        path (str): The path to save the file to.
        data (dict | list): The list or dict to save.
        replace_slash (bool, optional): Whether to replace all slashes in the given path with os.path.sep. Defaults to False.
    """
    if replace_slash:
        path = path.replace("/", SLASH)

    with open(path, "w+") as file_write:
        json.dump(data, file_write, indent=4)