"""Contains functions for loading and saving to files."""

import json
import typing

def load(path: str, default = None) -> dict | list:
    """Loads a json file. The provided default will be returned if the file does not exist or there is a problem loading it."""
    
    try:
        with open(path, "r", encoding="utf8") as file_load:
            return json.load(file_load)
    except:
        return default

def save(path: str, data: dict | list) -> None:
    """Saves a dict or list to a file. Will create a file if it does not already exist."""

    with open(path, "w+") as file_write:
        json.dump(data, file_write, indent=4)

def get_ping_list_file() -> dict[str, list[typing.Optional[int]]]:
    return load("data/ping_lists.json")

def set_ping_list_file(data: dict[str, list[typing.Optional[int]]]) -> None:
    return save("data/ping_lists.json", data)

def get_ping_list(ping_list_name: str) -> list[typing.Optional[int]]:
    """Gets a ping list from the ping list file.

    Args:
        ping_list_name (str): The key of the ping list.

    Returns:
        list[typing.Optional[int]]: A list of user ids that are on the ping list, or an empty list if the ping list does not exist (or nobody is on it :( )
    """
    ping_list_file = get_ping_list_file()

    if ping_list_name in ping_list_file:
        return ping_list_file[ping_list_name]
    
    return []

def user_on_ping_list(ping_list_name: str, user_id: int) -> bool:
    """Returns a boolean for whether a user is on a specific ping list.

    Args:
        ping_list_name (str): The name of the ping list to check.
        user_id (int): The id of the user to check.

    Returns:
        bool: Whether the user is on the ping list.
    """
    return user_id in get_ping_list_file().get(ping_list_name, [])

def update_ping_list(ping_list_name: str, user_id: int, new_state: bool) -> None:
    """Modifies the state of a ping list.

    Args:
        ping_list_name (str): The name of the ping list to modify.
        user_id (int): The id of the user to modify.
        new_state (bool): Whether the player should be on it, True for yes, False for no.
    """
    ping_list_file = get_ping_list_file()

    if ping_list_name not in ping_list_file:
        if new_state:
            ping_list_file[ping_list_name] = [user_id]
        else:
            ping_list_file[ping_list_name] = []

        set_ping_list_file(ping_list_file)
        return
    
    if new_state:
        if user_id in ping_list_file[ping_list_name]:
            return
        
        ping_list_file[ping_list_name].append(user_id)
        set_ping_list_file(ping_list_file)
        return
    
    if user_id not in ping_list_file[ping_list_name]:
        return
    
    ping_list_file[ping_list_name].remove(user_id)
    set_ping_list_file(ping_list_file)
    return