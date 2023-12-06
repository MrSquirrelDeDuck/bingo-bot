from PIL import Image as PIL_Image
from PIL import ImageDraw as PIL_ImageDraw
from PIL import ImageFont as PIL_ImageFont
import textwrap

import utility.bingo as bingo
import utility.text as text

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

def render_board(tile_string: str, enabled: int, tile_list: list[dict], board_size: int, solo: bool = False) -> PIL_Image:
    """Generates an image for a 5x5 bingo board and saves it to images/generated/bingo_board.png

    Board size is in length of one face of the sqaure, so for a 5x5 board it would be 5.
    
    After saving the image it will return the image object."""

    # Split the tile string into groups of 3 characters.
    tile_string_split = text.split_chunks(tile_string, 3)

    # Generate the base image from bingo_board_base().
    img = bingo_board_base(board_size, solo)

    # Setup ImageDraw, the font, and the text wrapper.
    draw = PIL_ImageDraw.Draw(img)
    font = PIL_ImageFont.truetype("verdana.ttf", size=25)
    text_wrapper = textwrap.TextWrapper(width=14) 

    # Convert the enabled number into a list of booleans.
    enabled_list = bingo.decompile_enabled(enabled, board_size)

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
    img.save("images/generated/bingo_board.png")

    # Return the image.
    return img

def render_board_5x5(tile_string: str, enabled: int) -> PIL_Image:
    """Renders a 5x5 bingo board and saves to images/generated/bingo_board.png

    After saving the image it will return the image object."""

    tile_list = bingo.tile_list_5x5()

    return render_board(
        tile_string = tile_string,
        enabled = enabled,
        tile_list = tile_list,
        board_size = 5
    )

def render_board_9x9(tile_string: str, enabled: int) -> PIL_Image:
    """Renders a 9x9 bingo board and saves to images/generated/bingo_board.png

    After saving the image it will return the image object."""

    tile_list = bingo.tile_list_9x9()

    return render_board(
        tile_string = tile_string,
        enabled = enabled,
        tile_list = tile_list,
        board_size = 9
    )