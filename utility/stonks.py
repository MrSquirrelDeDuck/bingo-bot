"""Functions for working with stonks."""

import typing
import discord
import re

import utility.files as u_files
import utility.values as u_values
import utility.text as u_text

def stonk_history(database: u_files.DatabaseInterface) -> list[dict[str, int]]:
    """Returns the entire stonk history."""
    get = database.load("stonks", "stonk_history", default=None)

    if get is None:
        get = [
            {
                stonk.internal_name: stonk.base_value
                for stonk in u_values.stonks
            }
        ]

        database.save("stonks", "stonk_history", data=get)
    
    return get

def full_current_values(database: u_files.DatabaseInterface) -> dict[str, dict[str, int] | int]:
    """Returns the full current data from stonks/current_values in the database."""
    get = database.load("stonks", "current_values", default=None)

    if get is None:
        history = stonk_history(database)
        get = {
            "message_link": "https://discord.com/channels/958392331671830579/969883131941363712/997243972072243261",
            "tick_number": len(history) - 1,
            "values": history[-1]
        }

        database.save("stonks", "current_values", data=get)

    return get

def current_values(database: u_files.DatabaseInterface) -> dict[str, int]:
    """Returns just the current stonk values."""
    return full_current_values(database)["values"]

def current_tick_number(database: u_files.DatabaseInterface) -> int:
    """Returns the current stonk tick number."""
    return full_current_values(database)["tick_number"]

def filter_splits(
        previous: dict[u_values.StonkItem, int],
        current: dict[u_values.StonkItem, int]
    ) -> dict[str, dict[u_values.StonkItem, int]]:    
    """Filters splits and returns a corrected version. Also provides the amount of times each stonk was split."""
    amounts = {stonk: 0 for stonk in current}

    for stonk in previous:
        if not (current.get(stonk, previous[stonk]) / previous[stonk] <= 0.85):
            continue

        for i in range(50):
            previous[stonk] /= 2
            amounts[stonk] += 1
            if not (current.get(stonk, previous[stonk]) / previous[stonk] <= 0.85):
                break    
    
    return {"new": previous, "split_amounts": amounts}

def convert_tick(old: dict[str, int]) -> dict[u_values.StonkItem, int]:
    """Converts the keys in a stonk tick dict to a StonkItem object.

    Args:
        old (dict[str, int]): The stonk tick dict to use.

    Returns:
        dict[u_values.StonkItem, int]: The converted dict with StonkItem keys.
    """
    return {u_values.get_item(key): value for key, value in old.items()}

def parse_stonk_tick(message: discord.Message) -> dict[u_values.StonkItem, list[int]]:
    """Parses a stonk tick message to extract the values.

    Args:
        message (discord.Message): The message.

    Returns:
        dict[str, list[int]]: The extracted values in a dict.
    """
    content = message.content
    
    out = {}

    for stonk in u_values.stonks:
        matched = re.search(f"{stonk.internal_emoji}: .* dough", content)

        if matched is None:
            matched = re.search(f"{stonk.emoji}: .* dough", content)
        
        if matched is None:
            continue

        out[stonk] = [
            u_text.return_numeric(val)
            for val in matched.group(0).split("->")
        ]
    
    return out

def closest_to_dough(
        dough_amount: int,
        database: u_files.DatabaseInterface
    ) -> u_values.StonkItem:
    """Returns the stonk that, if all the dough is invested in that stonk, would result in the lowest remaining dough.

    Args:
        dough_amount (int): The amount of dough to use.

    Returns:
        u_values.StonkItem: The stonk.
    """
    return min(u_values.stonks, key=lambda stonk: dough_amount % stonk.value(database=database))