"""Contains functions for loading and saving to files."""

import json

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