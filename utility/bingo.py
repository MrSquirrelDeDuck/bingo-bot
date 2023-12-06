import random

import utility.files as files

def generate_custom_board(tile_list: dict, size: int = 25) -> str:
    """Generates a bingo board based on a tile list and a size."""
    # data = files.load("data/bingo/tile_list_5x5.json")
    data = tile_list

    # Get a copy of the initial data.
    data_copy = data.copy()
    
    # Remove disabled items
    data = [item for item in data if not item.get("disabled")]

    # Filter items with "center" value set to "true"
    center_items = [item for item in data if item.get("center")]

    # Remove center items from data
    data = [item for item in data if item not in center_items]

    # Randomly select 24 non-center items
    chosen_items = random.sample(data, size - 1)

    # Shuffle the center items
    random.shuffle(center_items)

    # Pick the center item
    center_item = random.choice(center_items)

    # Shuffle the chosen items
    random.shuffle(chosen_items)

    # Get the 3-character IDs of chosen items
    ids = [str(data_copy.index(item)).zfill(3) for item in chosen_items]

    # Insert the center item at the 12th spot
    ids.insert(size // 2, str(data_copy.index(center_item)).zfill(3))

    # Create a string of 25 IDs
    result = "".join(ids)

    return result

def generate_5x5_board() -> str:
    """Generates a board for the 5x5 bingo game, using the tile list in data/bingo/tile_list_5x5.json"""
    tile_list = tile_list_5x5()

    return generate_custom_board(tile_list, 25)

def generate_9x9_board() -> str:
    """Generates a board for the 5x5 bingo game, using the tile list in data/bingo/tile_list_9x9.json"""
    tile_list = tile_list_9x9()

    return generate_custom_board(tile_list, 81)

def decompile_enabled(enabled: int, board_size: int) -> list[bool]:
    """Decompiles an enabled integer into a list of booleans.
    
    Note that providing the size of the board is required. The size of the board is the length of one edge, so for the 5x5 board it would be 5."""

    # Get a list full of `False` that's the size of board_size^2.
    result_data = [False] * board_size ** 2

    # Loop thorugh the indexes in result_data, from last to first.
    for index in range(board_size ** 2, -1, -1):
        # If the enable number is greater than 2^index, then we know this one is enabled.
        if enabled >= 2 ** index:
            result_data[index] = True
            enabled -= 2 ** index

    return result_data    

def tile_list_5x5() -> list[dict]:
    """Returns the 5x5 board tile list."""
    return files.load("data/bingo/tile_list_5x5.json")

def tile_list_9x9() -> list[dict]:
    """Returns the 9x9 board tile list."""
    return files.load("data/bingo/tile_list_9x9.json")

def live() -> dict:
    """Returns the current live data dict."""
    return files.load("data/bingo/live_data.json")