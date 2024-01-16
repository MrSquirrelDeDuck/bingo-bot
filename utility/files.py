"""Contains functions for loading and saving to files."""

import json
import typing
from os.path import sep as SLASH

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

def get_ouija_data(channel_id: typing.Union[str, int]) -> dict[str, typing.Union[str, int, bool]]:
    """Gets ouija data.

    Args:
        channel_id (typing.Union[str, int]): Channel id, as a string or an int.

    Returns:
        dict[str, typing.Union[str, int, bool]]: The found data.
    """
    ouija_data = load(f"data{SLASH}askouija.json")

    return ouija_data.get(str(channel_id), {"active": False, "letters": "", "message_id": None, "author_id": None})

def set_ouija_data(channel_id: typing.Union[str, int], active: bool = None, letters: str = None, message_id: int = None, author_id: int = None) -> dict[str, typing.Union[str, int, bool]]:
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
    ouija_data = load(f"data{SLASH}askouija.json")

    if str(channel_id) not in ouija_data:
        new = {
            "active": active,
            "letters": letters,
            "message_id": message_id,
            "author_id": author_id
        }
        ouija_data[str(channel_id)] = new
        save(f"data{SLASH}askouija.json", ouija_data)
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
    save(f"data{SLASH}askouija.json", ouija_data)
    return ouija_data[str(channel_id)]

def get_counting_data(channel_id: typing.Union[str, int]) -> dict[str, typing.Union[str, int, bool]]:
    """Gets counting data.

    Args:
        channel_id (typing.Union[str, int]): Channel id, as a string or an int.

    Returns:
        dict[str, typing.Union[str, int, bool]]: The found data.
    """
    counting_data = load(f"data{SLASH}counting_data.json")

    return counting_data.get(str(channel_id), {"count": 0, "sender": 0})

def set_counting_data(channel_id: typing.Union[str, int], count: int = None, sender: int = None) -> dict[str, typing.Union[str, int, bool]]:
    """Modifies a piece of counting data.

    Args:
        channel_id (typing.Union[str, int]): The channel id, as a string or an int.
        count (int, optional): New count. Defaults to None.
        sender (int, optional): New sender id. Defaults to None.

    Returns:
        dict[str, typing.Union[str, int, bool]]: The updated dict for the channel.
    """
    counting_data = load(f"data{SLASH}counting_data.json")

    if str(channel_id) not in counting_data:
        new = {
            "count": count,
            "sender": sender
        }
        counting_data[str(channel_id)] = new
        save(f"data{SLASH}counting_data.json", counting_data)
        return new
    
    new = {}

    if count is not None:
        new["count"] = count
    if sender is not None:
        new["sender"] = sender
    
    counting_data[str(channel_id)].update(new)
    save(f"data{SLASH}counting_data.json", counting_data)
    return counting_data[str(channel_id)]