"""Functions for working with stonks."""

from os.path import sep as SLASH

import typing
import discord
import re

import utility.files as u_files
import utility.values as u_values
import utility.text as u_text

def stonk_history() -> list[dict[str, int]]:
    """Returns the entire stonk history."""
    return u_files.load(f"data{SLASH}stonks{SLASH}stonk_history.json")

def full_current_values() -> dict[str, typing.Union[dict[str, int], int]]:
    """Returns the raw values from current_values.json."""
    return u_files.load(f"data{SLASH}stonks{SLASH}current_values.json")

def current_values() -> dict[str, int]:
    """Returns just the current stonk values."""
    return full_current_values()["values"]

def current_tick_number() -> int:
    """Returns the current stonk tick number."""
    return full_current_values()["tick_number"]

def filter_splits(previous: dict[u_values.StonkItem, int], current: dict[u_values.StonkItem, int]) -> dict[str, dict[u_values.StonkItem, int]]:    
    """Filters splits and returns a corrected version. Also provides the amount of times each stonk was split."""
    amounts = {stonk: 0 for stonk in current}

    for stonk in previous:
        if not (current[stonk] / previous[stonk] <= 0.85):
            continue

        for i in range(50):
            previous[stonk] /= 2
            amounts[stonk] += 1
            if not (current[stonk] / previous[stonk] <= 0.85):
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