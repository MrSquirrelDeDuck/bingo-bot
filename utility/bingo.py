"""Functions that relate to the bingo game."""

import random
import typing

import utility.files as files
import utility.text as text

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
    result_data = [False for _ in range(board_size ** 2)]

    # Loop thorugh the indexes in result_data, from last to first.
    for index in range(board_size ** 2, -1, -1):
        # If the enable number is greater than 2^index, then we know this one is enabled.
        if enabled >= 2 ** index:
            result_data[index] = True
            enabled -= 2 ** index

    return result_data

def compile_enabled(enabled_list: list[bool]) -> int:
    """Compiles a list of bools into an integer."""

    # Initialize a variable to track the current number.
    result = 0

    # Loop through the provided list, and if an item is true add 2^index to the current variable.
    for index, item in enumerate(enabled_list):
        if item:
            result += 2 ** index
    
    return result

def count_bingos(enabled_data: list[bool] | int, board_size: int = None) -> int:
    """Returns the amount of bingos in an enabled tiles list or enabled integer. If an integer is provided a board size must also be provided as the length of one side."""

    # If enabled_data is an int, make sure that board_size is passed, and then convert enabled_data to a list of bools.
    if isinstance(enabled_data, int):
        if board_size is None:
            msg = "Because the passed enabled data is an enabled integer, a board size must be provided."
            raise TypeError(msg)
        
        enabled_data = decompile_enabled(enabled_data, board_size)

    bingos_found = 0

    # Get the board size.
    board_size = int(len(enabled_data) ** 0.5)

    # Check vertical lines.
    for modifier in range(board_size):
        if all(enabled_data[modifier::board_size]):
            bingos_found += 1

    # Check horizontal lines.
    for modifier in range(board_size):
        if all(enabled_data[modifier * board_size:modifier * board_size + board_size]):
            bingos_found += 1
    
    # If the board size is even, then there are no diagonal lines, in which case we just return the number of bingos found already.
    if board_size % 2 == 0:
        return bingos_found
    
    # Top left to bottom right diagonal.
    if all(enabled_data[::6]):
        bingos_found += 1

    # Top right to bottom left diagonal.
    if all(enabled_data[board_size - 1:len(enabled_data) - 1:board_size - 1]):
        bingos_found += 1
    
    return bingos_found

def tile_list_5x5() -> list[dict]:
    """Returns the 5x5 board tile list."""
    return files.load("data/bingo/tile_list_5x5.json")

def get_objective_5x5(objective_id: int) -> dict:
    """Gets the data for an objective from the 5x5 tile list."""
    return tile_list_5x5()[objective_id]

def tile_list_9x9() -> list[dict]:
    """Returns the 9x9 board tile list."""
    return files.load("data/bingo/tile_list_9x9.json")

def get_objective_9x9(objective_id: int) -> dict:
    """Gets the data for an objective from the 9x9 tile list."""
    return tile_list_9x9()[objective_id]

def live() -> dict:
    """Returns the current live data dict."""
    return files.load("data/bingo/live_data.json")

def update_live(new_data: dict) -> None:
    """Updates the live data with the provided dict."""
    files.save("data/bingo/live_data.json", new_data)

def set_live(key: str, value: any) -> None:
    """Sets a single value in the live data, takes the key and new value."""
    
    # Get the current data.
    live_data = live()

    # Update the key with the new value.
    live_data[key] = value

    # Save the data.
    update_live(live_data)

def get_tile_state_5x5(tile_id: int) -> bool:
    """Gets a bool for whether a specific tile on the 5x5 board is ticked or not."""

    # Get the live data.
    live_data = live()

    # Decompile the enabled integer into a list of bools, and return the one chosen by the tile_id parameter.
    return decompile_enabled(live_data["daily_enabled"], 5)[tile_id]

def get_tile_state_9x9(tile_id: int) -> bool:
    """Gets a bool for whether a specific tile on the 9x9 board is ticked or not."""

    # Get the live data.
    live_data = live()

    # Decompile the enabled integer into a list of bools, and return the one chosen by the tile_id parameter.
    return decompile_enabled(live_data["weekly_enabled"], 9)[tile_id]

def update_tile(tile_id: int, board_size: int, live_data_key: str, new_value: bool, live_data: dict = None) -> tuple[int, int]:
    """Updates a tile on a bingo board.
    
    Parameters:
    - tile_id (int): The tile id on the board to tick, should be a value between 0 and board_size^2-1.
    - board_size (int): The length of one face of the board, so for the 5x5 board it would be 5.
    - live_data_key (str): The key in the live data that houses the current enabled string.
    - new_value (bool): The new value for the tile data, should be either True or False.
    - live_data (dict) = None: An optional parameter that allows for passing of a version of the live data, so this function doesn't get another copy.
    
    Returns a tuple of:
    - Pre-tick enabled integer.
    - Post-tick enabled integer."""

    # If live_data was not provided, get the current data.
    if live_data is None:
        live_data = live()

    # Get a copy of the pre-tick enabled integer.
    pre_tick = live_data[live_data_key]

    # Decompile the current enabled number into a list.
    decompiled = decompile_enabled(pre_tick, board_size ** 2)

    # Update the changing value with True.
    decompiled[tile_id] = new_value

    # Compile the list of bools into a number.
    post_tick = compile_enabled(decompiled)

    # Save the data, while compiling the `decompiled` list into a number.
    set_live(live_data_key, post_tick)

    # Return the before and after version of the enabled integer.
    return (pre_tick, post_tick)

def tick_5x5(tile_id: int) -> tuple[int, int, int]:
    """Ticks a tile on the 5x5 board, takes a tile id.
    
    Returns a tuple of:
    - Pre-tick enabled integer.
    - Post-tick enabled integer.
    - Objective id of the affected tile."""

    # Get the current data.
    live_data = live()

    pre_tick, post_tick = update_tile(
        tile_id = tile_id,
        board_size = 5,
        live_data_key = "daily_enabled",
        new_value = True,
        live_data = live_data
    )

    # Get the tile string and split it into groups of 3 characters.
    tile_string = live_data["daily_tile_string"]
    split_tile_string = text.split_chunks(tile_string, 3)

    # Return an integer version of the objective id of the ticked tile.
    return (pre_tick, post_tick, int(split_tile_string[tile_id]))

def untick_5x5(tile_id: int) -> tuple[int, int, int]:
    """Unticks a tile on the 5x5 board, takes a tile id.
    
    Returns a tuple of:
    - Pre-tick enabled integer.
    - Post-tick enabled integer."""

    pre_tick, post_tick = update_tile(
        tile_id = tile_id,
        board_size = 5,
        live_data_key = "daily_enabled",
        new_value = False
    )

    # Return an integer version of the objective id of the ticked tile.
    return (pre_tick, post_tick)