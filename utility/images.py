"""Functions for the generation of images."""

from os.path import sep as SLASH

import typing
import importlib
import textwrap
import io
import chess
import math

# pip install matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# pip install pillow
from PIL import Image as PIL_Image
from PIL import ImageDraw as PIL_ImageDraw
from PIL import ImageFont as PIL_ImageFont

import utility.bingo as u_bingo
import utility.text as u_text
import utility.files as u_files
import utility.stonks as u_stonks
import utility.values as u_values
import utility.algorithms as u_algorithms
import utility.chess_utils as u_chess

######################################################################################################################################
##### BINGO BOARDS ###################################################################################################################
######################################################################################################################################

def bingo_board_base(
        board_size: int,
        solo: bool = False
    ) -> PIL_Image:
    """Generates the base of a bingo board, without any text.

    Args:
        board_size (int): The length of one side of the square board. So for the 5x5 board it would be 5.
        solo (bool, optional): Whether this is a solo board, in which case the background will be green. Defaults to False.

    Returns:
        PIL_Image: The generated image object.
    """

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

def render_board(
        database: u_files.DatabaseInterface,
        tile_string: str,
        enabled: int,
        tile_list: list[dict],
        board_size: int,
        solo: bool = False,
        force: bool = False
    ) -> PIL_Image:
    """Generates the image for a bingo board and saves it to 'images/generated/bingo_board.png'

    Args:
        database (u_files.DatabaseInterface): The database object.
        tile_string (str): The tile string to render.
        enabled (int): The integer that defines what objectives have been completed.
        tile_list (list[dict]): The tile list to pull objective names from.
        board_size (int): The length of one side of the square board. So for the 5x5 board it would be 5.
        solo (bool, optional): Whether this is a solo board, in which case the background will be green. Defaults to False.
        force (bool, optional): Whether to force it to make the image, and to not use the last generated image if the data matches. Defaults to False.

    Returns:
        PIL_Image: The generated image object. The image is also saved to the above path.
    """

    # Get the current data, since if the last image generated is the same as the one we're making, then we don't need to make anything new.
    if not force:
        # If force is true, then we don't do this check.
        current_data = database.load("bingo", "last_generated", default={})
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
    font = PIL_ImageFont.truetype(f"images{SLASH}bases{SLASH}verdana.ttf", size=25)
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

    # Update the data in bingo/last_generated.
    database.save("bingo", "last_generated", data={
        "board": tile_string,
        "enabled": enabled,
        "solo": solo,
        "last_size": board_size
    })

    # Return the image.
    return img

def render_board_5x5(
        database: u_files.DatabaseInterface,
        tile_string: str,
        enabled: int
    ) -> PIL_Image:
    """Renders a 5x5 bingo board and saves to images/generated/bingo_board.png

    After saving the image it will return the image object."""

    tile_list = u_bingo.tile_list_5x5(database=database)

    return render_board(
        database = database,
        tile_string = tile_string,
        enabled = enabled,
        tile_list = tile_list,
        board_size = 5
    )

def render_full_5x5(
        database: u_files.DatabaseInterface,
        tile_string: str,
        enabled: int
    ) -> PIL_Image:
    """Renders the 5x5 board in the announcement version."""

    tile_list = u_bingo.tile_list_5x5(database=database)

    main_board = render_board(
        database = database,
        tile_string = tile_string,
        enabled = enabled,
        tile_list = tile_list,
        board_size = 5
    )

    base = PIL_Image.open(f"images{SLASH}bases{SLASH}full_5x5_base.png").copy().convert("RGBA")

    base.paste(main_board, (0, 270))

    current_data = database.load("bingo", "last_generated", default={})

    current_data["last_size"] = "5x5_full"

    database.save("bingo", "last_generated", data=current_data)

    base.save(f"images{SLASH}generated{SLASH}bingo_board.png")

    return base

def render_board_9x9(
        database: u_files.DatabaseInterface,
        tile_string: str,
        enabled: int
    ) -> PIL_Image:
    """Renders a 9x9 bingo board and saves to images/generated/bingo_board.png

    After saving the image it will return the image object."""

    tile_list = u_bingo.tile_list_9x9(database=database)

    return render_board(
        database = database,
        tile_string = tile_string,
        enabled = enabled,
        tile_list = tile_list,
        board_size = 9
    )

######################################################################################################################################
##### GRAPHS #########################################################################################################################
######################################################################################################################################

def generate_graph(
        lines: list[dict[str, str | tuple[int, int, int] | list[tuple[int, int]]]], # color, label, values
        *,
        x_label: str = "",
        y_label: str = "",
        log_scale: bool = False,
        file_name: str = f"images{SLASH}generated{SLASH}generated_graph.png"
    ) -> str:
    """Generates a graph.

    Args:
        lines (list[dict[str, str | tuple[int, int, int] | list[tuple[int, int]]]]): The data to graph, should be a list of dicts, each dict with "color", "label" and "values" keys, the values one should be a list of tuples with x and y coordinates, "color" can be a string hex code or RGB, "label" should just be a string.
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

def generate_bar_graph(
        bars: list[tuple[str, int]], # label, values
        *,
        x_label: str = "",
        y_label: str = "",
        file_name: str = f"images{SLASH}generated{SLASH}generated_graph.png"
    ) -> str:
    """Generates a bar graph.

    Args:
        bars (list[tuple[str, int]]): A list of tuples, each tuple should have a string and an int, the string is the label and the int is the value.
        x_label (str, optional): The x axis label. Defaults to "".
        y_label (str, optional): The y axis label. Defaults to "".
        file_name (str, optional): The file path. Defaults to "images/generated/generated_graph.png".

    Returns:
        str: The file name of the generated image, this is going to be the same as the file_name argument.
    """
    plt.clf()

    x_labels, y_values = list(zip(*bars))

    plt.bar(x_labels, y_values)

    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.grid()

    plt.savefig(file_name, bbox_inches='tight')

    return file_name

######################################################################################################################################
##### STONK REPORT ###################################################################################################################
######################################################################################################################################

def stonk_report(database: u_files.DatabaseInterface) -> None:
    """Generates the image for the stonk report and saves it to 'images/generated/stonk_report.png'

    Args:
        database (u_files.DatabaseInterface): The database object.
    """
    START_TICK = 2000 # The starting tick for the average value calculation.

    stonk_history = u_stonks.stonk_history(database)

    current_tick = u_stonks.convert_tick(stonk_history[-1])
    previous_tick = u_stonks.convert_tick(stonk_history[-2])

    previous_tick = u_stonks.filter_splits(previous_tick, current_tick)["new"]

    # Stonk algorithms.
    importlib.reload(u_algorithms)

    stonk_values = u_stonks.current_values(database)
    check = lambda data: u_algorithms.dough_sum(data, stonk_values) ** (1 / (data["tick"] - 2000)) # data["data"]["current_total"] / 5000)

    leaderboard = u_algorithms.get_leaderboard(database, check, filter_list=["hide_report"])

    algorithm_data = u_algorithms.get_info(database, leaderboard[0][0])
    algorithm_portfolio = algorithm_data["func"](1_000_000)["portfolio"]
    algorithm_choices = [ # This can be called via list[bool] to get whether it was chosen by the algorithm or not.
        ((0.75, 0.4, 0.4, 1), PIL_Image.open(f"images{SLASH}bases{SLASH}x.png").resize((90, 90)).convert("RGBA")),
        ((0.4, 0.75, 0.4, 1), PIL_Image.open(f"images{SLASH}bases{SLASH}check.png").resize((90, 90)).convert("RGBA"))
    ]
    ###################

    backgrounds = [
        (0.85, 0.85, 0.85, 1.0),
        (0.94, 0.94, 0.94, 1.0)
    ]

    gradients = [
        mcolors.LinearSegmentedColormap.from_list('gradient', [(1, 0, 0, 1.0), backgrounds[0], (0, 1, 0, 1.0)], N=100), # Dark background.
        mcolors.LinearSegmentedColormap.from_list('gradient', [(1, 0, 0, 1.0), backgrounds[1], (0, 1, 0, 1.0)], N=100) # Light background.
    ]

    img = PIL_Image.open(f"images{SLASH}bases{SLASH}stonk_report_base.png").copy().convert("RGBA")
    font = PIL_ImageFont.truetype(f"images{SLASH}bases{SLASH}verdana.ttf", size=57)
    algorithm_font = PIL_ImageFont.truetype("images/bases/centaur.ttf", size=50)
    imgDraw = PIL_ImageDraw.Draw(img)

    # Write the best algorithm's name.
    imgDraw.text((100, 660), algorithm_data["name"].replace("_"," ").title(), (0, 0, 0), font=algorithm_font, align="center", stroke_width=1)

    def get_data_list(
            key: typing.Callable[[int, int], float],
            stonk: u_values.StonkItem,
            offset: int = 0,
            default: int = 1
        ) -> list[int | float]:
        """Generates a list of values using the key function.

        Args:
            key (typing.Callable[[int, int], float]): A function that takes in two integers and returns a float. The two integers will be the start tick and the end tick.
            stonk (u_values.StonkItem): The stonk that will be used.
            offset (int, optional): Offset from the starting tick. Defaults to 0.
            default (int, optional): The value that will be put in the list if there aren't enough ticks. Defaults to 1.

        Returns:
            list[int | float]: The created list.
        """
        if START_TICK + offset >= len(stonk_history):
            return [default]
        
        out = []
        for tick_id in range(START_TICK + offset, len(stonk_history)):
            data = [
                u_stonks.convert_tick(tick)
                for tick in stonk_history[tick_id - offset:tick_id + 1]
            ]
            
            out.append(key(data))

        return out
    
    def convert_color(data: tuple):
        return tuple([int(item * 255) for item in data])
    
    def render_gradient(
            gradient: mcolors.LinearSegmentedColormap,
            vertical_position: int,
            stonk_id: int,
            pixel_count: int = 47
        ) -> tuple:
        for pixel in range(pixel_count):
            color = convert_color(gradient(pixel / pixel_count))
            imgDraw.rectangle([(520 + (stonk_id * 435), 315 + (vertical_position * 100) + pixel), (949 + (stonk_id * 435), 315 + (vertical_position * 100) + pixel)], fill=color)
            imgDraw.rectangle([(520 + (stonk_id * 435), 409 + (vertical_position * 100) - pixel), (949 + (stonk_id * 435), 409 + (vertical_position * 100) - pixel)], fill=color)

    def render_data(
            data: float,
            data_list: list[float],
            text: str,
            vertical_position: int,
            stonk_id: int
        ) -> None:
        """Renders the gradient on the image and then puts the text on top."""

        base_gradient = gradients[stonk_id % 2]
        average = sum(data_list) / len(data_list)
        if data > average:
            color_id = 50 + ((data - average) / (max(data_list) - average)) * 50
        elif data == average:
            color_id = 50
        else:
            color_id = ((data - min(data_list)) / (average - min(data_list))) * 50

        color = convert_color(base_gradient(color_id / 100)) # tuple([int(item * 255) for item in base_gradient(color_id / 100)])
        gradient = mcolors.LinearSegmentedColormap.from_list('gradient', [tuple([i / 255 for i in color]), backgrounds[stonk_id % 2]], N=47)

        render_gradient(
            gradient = gradient,
            vertical_position = vertical_position,
            stonk_id = stonk_id
        )
        
        imgDraw.text((734 + (435 * stonk_id) - (33 * len(str(text)) / 2), 320 + (101 * vertical_position)), str(text), font=font, fill=(0, 0, 0))    

    for stonk_id, stonk in enumerate(u_values.stonks):
        def calc(x: list[dict]):
            x[-2] = u_stonks.filter_splits(x[-2], x[-1])["new"]
            return x[-1].get(stonk) / x[-2].get(stonk)

        change_percent_list = get_data_list(
            key = calc,
            stonk = stonk,
            offset = 1
        )

        day_percent_list = [
            sum(change_percent_list[tick_id - 3:tick_id + 1]) / 4
            for tick_id in range(len(change_percent_list))
            if tick_id >= 4
        ]

        three_days_percent_list = [
            sum(change_percent_list[tick_id - 11:tick_id + 1]) / 12
            for tick_id in range(len(change_percent_list))
            if tick_id >= 12
        ]

        change = current_tick.get(stonk, stonk.base_value) - previous_tick.get(stonk, stonk.base_value)
        change_percent = change_percent_list[-1]
        day_percent = day_percent_list[-1]
        three_days_percent = three_days_percent_list[-1]

        # First row, raw change and percent changed.
        render_data(
            data = change_percent,
            data_list = change_percent_list,
            text = "{} ({:.2%})".format(change, change_percent - 1),
            vertical_position = 0,
            stonk_id = stonk_id
        )

        # Second row, average change in the past 4 ticks.
        render_data(
            data = day_percent,
            data_list = day_percent_list,
            text = "{:.2%}".format(day_percent - 1),
            vertical_position = 1,
            stonk_id = stonk_id
        )

        # Third row, average change in the past 12 ticks.
        render_data(
            data = three_days_percent,
            data_list = three_days_percent_list,
            text = "{:.2%}".format(three_days_percent - 1),
            vertical_position = 2,
            stonk_id = stonk_id
        )

        # Fourth row, whether the best algorithm is investing in this stonk.
        gradient_color, image_paste = algorithm_choices[algorithm_portfolio[stonk.internal_name] >= 1]
        gradient = mcolors.LinearSegmentedColormap.from_list('gradient', [gradient_color, backgrounds[stonk_id % 2]], N=47)

        render_gradient(
            gradient = gradient,
            vertical_position = 3,
            stonk_id = stonk_id
        )

        img.paste(image_paste, (692 + (stonk_id * 435), 617), image_paste)

    # Save the final image.
    img.save(f"images{SLASH}generated{SLASH}stonk_report.png", quality=90)

######################################################################################################################################
##### CHESS MATCH ####################################################################################################################
######################################################################################################################################

def chess_match(
        bot_white: str,
        bot_black: str,
        game_data: dict
    ) -> None:
    """Generates the cover image for the daily Chess game and saves it to 'images/generated/chess_match.png'

    Args:
        bot_white (str): The name of the bot playing the white pieces.
        bot_black (str): The name of the bot playing the black pieces.
    """
    img = PIL_Image.open(f"images{SLASH}bases{SLASH}chess_match_base.png").copy().convert("RGBA")

    ### Rendering the chess board.

    board = u_chess.get_board_from_pgn(game_data.get("pgn"))
    board_path = u_chess.render_board(board)
    board_image = PIL_Image.open(board_path).copy().convert("RGBA")
    board_image = board_image.resize((390, 390))

    img.paste(board_image, (406, 105))

    #############################

    font_path = f"images{SLASH}bases{SLASH}verdana.ttf"

    imgDraw = PIL_ImageDraw.Draw(img)

    white_name = bot_white.replace("_"," ").title()
    black_name = bot_black.replace("_"," ").title()

    max_font_size = 57
    y_size = 95
    x_size = 356
    x_multiplier = 0.95
    
    # The coordinates of the top left parts of the text background boxes.
    # The left sides of the boxes is the same, so only one variable is needed.
    box_left = 33
    box_white_top = 388
    box_black_top = 115

    # Font sizes.
    ending_x_size = x_size * x_multiplier

    font_size_white = 1
    font_size_black = 1

    # White font size.
    font_white = PIL_ImageFont.truetype(font_path, font_size_white)
    while font_white.getlength(white_name) < ending_x_size:
        # iterate until the text size is just larger than the criteria
        font_size_white += 1
        font_white = PIL_ImageFont.truetype(font_path, font_size_white)
    font_white = PIL_ImageFont.truetype(font_path, font_size_white - 1)

    if font_size_white > max_font_size:
        font_white = PIL_ImageFont.truetype(font_path, size=max_font_size)

    # Black font size.
    font_black = PIL_ImageFont.truetype(font_path, font_size_black)
    while font_black.getlength(black_name) < ending_x_size:
        # iterate until the text size is just larger than the criteria
        font_size_black += 1
        font_black = PIL_ImageFont.truetype(font_path, font_size_black)
    font_black = PIL_ImageFont.truetype(font_path, font_size_black - 1)

    if font_size_black > max_font_size:
        font_black = PIL_ImageFont.truetype(font_path, size=max_font_size)

    # Figure out where the text should go.
    white_bounds = imgDraw.textbbox((0, 0), white_name, font=font_white)
    black_bounds = imgDraw.textbbox((0, 0), black_name, font=font_black)

    white_x_coord = (x_size - white_bounds[2]) / 2 + box_left
    black_x_coord = (x_size - black_bounds[2]) / 2 + box_left

    white_y_coord = (y_size - white_bounds[3]) / 2 + box_white_top
    black_y_coord = (y_size - black_bounds[3]) / 2 + box_black_top

    # Write the name of the bot playing white.
    imgDraw.text((white_x_coord, white_y_coord), white_name, (0, 0, 0), font=font_white, align="center", stroke_width=1)

    # Write the name of the bot playing black.
    imgDraw.text((black_x_coord, black_y_coord), black_name, (0, 0, 0), font=font_black, align="center", stroke_width=1)
    
    # Elo ratings:
    increase_color = (0, 230, 0)
    decrease_color = (230, 0, 0)

    elo_font = PIL_ImageFont.truetype(font_path, size=30)

    # White elo
    imgDraw.text((242, 341), str(game_data["white_elo"]), (0, 0, 0), font=elo_font, align="center", stroke_width=1)
    white_width = imgDraw.textlength(str(game_data["white_elo"]), elo_font)

    delta = str(game_data["delta_white_elo"])
    if game_data["delta_white_elo"] > 0:
        delta = f"+{delta}"
        color = increase_color
    else:
        color = decrease_color

    imgDraw.text((242 + white_width + 10, 341), delta, color, font=elo_font, align="center", stroke_width=1)

    # Black elo
    imgDraw.text((242, 218), str(game_data["black_elo"]), (0, 0, 0), font=elo_font, align="center", stroke_width=1)
    black_width = imgDraw.textlength(str(game_data["black_elo"]), elo_font)

    delta = str(game_data["delta_black_elo"])
    if game_data["delta_black_elo"] > 0:
        delta = f"+{delta}"
        color = increase_color
    else:
        color = decrease_color

    imgDraw.text((242 + black_width + 10, 218), delta, color, font=elo_font, align="center", stroke_width=1)



    # Save the final image.
    img.save(f"images{SLASH}generated{SLASH}chess_match.png", quality=90)
    
    # 242, 221

######################################################################################################################################
##### CHESS PUZLES ###################################################################################################################
######################################################################################################################################

def chess_puzzle(
        puzzle_data: dict,
        elo_data: dict
    ) -> None:
    correct_image = PIL_Image.open(f"images{SLASH}bases{SLASH}check.png").resize((50, 50)).convert("RGBA")
    incorrect_image = PIL_Image.open(f"images{SLASH}bases{SLASH}x.png").resize((50, 50)).convert("RGBA")
    
    def prep_board(board: PIL_Image.Image) -> PIL_Image.Image:
        board = board.resize((390, 390))
        outside = PIL_Image.new("RGBA", (394, 394), "#bfbfbf")
        outside.paste(board, (2, 2))
        return outside
        
    def index_to_grid(index: int) -> tuple[int]:
        x = index % PER_ROW
        y = index // PER_ROW
        
        if (number_of_bots - index - 1) < EXTRA_BOTS:
            x += -1/2 * EXTRA_BOTS + PER_ROW / 2
            
        return (int(SIDE_BUFFERS + x * (WIDTH_PER_BOT + 12)), TOP_OFFSET + y * (HEIGHT_PER_BOT + 12))

    font_path = f"images{SLASH}bases{SLASH}verdana.ttf"
    
    number_of_bots = len(puzzle_data["bots"])
    
    TOTAL_ROWS = math.isqrt(number_of_bots)
    PER_ROW = math.ceil(number_of_bots / TOTAL_ROWS)
    EXTRA_BOTS = number_of_bots % PER_ROW
    
    # Height:
    TOP_OFFSET = 467
    BOTTOM_BUFFER = 40
    HEIGHT_PER_BOT = 95 + 394 + 52 # 95 (height of the bot label) + 394 (height of the board itself) + 52 (height of the elo label)
    
    # Width:
    SIDE_BUFFERS = 40
    WIDTH_PER_BOT = 5 + 394 + 5 # 5 (white outline on the left) + 394 (width of the board itself) + 5 (white outline on the right)
    
    total_image_height = TOP_OFFSET + (12 + HEIGHT_PER_BOT) * TOTAL_ROWS + BOTTOM_BUFFER - 12 # Subtract 12 to remove the buffer between bots for the last row.
    total_image_width = SIDE_BUFFERS * 2 + (12 + WIDTH_PER_BOT) * PER_ROW - 12 # Subtract 12 to remove the buffer between bots for the last column.
    
    img = PIL_Image.open(f"images{SLASH}bases{SLASH}chess_puzzles.png").copy().convert("RGBA")
    img = img.resize((total_image_width, total_image_height))
    img_draw = PIL_ImageDraw.ImageDraw(img)
    
    puzzle_default = prep_board(u_chess.render_board(
        board = chess.Board(puzzle_data["puzzle"]["fen"]),
        last_move=chess.Move.from_uci(puzzle_data["puzzle"]["last_move"]),
        return_image=True
    ))
    
    img.paste(puzzle_default, (img.width//2 - 394//2, 40))
    img_draw.line([(50, 450), (img.width-51, 450)], width=9)
    
    name_y_size = 95
    name_x_size = 356
    namx_x_size_multiplier = 0.95
    ending_name_x_size = name_x_size * namx_x_size_multiplier
    max_name_font_size = 57
    
    for index, bot_name in enumerate(puzzle_data["bots"].keys()):
        data = puzzle_data["bots"][bot_name]
        
        base_x, base_y = index_to_grid(index)
        
        # Draw the background rectangle:
        img_draw.rounded_rectangle([(base_x, base_y), (base_x + WIDTH_PER_BOT, base_y + HEIGHT_PER_BOT)], radius=25, fill="#ffffff")
        
        # Draw the board:
        if data["correct"]:
            highlight_light = "#6ad16c"
            highlight_dark = "#45aa3b"
        else:
            highlight_light = "#d1716a"
            highlight_dark = "#aa3b3f"
        
        bot_puzzle_board = prep_board(u_chess.render_board(
            board = chess.Board(data["ending_fen"]),
            last_move=chess.Move.from_uci(data["last_move"]),
            last_move_light = highlight_light,
            last_move_dark = highlight_dark,
            return_image=True
        ))
    
        img.paste(bot_puzzle_board, (base_x + 5, base_y + 95))
        
        # Write the bot's name:
        fancy_name = u_chess.format_name(bot_name)
        box_left = base_x + 20
        box_top = base_y
        name_font_width = 1
        
        # White font size.
        name_font = PIL_ImageFont.truetype(font_path, name_font_width)
        while name_font.getlength(fancy_name) < ending_name_x_size:
            # iterate until the text size is just larger than the criteria
            name_font_width += 1
            name_font = PIL_ImageFont.truetype(font_path, name_font_width)

        if name_font_width > max_name_font_size:
            name_font = PIL_ImageFont.truetype(font_path, size=max_name_font_size)
        else:
            name_font = PIL_ImageFont.truetype(font_path, name_font_width - 1)
        
        name_bounds = img_draw.textbbox((0, 0), fancy_name, font=name_font)

        white_x_coord = (name_x_size - name_bounds[2]) / 2 + box_left
        white_y_coord = (name_y_size - name_bounds[3]) / 2 + box_top

        # Write the name of the bot playing white.
        img_draw.text((white_x_coord, white_y_coord), fancy_name, (0, 0, 0), font=name_font, align="center", stroke_width=1)
        
        # Elo ratings:
        increase_color = (0, 230, 0)
        decrease_color = (230, 0, 0)

        elo_font = PIL_ImageFont.truetype(font_path, size=30)

        # White elo
        img_draw.text((base_x + 20, base_y + 494), str(elo_data[bot_name]["elo"]), (0, 0, 0), font=elo_font, align="center", stroke_width=1)
        elo_width = img_draw.textlength(str(elo_data[bot_name]["elo"]), elo_font)

        delta = str(elo_data[bot_name]["delta"])
        if elo_data[bot_name]["delta"] > 0:
            delta = f"+{delta}"
            color = increase_color
        else:
            color = decrease_color

        img_draw.text((base_x + elo_width + 30, base_y + 494), delta, color, font=elo_font, align="center", stroke_width=1)
        
        # Check/X stamp:
        if data["correct"]:
            to_paste = correct_image
        else:
            to_paste = incorrect_image
            
        img.paste(to_paste.copy(), (base_x + WIDTH_PER_BOT - 51, base_y + HEIGHT_PER_BOT - 51), to_paste.copy())
    
    # Save the final image.
    img.save(f"images{SLASH}generated{SLASH}chess_puzzle.png", quality=90)
    
    

######################################################################################################################################
##### COLOR ##########################################################################################################################
######################################################################################################################################

def solid_color(
        color: tuple[int],
        xsize: int = 255,
        ysize: int = 255
    ):
    """Generates an image of a solid color."""
    img = PIL_Image.new("RGB", (xsize, ysize), color)

    output = io.BytesIO()
    img.save(output, "png")
    output.seek(0)

    return output



######################################################################################################################################
##### AVATAR #########################################################################################################################
######################################################################################################################################

def avatar_decoration(
        avatar: io.BytesIO,
        decoration: io.BytesIO,
        avatar_size: tuple[int] = (244, 244),
        decoration_size: tuple[int] = (288, 288)
):

    # Create image objects.
    final = PIL_Image.new("RGBA", decoration_size, "#00000000")
    avatar = PIL_Image.open(avatar).convert("RGBA").resize(avatar_size)
    decoration = PIL_Image.open(decoration).convert("RGBA").resize(decoration_size)

    # Create circular mask for avatar.
    mask = PIL_Image.new("L", avatar_size, 0)
    mask_draw = PIL_ImageDraw.Draw(mask)
    mask_draw.ellipse(((0,0), avatar_size), fill=255)

    # Mask avatar with circular mask.
    avatar.putalpha(mask)

    # Place images on base.
    final.paste(avatar, ((decoration_size[0] - avatar_size[0]) // 2, (decoration_size[1] - avatar_size[1]) // 2))
    final = PIL_Image.alpha_composite(final, decoration)

    # Render final image.
    output = io.BytesIO()
    final.save(output, "png")
    output.seek(0)

    return output