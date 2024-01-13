"""Functions for working with stonks."""

import utility.files as u_files

def stonk_history() -> list[dict[str, int]]:
    """Returns the entire stonk history."""
    return u_files.load("data/stonks/stonk_history.json")

def current_values() -> dict[str, int]:
    """Returns just the current stonk values."""
    return u_files.load("data/stonks/current_values.json")