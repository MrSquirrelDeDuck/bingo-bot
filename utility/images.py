"""Functions for the generation of images."""

from os.path import sep as SLASH

from PIL import Image as PIL_Image
from PIL import ImageDraw as PIL_ImageDraw
from PIL import ImageFont as PIL_ImageFont
import textwrap
import matplotlib.pyplot as plt
import matplotlib
import typing

import utility.bingo as u_bingo
import utility.text as u_text
import utility.files as u_files

######################################################################################################################################
##### BINGO BOARDS ###################################################################################################################
######################################################################################################################################

def bingo_board_base(board_size: int, solo: bool = False) -> PIL_Image:
    """Generates the base for a bingo board, allowing for any size."""

    # Figure out how large the image is going to be 
    size = (
        20 + 250 * board_size + 10 * (board_size - 1),
        20 + 250 * board_size + 20 * (board_size - 1),
    )

    # Get the background color, if it's a solo board it's green, if it's a normal board it's red.
    if solo:
        background_color = (31, 168, 43)
    else:
        background_color = (170, 31, 48)

    # Create a new image using the determined size and background color.
    img = PIL_Image.new(
        mode = "RGB",
        size = size,
        color = background_color
    )

    # Setup ImageDraw for the image.
    draw = PIL_ImageDraw.Draw(img)

    # Loop through all the squares on the grid.
    for ypos in range(board_size):
        for xpos in range(board_size):
            # Draw the black border as a rectangle.
            draw.rectangle(
                xy = ((xpos * 260 + 10, ypos * 270 + 10),
                (xpos * 260 + 258, ypos * 270 + 258)),
                fill = (0, 0, 0),
                width = 0
            )

            # Draw the white inside by drawing a rectangle over the black rectangle.
            draw.rectangle(
                xy = ((xpos * 260 + 16, ypos * 270 + 16),
                (xpos * 260 + 252, ypos * 270 + 252)),
                fill = (255, 255, 255),
                width = 0
            )

    # Return the finished image.
    return img

def render_board(tile_string: str, enabled: int, tile_list: list[dict], board_size: int, solo: bool = False, force: bool = False) -> PIL_Image:
    """Generates an image for a 5x5 bingo board and saves it to images/generated/bingo_board.png

    Board size is in length of one face of the sqaure, so for a 5x5 board it would be 5.
    
    After saving the image it will return the image object."""

    # Get the current data, since if the last image generated is the same as the one we're making, then we don't need to make anything new.
    if not force:
        # If force is true, then we don't do this check.
        current_data = u_files.load(f"data{SLASH}bingo{SLASH}last_generated.json")
        if all([
                board_size == current_data.get("last_size"),
                tile_string == current_data.get(f"board"),
                enabled == current_data.get(f"enabled"),
                solo == current_data.get(f"solo")
            ]):
            # If it's here, then the board is the same.
            # Now we load the existing image, and return it.
            return PIL_Image.open(f"images{SLASH}generated{SLASH}bingo_board.png")

    # Split the tile string into groups of 3 characters.
    tile_string_split = u_text.split_chunks(tile_string, 3)

    # Generate the base image from bingo_board_base().
    img = bingo_board_base(board_size, solo)

    # Setup ImageDraw, the font, and the text wrapper.
    draw = PIL_ImageDraw.Draw(img)
    font = PIL_ImageFont.truetype("verdana.ttf", size=25)
    text_wrapper = textwrap.TextWrapper(width=14) 

    # Convert the enabled number into a list of booleans.
    enabled_list = u_bingo.decompile_enabled(enabled, board_size)

    # Loop through all the items in the enabled list, but using `enumerate()` so it tracks the index.
    for index, item in enumerate(enabled_list):
        # Draw the yellow square, only if that item in enabled_list is True.
        if item:
            draw.rectangle(
                xy = ((index % board_size * 260 + 16, index // board_size * 270 + 16),
                (index % board_size * 260 + 252, index // board_size * 270 + 252)),
                fill = (255, 255, 0),
                width = 0
            )
        
        # Get the text of the objective that goes on this tile.
        tile_text = tile_list[int(tile_string_split[index])]["name"]

        # Wrap the text of the objective so it'll fit in the square.
        text_split = text_wrapper.wrap(tile_text)

        # For each line in the text, draw that text via ImageDraw.
        for line_index, line in enumerate(text_split):
            draw.text(
                xy = (134 + 260 * (index % board_size), (((134 + line_index * 25) + 270 * (index // board_size))) - (9 * len(text_split))), 
                text = line, 
                font = font,
                fill = (0, 0, 0),
                anchor = "mm"
            )
    
    # Save the image to images/generated/bingo_board.png
    img.save(f"images{SLASH}generated{SLASH}bingo_board.png")

    # Update the data in data/bingo/last_generated.json.
    current_data = u_files.load(f"data{SLASH}bingo{SLASH}last_generated.json")

    current_data["board"] = tile_string
    current_data["enabled"] = enabled
    current_data["solo"] = solo
    current_data["last_size"] = board_size

    u_files.save(f"data{SLASH}bingo{SLASH}last_generated.json", current_data)

    # Return the image.
    return img

def render_board_5x5(tile_string: str, enabled: int) -> PIL_Image:
    """Renders a 5x5 bingo board and saves to images/generated/bingo_board.png

    After saving the image it will return the image object."""

    tile_list = u_bingo.tile_list_5x5()

    return render_board(
        tile_string = tile_string,
        enabled = enabled,
        tile_list = tile_list,
        board_size = 5
    )

def render_board_9x9(tile_string: str, enabled: int) -> PIL_Image:
    """Renders a 9x9 bingo board and saves to images/generated/bingo_board.png

    After saving the image it will return the image object."""

    tile_list = u_bingo.tile_list_9x9()

    return render_board(
        tile_string = tile_string,
        enabled = enabled,
        tile_list = tile_list,
        board_size = 9
    )

######################################################################################################################################
##### GRAPHS #########################################################################################################################
######################################################################################################################################

def generate_graph(
    lines: list[dict[str, typing.Union[str, tuple[int, int, int], list[tuple[int, int]]]]], # color, label, values
    *,
    x_label: str = "",
    y_label: str = "",
    log_scale: bool = False,
    file_name: str = f"images{SLASH}generated{SLASH}generated_graph.png"
) -> str:
    """Generates a graph.

    Args:
        lines (list[dict[str, typing.Union[str, tuple[int, int, int], list[tuple[int, int]]]]]): The data to graph, should be a list of dicts, each dict with "color", "label" and "values" keys, the values one should be a list of tuples with x and y coordinates, "color" can be a string hex code or RGB, "label" should just be a string.
        x_label (str, optional): The label of the x axis. Defaults to "".
        y_label (str, optional): The label of the y axis. Defaults to "".
        log_scale (bool, optional): Whether the y axis should be on a log scale. Defaults to False.
        file_name (bool, optional): Custom file location. Defaults to "images/generated/generated_graph.png".

    Returns:
        str: The file name of the generated image, this is going to be the same as the file_name argument.
    """
    plt.clf()

    for line_data in lines:
        line_color = line_data.get("color")

        if isinstance(line_color, tuple):
            line_color = tuple([color / 255 for color in line_color])
        elif isinstance(line_color, str):
            line_color = line_color.replace("#", "")
            line_color = [int(item, 16) / 255 for item in u_text.split_chunks(line_color, 2)]

        line_label = line_data.get("label")

        x_values = []
        y_values = []

        for x_val, y_val in line_data["values"]:
            x_values.append(x_val)
            y_values.append(y_val)
        
        plt.plot(x_values, y_values, label=line_label, color=line_color)
    
    plt.xlabel(x_label)
    plt.ylabel(y_label)

    if log_scale:
        plt.yscale('log')

    plt.legend(bbox_to_anchor=(1.04, 0.5), loc="center left", borderaxespad=0)
    plt.grid()
    
    plt.savefig(file_name, bbox_inches='tight')

    return file_name
        

