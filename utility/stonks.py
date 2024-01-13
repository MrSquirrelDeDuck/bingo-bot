"""Functions for working with stonks."""

from os.path import sep as SLASH

import typing
import utility.files as u_files

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