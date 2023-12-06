import utility.files as files
import random

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
    tile_list = files.load("data/bingo/tile_list_5x5.json")

    return generate_custom_board(tile_list, 25)

def generate_9x9_board() -> str:
    """Generates a board for the 5x5 bingo game, using the tile list in data/bingo/tile_list_9x9.json"""
    tile_list = files.load("data/bingo/tile_list_9x9.json")

    return generate_custom_board(tile_list, 81)