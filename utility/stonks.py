"""Functions for working with stonks."""

from os.path import sep as SLASH

import typing

import utility.files as u_files
import utility.values as u_values

def stonk_history() -> list[dict[str, int]]:
    """Returns the entire stonk history."""
    return u_files.load(f"data{SLASH}stonks{SLASH}stonk_history.json")

def full_current_tick() -> dict[str, typing.Union[dict[str, int], int]]:
    """Returns the raw values from current_values.json."""
    return u_files.load(f"data{SLASH}stonks{SLASH}current_values.json")

def current_values() -> dict[str, int]:
    """Returns just the current stonk values."""
    return full_current_tick()["values"]

def current_tick_number() -> int:
    """Returns the current stonk tick number."""
    return full_current_tick()["tick_number"]

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