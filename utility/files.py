import json

def load(path: str) -> dict | list:
    """Loads a json file."""
    
    with open(path) as file_load:
        return json.load(file_load)

def save(path: str, data: dict | list) -> None:
    """Saves a dict or list to a file. Will create a file if it does not already exist."""

    with open(path, "w+") as file_write:
        json.dump(data, file_write)
    
    return None