"""This cog is for commands that relate to the bingo game."""

from discord.ext import commands
import discord
import typing
import math
import asyncio
from os.path import sep as SLASH

# pip install fuzzywuzzy
# pip install python-Levenshtein
from fuzzywuzzy import fuzz

import sys

import utility.bingo as u_bingo
import utility.images as u_images
import utility.checks as u_checks
import utility.text as u_text
import utility.custom as u_custom
import utility.interface as u_interface
import utility.converters as u_converters
import utility.files as u_files
import utility.detection as u_detection

database = None # type: u_files.DatabaseInterface

class Bingo_cog(u_custom.CustomCog, name="Bingo", description="Commands for running the bingo game!"):
    bot = None

    creating_objectives = [] # List of user ids that are currently making objectives.

    async def hourly_task(self):
        """Code that runs for every hour."""
        self.creating_objectives.clear()
    
    ######################################################################################################################################################
    ##### UTILTIY FUNCTIONS ##############################################################################################################################
    ######################################################################################################################################################

    def _determine_coordinate(self, board_size: int, x_input: int, y_input: int | None) -> (int | str):
        """Determines a tile id coordinate from X and Y inputs. A raw tile id can also be passed.
        This can return a string, in which that string should be sent as a Discord message."""

        # If the y input is not None, then the inputs should be parsed as x and y coordinates.
        if y_input is not None:
            if not(1 <= x_input <= board_size):
                return "The X coordinate must be between 1 and {}.".format(board_size)
            
            if not(1 <= y_input <= board_size):
                return "The Y coordinate must be between 1 and {}.".format(board_size)
            
            return x_input - 1 + ((y_input - 1) * board_size)
        elif not(1 <= x_input <= board_size ** 2):
            return "The tile id must be between 1 and {}.".format(board_size ** 2)
        
        return x_input - 1
    
    def _match_tile_list(self, board: str) -> list[dict]:
        """Returns a tile list based on a string input. 'daily' will be the daily tile list and 'weekly' will be the weekly tile list."""
        match board:
            case "daily":
                return u_bingo.tile_list_5x5(database=database)
            case "weekly":
                return u_bingo.tile_list_9x9(database=database)
    
    def _generate_list(self, tile_list: list[dict], base_tile_list: list[dict], title: str, page: (int | None) = 0, type_text: str = "daily", command: str = "%objective list", page_size: int = 6, identifier: str = "in the daily tile list") -> discord.Embed:
        """Generates a list of objectives for the objective list and board stats commands. Returns a Discord.py embed object.
        
        Parameters:
        - tile_list (list[dict]): The tile list that will be used. All the items in this can be viewed, so if you only want a set you'll need to set that up and pass the modified version to this.
        - base_tile_list (list[dict]): The tile list the items from the tile_list came from.
        - title (str): The title of this, note that ' page #' will be added after this.
        - page (int) = 0: The input for the page. This function will correct it if it's outside of acceptable boundaries, so you don't need to worry about that.
        - type_text (str) = "daily": The type of this, 'daily' and 'weekly' are what's expected, but this is not enforced and other things can be provided.
        - command (str) = "%objective list": The command used to invoke this. Note that the command prefix will need to be provided, as this function does not add it.
        - page_size (int) = 6: The amount of objectives that will be shown on each page.
        - identifier (int) = "in the daily tile list": This is a piece of text that will be put at the end of the description before the objectives."""

        if page is None:
            page = 0
        else:
            page -= 1

        page_count = math.ceil(len(tile_list) / page_size)

        if page >= page_count:
            page = page_count - 1
        if page < 0:
            page = 0

        fields = []

        lower_bound = page_size * page
        upper_bound = min(len(tile_list), page_size * (page + 1))

        for objective_id in range(lower_bound, upper_bound):
            objective_data = tile_list[objective_id]

            fields.append((objective_data["name"], "Objective #{}.\n\nDescription:\n{}".format(base_tile_list.index(objective_data), objective_data["description"]), True))
        
        embed = u_interface.gen_embed(
            title = "{} page {}".format(title, page + 1),
            description = f"Page {page + 1} of {page_count}. You can get other pages via `{command} [page number]`\n\nTo get more information about an objective, use `%objective {type_text} [objective id]`\n\nObjectives {lower_bound} to {upper_bound - 1} {identifier}:",
            fields = fields
        )

        return embed

    
    
    
    
    
    
    ######################################################################################################################################################
    ##### OBJECTIVE ######################################################################################################################################
    ######################################################################################################################################################

    @commands.group(
        name = "objective",
        brief = "Get an objective from a tile list.",
        description = "Get information about an objective.\nTo see the information about an objective on the current board, use '%[board|weekly] stats'.\nTo search for an objective, use '%objective search [daily|weekly] [search term]'\nTo get a list of objectives, use '%objective list [daily|weekly]'",
        pass_context = True,
        invoke_without_command = True
    )
    async def objective(self, ctx,
            board: typing.Optional[str] = commands.parameter(description = "Which board to use, 'daily' or 'weekly'."),
            objective: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The id of the objective to look up.")
        ):
        if ctx.invoked_subcommand is not None:
            return
        
        if board not in ["daily", "weekly"]:
            await ctx.reply("You must specify what set of objectives you want. `daily` and `weekly` are the current options.")
            return
        
        if objective is None:
            await ctx.reply("You must provide an objective id.")
            return
        
        tile_list = self._match_tile_list(board)
        
        if not (len(tile_list)> objective >= 0):
            await ctx.reply(f"The objective id must be between 0 and {len(tile_list) - 1}.")
            return
        
        objective_data = tile_list[objective]

        emojis = ["<:x_:1189696918645907598>", "<:check:1189696905077325894>"]

        center = emojis[objective_data.get("center", False)]
        solo = emojis[objective_data.get("solo", False)]
        disabled = emojis[objective_data.get("disabled", False)]

        internal_id = f"{board[0]}{objective}"
        auto_detection = "<:check:1189696905077325894> (Note that it might not be found in every situation.)" if internal_id in u_detection.all_detection else "<:x_:1189696918645907598>"

        embed = u_interface.gen_embed(
            title = objective_data["name"],
            description = f"Objective {objective} on the {board} board.\n\nDescription:\n{objective_data['description']}\n\nCenter objective: {center}\nSolo objective: {solo}\nDisabled: {disabled}\nHas auto detection: {auto_detection}\n\nYou can use `%[board|weekly] stats` to see information about the objectives on the current board.\nYou can use `%objective search [daily|weekly] [search term]` to search for an objective.\nYou can also use `%objective list [daily|weekly]` to get a list of the possible objectives.",
        )

        await ctx.reply(embed=embed)

    
    
    
    
    
    
    ######################################################################################################################################################
    ##### OBJECTIVE SEARCH ###############################################################################################################################
    ######################################################################################################################################################
    
    @objective.command(
        name = "search",
        brief = "Search for an objective.",
        description = "Search for an objective on the daily or weekly board.\nTo get information about a specific objective, use '%objective [daily|weekly] [objective id]'\nTo get a list of objectives, use '%objective list [daily|weekly]'"
    )
    async def objective_search(self, ctx,
            board: typing.Optional[str] = commands.parameter(description = "Which board to use, 'daily' or 'weekly'."),
            *, search: typing.Optional[str] = commands.parameter(description = "The text to search for.")
        ):
        if board not in ["daily", "weekly"]:
            await ctx.reply("You must specify what set of objectives you want. `daily` and `weekly` are the current options.")
            return

        if search is None:
            await ctx.reply("You must provide a search term.")
            return
        
        
        def fuzzy_search(search, tile_list):
            result = []

            for objective_id, objective_data in enumerate(tile_list):
                name_similarity = fuzz.partial_ratio(search.lower(), objective_data.get("name", "").lower())
                description_similarity = fuzz.partial_ratio(search.lower(), objective_data.get("description", "").lower())

                result.append((objective_data, objective_id, max(name_similarity, description_similarity)))

            return sorted(result, key=lambda x: x[2], reverse=True)
        
        tile_list = self._match_tile_list(board)

        returned = fuzzy_search(search, tile_list)

        embed = u_interface.gen_embed(
            title = "Search results:",
            description = f"You can use `%objective {board} <objective id>` to get more information about an objective.\nResult from searching the text `{u_text.ping_filter(search)}` in the {board} objective list:",
            fields = [
                (returned[i][0]["name"], f"Objective id: {returned[i][1]}\n\nDescription:\n{returned[i][0]['description']}", True)
                for i in range(3)
            ]
        )

        await ctx.reply(embed=embed)

    
    
    
    
    
    
    ######################################################################################################################################################
    ##### OBJECTIVE LIST #################################################################################################################################
    ######################################################################################################################################################

    @objective.command(
        name = "list",
        brief = "Provides a list of objectives.",
        description = "Get a list of all the daily or weekly objectives.\nTo get information about a specific objective, use '%objective [daily|weekly] [objective id]'\nTo search for an objective, use '%objective search [daily|weekly] [search term]'"
    )
    async def objective_list(self, ctx,
            board: typing.Optional[str] = commands.parameter(description = "Which board to use, 'daily' or 'weekly'."),
            page: typing.Optional[int] = commands.parameter(description = "An integer for what page to use.", displayed_default = 1)
        ):
        if board not in ["daily", "weekly"]:
            await ctx.reply("You must specify what set of objectives you want. `daily` and `weekly` are the current options.")
            return
        
        tile_list = self._match_tile_list(board)

        embed = self._generate_list(
            tile_list = tile_list,
            base_tile_list = tile_list,
            title = "{} objective list".format(board.title()),
            page = page,
            type_text = board,
            command = "%objective list",
            identifier = "in the {} tile list".format(board)
        )

        await ctx.reply(embed=embed)

    
    
    
    
    
    
    ######################################################################################################################################################
    ##### OBJECTIVE ADD ##################################################################################################################################
    ######################################################################################################################################################

    @objective.command(
        name = "add",
        brief = "Adds an objective.",
        description = "Adds an objective to either the 5x5 or 9x9 tile lists.\nIt will prompt you to provide the required information, so you just need to say the board type in the initial command."
    )
    @commands.check(u_checks.bingo_tick_check)
    async def objective_add(self, ctx,
            board: typing.Optional[str] = commands.parameter(description = "Which board to append to, 'daily' or 'weekly'."),
        ):
        if ctx.author.id in self.creating_objectives:
            return
        
        if board not in ["daily", "weekly"]:
            await ctx.reply("You must specify what set of objectives you want. `daily` and `weekly` are the current options.")
            return
        
        self.creating_objectives.append(ctx.author.id)

        objective_info = {
            "name": None,
            "description": None,
            "center": False
        }
        if board == "daily":
            objective_info["solo"] = False

        def check(m: discord.Message) -> bool:
            return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id
        
        async def prompt(message: discord.Message, content: str) -> discord.Message | None:
            await message.reply(content)
            try:
                msg = await self.bot.wait_for('message', check = check, timeout = 60.0)
                return msg
            except asyncio.TimeoutError:
                await message.reply("You have taken too long to respond, please start over.")
                return None
        
        name = await prompt(message = ctx.message, content = "What is the name of the objective?")
        if name is None:
            self.creating_objectives.remove(ctx.author.id)
            return
        objective_info["name"] = name.content
        
        description = await prompt(message = name, content = "What is the description of the objective?")
        if description is None:
            self.creating_objectives.remove(ctx.author.id)
            return
        objective_info["description"] = description.content
        
        center = await prompt(message = description, content = "Yes or no, should the objective be able to be in the center of the board?")
        if center is None:
            self.creating_objectives.remove(ctx.author.id)
            return
        result = False
        try:
            result = u_converters.extended_bool(center.content)
        except commands.BadArgument:
            self.creating_objectives.remove(ctx.author.id)
            await center.reply("I don't recognize that, please start over.")
            return

        objective_info["center"] = bool(result)
        
        if board == "daily":
            solo = await prompt(message = center, content = "Yes or no, can the objective be completed solo?")
            if solo is None:
                self.creating_objectives.remove(ctx.author.id)
                return
            result = False
            try:
                result = u_converters.extended_bool(solo.content)
            except commands.BadArgument:
                self.creating_objectives.remove(ctx.author.id)
                await solo.reply("I don't recognize that, please start over.")
                return

            objective_info["solo"] = bool(result)
        
        tile_list = self._match_tile_list(board)
        
        tile_list.append(objective_info)

        if board == "daily":
            database.save("bingo", "tile_list_5x5", data=tile_list)
        elif board == "weekly":
            database.save("bingo", "tile_list_9x9", data=tile_list)

        emojis = ["<:x_:1189696918645907598>", "<:check:1189696905077325894>"]

        embed = u_interface.gen_embed(
            title = "Added objective #{}".format(len(tile_list) - 1),
            description = "Objective information:\nTitle: {}\nDescription: {}\nCenter: {}\nSolo: {}".format(
                objective_info["name"],
                objective_info["description"],
                emojis[objective_info["center"]],
                emojis[objective_info.get("solo", False)]
            )
        )

        await ctx.reply(embed=embed)
        
        self.creating_objectives.remove(ctx.author.id)

    
    
    
    
    
    
    ######################################################################################################################################################
    ##### OBJECTIVE MODIFY ###############################################################################################################################
    ######################################################################################################################################################

    @objective.command(
        name = "modify",
        brief = "Modifies an objective.",
        description = "Modifies an objective in either the 5x5 or 9x9 tile lists.\n\nCurrently used modification types:\n- name (text)\n- description (text)\n- center (boolean)\n- solo (boolean)\n- disabled (boolean)"
    )
    @commands.check(u_checks.bingo_tick_check)
    async def objective_modify(self, ctx,
            board: typing.Optional[str] = commands.parameter(description = "Which board to append to, 'daily' or 'weekly'."),
            objective_id: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The id of the objective to modify."),
            modification_type: typing.Optional[str] = commands.parameter(description = "The type of data to modify. See above for list."),
            *, new_data: typing.Optional[str] = commands.parameter(description = "The new data to use.")
        ):
        if None in [board, objective_id, modification_type]:
            await ctx.reply("You must provide a board, objective id, and modification type.")
            return
        
        if board not in ["daily", "weekly"]:
            await ctx.reply("You must specify what set of objectives you want. `daily` and `weekly` are the current options.")
            return
        
        tile_list = self._match_tile_list(board)
        
        if objective_id >= len(tile_list):
            await ctx.reply("The objective id must be between 0 and {}.".format(len(tile_list) - 1))
            return
        
        objective_info = tile_list[objective_id]
        objective_copy = objective_info.copy()

        try:
            if modification_type == "name":
                objective_info["name"] = new_data
            elif modification_type == "description":
                objective_info["description"] = new_data
            elif modification_type == "center":
                objective_info["center"] = u_converters.extended_bool(new_data)
            elif modification_type == "solo":
                objective_info["solo"] = u_converters.extended_bool(new_data)
            elif modification_type == "disabled":
                objective_info["disabled"] = u_converters.extended_bool(new_data)
            else:
                await ctx.reply("I don't recognize that modification type, please try again.")
                return
        except commands.BadArgument:
            await ctx.reply("I don't recognize the new data provided, please try again.")
            return

        tile_list[objective_id] = objective_info

        if board == "daily":
            database.save("bingo", "tile_list_5x5", data=tile_list)
        elif board == "weekly":
            database.save("bingo", "tile_list_9x9", data=tile_list)

        emojis = ["<:x_:1189696918645907598>", "<:check:1189696905077325894>"]

        embed = u_interface.gen_embed(
            title = "Modified objective #{}".format(objective_id),
            fields = [
                ("Old information:", "Title: {}\nDescription: {}\nCenter: {}\nSolo: {}\nDisabled: {}".format(
                objective_copy["name"],
                objective_copy["description"],
                emojis[objective_copy["center"]],
                emojis[objective_copy.get("solo", False)],
                emojis[objective_copy.get("disabled", False)]
                ), False),
                ("New information:", "Title: {}\nDescription: {}\nCenter: {}\nSolo: {}\nDisabled: {}".format(
                objective_info["name"],
                objective_info["description"],
                emojis[objective_info["center"]],
                emojis[objective_info.get("solo", False)],
                emojis[objective_info.get("disabled", False)]
                ), False)
            ]
        )
        await ctx.reply(embed=embed)

    
    
    
    
    
    
    ######################################################################################################################################################
    ##### OBJECTIVE REMOVE ###############################################################################################################################
    ######################################################################################################################################################

    @objective.command(
        name = "remove",
        aliases = ["delete"],
        brief = "Removes an objective.",
        description = "Removes an objective."
    )
    @commands.is_owner()
    async def objective_remove(self, ctx,
            board: typing.Optional[str] = commands.parameter(description = "Which board to append to, 'daily' or 'weekly'."),
            objective_id: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The id of the objective to modify.")
        ):
        if None in [board, objective_id]:
            await ctx.reply("You must provide a board and objective id.")
            return
        
        if board not in ["daily", "weekly"]:
            await ctx.reply("You must specify what set of objectives you want. `daily` and `weekly` are the current options.")
            return
        
        tile_list = self._match_tile_list(board)
        
        if objective_id >= len(tile_list):
            await ctx.reply("The objective id must be between 0 and {}.".format(len(tile_list) - 1))
            return
        
        objective_data = tile_list.pop(objective_id)

        if board == "daily":
            database.save("bingo", "tile_list_5x5", data=tile_list)
        elif board == "weekly":
            database.save("bingo", "tile_list_9x9", data=tile_list)

        emojis = ["<:x_:1189696918645907598>", "<:check:1189696905077325894>"]

        embed = u_interface.gen_embed(
            title = "Removed objective #{}".format(objective_id),
            fields = [
                ("Objective information:", "Title: {}\nDescription: {}\nCenter: {}\nSolo: {}\nDisabled: {}".format(
                objective_data["name"],
                objective_data["description"],
                emojis[objective_data["center"]],
                emojis[objective_data.get("solo", False)],
                emojis[objective_data.get("disabled", False)]
                ), False)
            ]
        )
        await ctx.reply(embed=embed)
        
        



    
    
    
    
    
    
    ######################################################################################################################################################
    ##### BOARD (daily) ##################################################################################################################################
    ######################################################################################################################################################
    
    @commands.group(
        name = "board",
        aliases = ["daily"],
        brief = "Shows the current 5x5 bingo board.",
        description = "Shows the current 5x5 bingo board.",
        pass_context = True,
        invoke_without_command = True
    )
    async def board(self, ctx):
        if ctx.invoked_subcommand is not None:
            return
        
        live_data = u_bingo.live(database=database)

        u_images.render_board_5x5(
            database = database,
            tile_string = live_data["daily_tile_string"],
            enabled = live_data["daily_enabled"]
        )

        await ctx.reply(content="This is bingo board #{}!".format(live_data["daily_board_id"]), file=discord.File(r'images/generated/bingo_board.png'))

    
    
    
    
    
    
    ######################################################################################################################################################
    ##### BOARD STATS (daily) ############################################################################################################################
    ######################################################################################################################################################
    
    @board.command(
        name = "stats",
        brief = "Get information about the current board.",
        description = "Get information about the current board."
    )
    async def daily_stats(self, ctx,
            page: typing.Optional[int] = commands.parameter(description = "An integer for what page to use.", displayed_default = 1)
        ):
        base_tile_list = u_bingo.tile_list_5x5(database=database)

        live_data = u_bingo.live(database=database)

        live_list = u_text.split_chunks(live_data["daily_tile_string"], 3)

        tile_list = [base_tile_list[int(objective_id)] for objective_id in live_list]

        embed = self._generate_list(
            tile_list = tile_list,
            base_tile_list = base_tile_list,
            title = "5x5 board stats",
            page = page,
            type_text = "daily",
            command = "%board stats",
            identifier = "on the 5x5 board"
        )

        await ctx.reply(embed=embed)

    
    
    
    
    
    
    ######################################################################################################################################################
    ##### TICK (daily) ###################################################################################################################################
    ######################################################################################################################################################
    
    @commands.group(
        name = "tick",
        brief = "Tick off a tile on the bingo board.",
        description = "Tick off a tile on the bingo board."
    )
    @commands.check(u_checks.bingo_tick_check)
    async def tick(self, ctx,
            coord_x: typing.Optional[int] = commands.parameter(description = "The X coordinate of the tile to tick."),
            coord_y: typing.Optional[int] = commands.parameter(description = "The Y coordinate of the tile to tick.")
        ):
        if ctx.invoked_subcommand is not None:
            return
        
        # Ensure at least 1 number is provided, if just an x coordinate is provided, it is used as a tile id.
        if coord_x is None:
            await ctx.reply("You must provide a coordinate, as a single tile id or an X and Y coordinate.\nYou can use `%tick guide` to get a guide.")
            return
        
        # Figure out the location of the affected tile via an x and y coordinate or just a single tile id.
        tile_id = self._determine_coordinate(5, coord_x, coord_y)

        # If self._determine_coordinate returned a string there was a problem, and so just send that string.
        if isinstance(tile_id, str):
            await ctx.reply(tile_id)
            return
        
        # If the tile is already ticked.
        if u_bingo.get_tile_state_5x5(database=database, tile_id=tile_id):
            await ctx.reply("That tile is already ticked.")
            return
        
        # Tick the tile, and then convert the result into three variables.
        pre_tick_bingos, post_tick_bingos, objective_id, new_live = u_bingo.tick_5x5(database=database, bot=self.bot, tile_id=tile_id)

        # Count the bingos.
        pre_tick_bingos = u_bingo.count_bingos(pre_tick_bingos, 5)
        post_tick_bingos = u_bingo.count_bingos(post_tick_bingos, 5)

        # Determine how many bingos were made.
        bingos_made = post_tick_bingos - pre_tick_bingos
        
        # Get the name and description of the tile that was ticked.
        objective_data = u_bingo.get_objective_5x5(database=database, objective_id=objective_id)

        # Make the bonus text sent if a bingo is made.
        if bingos_made >= 1:
            bingo_bonus = "And that made {}! {}".format(u_text.smart_text(bingos_made, "bingo"), ":tada:" * bingos_made)
        else:
            bingo_bonus = ""

        await ctx.reply("It's been ticked off!\n\nThe objective was id {}, which has the name `{}` and description:\n{}\n\n{}".format(objective_id, objective_data["name"], objective_data["description"], bingo_bonus))


    
    
    
    
    
    
    ######################################################################################################################################################
    ##### UNTICK (daily) #################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "untick",
        brief = "Untick a tile on the bingo board.",
        description = "Untick a tile on the bingo board."
    )
    @commands.check(u_checks.bingo_tick_check)
    async def untick(self, ctx,
            coord_x: typing.Optional[int] = commands.parameter(description = "The X coordinate of the tile to untick."),
            coord_y: typing.Optional[int] = commands.parameter(description = "The Y coordinate of the tile to untick.")
        ):        
        # Ensure at least 1 number is provided, if just an x coordinate is provided, it is used as a tile id.
        if coord_x is None:
            await ctx.reply("You must provide a coordinate, as a single tile id or an X and Y coordinate.\nYou can use `%tick guide` to get a guide.")
            return
        
        # Figure out the location of the affected tile via an x and y coordinate or just a single tile id.
        tile_id = self._determine_coordinate(5, coord_x, coord_y)

        # If self._determine_coordinate returned a string there was a problem, and so just send that string.
        if isinstance(tile_id, str):
            await ctx.reply(tile_id)
            return
        
        # If the tile isn't ticked in the first place.
        if not u_bingo.get_tile_state_5x5(database=database, tile_id=tile_id):
            await ctx.reply("That tile isn't already ticked.")
            return
        
        # Tick the tile, and then convert the result into two variables.
        pre_tick_bingos, post_tick_bingos, new_live = u_bingo.untick_5x5(database=database, bot=self.bot, tile_id=tile_id)

        # Count the bingos.
        pre_tick_bingos = u_bingo.count_bingos(pre_tick_bingos, 5)
        post_tick_bingos = u_bingo.count_bingos(post_tick_bingos, 5)

        # Determine how many bingos were removed.
        bingos_unmade = pre_tick_bingos - post_tick_bingos

        # Make the bonus text sent if a bingo is reversed by this.
        if bingos_unmade >= 1:
            bingo_bonus = "And that undid {}! {}".format(u_text.smart_text(bingos_unmade, "bingo"), ":tada:" * bingos_unmade)
        else:
            bingo_bonus = ""

        await ctx.reply("It's been unticked!\n\n{}".format(bingo_bonus))


    
    
    
    
    
    
    ######################################################################################################################################################
    ##### TICK GUIDE (daily) #############################################################################################################################
    ######################################################################################################################################################
    
    @tick.command(
        name = "guide",
        brief = "Get a handy tile id guide for ticking.",
        description = "Get a handy tile id guide for ticking."
    )
    @commands.check(u_checks.bingo_tick_check)
    async def tick_guide(self, ctx):
        u_images.render_board(
            database = database,
            tile_string = "".join([f"{i:03}" for i in range(25)]),
            enabled = 0,
            board_size = 5,
            tile_list = [{"name": f"{i + 1} ({(i % 5) + 1}, {(i // 5) + 1})"} for i in range(25)],
            force = True
        )

        await ctx.reply(content="Here you go!", file=discord.File(r'images/generated/bingo_board.png'))



    
    
    
    
    
    
    ######################################################################################################################################################
    ##### BOARD GENERATE (daily) #########################################################################################################################
    ######################################################################################################################################################
    
    @board.command(
        name = "generate",
        brief = "Generates a 5x5 bingo board.",
        description = "Generates the tile string for a 5x5 bingo board.",
        hidden = True
    )
    async def board_generate(self, ctx):
        await ctx.reply("`{}`".format(u_bingo.generate_5x5_board(database=database)))

    
    
    
    
    
    
    ######################################################################################################################################################
    ##### BOARD RENDER (daily) ###########################################################################################################################
    ######################################################################################################################################################
    
    @board.command(
        name = "render",
        brief = "Renders a custom 5x5 board.",
        description = "Renders a custom 5x5 board.\nYou can get a random tile string using the '%board generate' command."
    )
    async def board_render(self, ctx,
            tile_string: typing.Optional[str] = commands.parameter(description = "A 75 character string that says what's on each tile."),
            enabled_number: typing.Optional[u_converters.parse_int] = commands.parameter(description = "Number between 0 and 2^25 - 1 that defines completed tiles.")
        ):
        if tile_string is None:
            await ctx.reply("You must provide a tile string.\nYou can get a random tile string via the `%board generate` command.")
            return
        
        tile_string = tile_string.replace(",", "")
        
        if len(tile_string) != 75:
            await ctx.reply("The length of the tile string must be 75.\nYou can get a random tile string via the `%board generate` command.")
            return
        
        if not u_converters.is_digit(tile_string):
            await ctx.reply("The tile string must be 75 numbers.\nYou can get a random tile string via the `%board generate` command.")
            return
        
        split_tile_string = u_text.split_chunks(tile_string, 3)
        objective_list = u_bingo.tile_list_5x5(database=database)

        for objective_id in split_tile_string:
            if int(objective_id) >= len(objective_list):
                await ctx.reply(f"One of the objectives in the tile list ({objective_id}) is greater than the max accepted value ({len(objective_list) - 1}.)")
                return
        
        if enabled_number is None:
            enabled_number = 0

        enabled_number = min(max(enabled_number, 0), 33554431)

        u_images.render_board_5x5(
            database = database,
            tile_string = tile_string,
            enabled = enabled_number
        )
        
        embed = u_interface.gen_embed(
            title = "Rendered board",
            description = f"Using a tile string of \"{tile_string}\" and an enabled number of {u_text.smart_number(enabled_number)}:",
            image_link = "attachment://bingo_board.png"
        )
        await ctx.reply(embed=embed, file=discord.File(f'images{SLASH}generated{SLASH}bingo_board.png'))

    
    
    
    
    
    
    ######################################################################################################################################################
    ##### WEEKLY (weekly) ################################################################################################################################
    ######################################################################################################################################################
        
    @commands.group(
        name = "weekly",
        brief = "Shows the current weekly bingo board.",
        description = "Shows the current weekly bingo board.",
        pass_context = True,
        invoke_without_command = True
    )
    async def weekly(self, ctx):
        if ctx.invoked_subcommand is not None:
            return
        
        live_data = u_bingo.live(database=database)

        u_images.render_board_9x9(
            database = database,
            tile_string = live_data["weekly_tile_string"],
            enabled = live_data["weekly_enabled"]
        )

        await ctx.reply(
            content = "This is weekly board #{}!".format(live_data["weekly_board_id"]),
            file = discord.File(r'images/generated/bingo_board.png')
        )

    
    
    
    
    
    
    ######################################################################################################################################################
    ##### WEEKLY STATS (weekly) ##########################################################################################################################
    ######################################################################################################################################################
    
    @weekly.command(
        name = "stats",
        brief = "Get information about the current board.",
        description = "Get information about the current board."
    )
    async def weekly_stats(self, ctx,
            page: typing.Optional[int] = commands.parameter(description = "An integer for what page to use.", displayed_default = 1)
        ):
        base_tile_list = u_bingo.tile_list_9x9(database=database)

        live_data = u_bingo.live(database=database)

        live_list = u_text.split_chunks(live_data["weekly_tile_string"], 3)

        tile_list = [base_tile_list[int(objective_id)] for objective_id in live_list]

        embed = self._generate_list(
            tile_list = tile_list,
            base_tile_list = base_tile_list,
            title = "9x9 board stats",
            page = page,
            type_text = "weekly",
            command = "%weekly stats",
            identifier = "on the 9x9 board"
        )

        await ctx.reply(embed=embed)

    
    
    
    
    
    
    ######################################################################################################################################################
    ##### WEEKLY TICK (weekly) ###########################################################################################################################
    ######################################################################################################################################################
    
    @weekly.group(
        name = "tick",
        brief = "Tick off a tile on the weekly board.",
        description = "Tick off a tile on the weekly board."
    )
    @commands.check(u_checks.bingo_tick_check)
    async def weekly_tick(self, ctx,
            coord_x: typing.Optional[int] = commands.parameter(description = "The X coordinate of the tile to tick."),
            coord_y: typing.Optional[int] = commands.parameter(description = "The Y coordinate of the tile to tick.")
        ):
        if ctx.invoked_subcommand is not None:
            return
        
        # Ensure at least 1 number is provided, if just an x coordinate is provided, it is used as a tile id.
        if coord_x is None:
            await ctx.reply("You must provide a coordinate, as a single tile id or an X and Y coordinate.\nYou can use `%weekly tick guide` to get a guide.")
            return
        
        # Figure out the location of the affected tile via an x and y coordinate or just a single tile id.
        tile_id = self._determine_coordinate(9, coord_x, coord_y)

        # If self._determine_coordinate returned a string there was a problem, and so just send that string.
        if isinstance(tile_id, str):
            await ctx.reply(tile_id)
            return
        
        # If the tile is already ticked.
        if u_bingo.get_tile_state_9x9(database=database, tile_id=tile_id):
            await ctx.reply("That tile is already ticked.")
            return
        
        # Tick the tile, and then convert the result into three variables.
        pre_tick_bingos, post_tick_bingos, objective_id, new_live = u_bingo.tick_9x9(database=database, bot=self.bot, tile_id=tile_id)

        # Count the bingos.
        pre_tick_bingos = u_bingo.count_bingos(pre_tick_bingos, 9)
        post_tick_bingos = u_bingo.count_bingos(post_tick_bingos, 9)

        # Determine how many bingos were made.
        bingos_made = post_tick_bingos - pre_tick_bingos
        
        # Get the name and description of the tile that was ticked.
        objective_data = u_bingo.get_objective_9x9(database=database, objective_id=objective_id)

        # Make the bonus text sent if a bingo is made.
        if bingos_made >= 1:
            bingo_bonus = "And that made {}! {}".format(u_text.smart_text(bingos_made, "bingo"), ":tada:" * bingos_made)
        else:
            bingo_bonus = ""

        await ctx.reply("It's been ticked off!\n\nThe objective was id {}, which has the name `{}` and description:\n{}\n\n{}".format(objective_id, objective_data["name"], objective_data["description"], bingo_bonus))


    
    
    
    
    
    
    ######################################################################################################################################################
    ##### WEEKLY UNTICK (weekly) #########################################################################################################################
    ######################################################################################################################################################
    
    @weekly.command(
        name = "untick",
        brief = "Untick a tile on the weekly board.",
        description = "Untick a tile on the weekly board."
    )
    @commands.check(u_checks.bingo_tick_check)
    async def weekly_untick(self, ctx,
            coord_x: typing.Optional[int] = commands.parameter(description = "The X coordinate of the tile to untick."),
            coord_y: typing.Optional[int] = commands.parameter(description = "The Y coordinate of the tile to untick.")
        ):
        # Ensure at least 1 number is provided, if just an x coordinate is provided, it is used as a tile id.
        if coord_x is None:
            await ctx.reply("You must provide a coordinate, as a single tile id or an X and Y coordinate.\nYou can use `%weekly tick guide` to get a guide.")
            return
        
        # Figure out the location of the affected tile via an x and y coordinate or just a single tile id.
        tile_id = self._determine_coordinate(9, coord_x, coord_y)

        # If self._determine_coordinate returned a string there was a problem, and so just send that string.
        if isinstance(tile_id, str):
            await ctx.reply(tile_id)
            return
        
        # If the tile isn't ticked in the first place.
        if not u_bingo.get_tile_state_9x9(database=database, tile_id=tile_id):
            await ctx.reply("That tile isn't already ticked.")
            return
        
        # Tick the tile, and then convert the result into two variables.
        pre_tick_bingos, post_tick_bingos, new_live = u_bingo.untick_9x9(database=database, bot=self.bot, tile_id=tile_id)

        # Count the bingos.
        pre_tick_bingos = u_bingo.count_bingos(pre_tick_bingos, 9)
        post_tick_bingos = u_bingo.count_bingos(post_tick_bingos, 9)

        # Determine how many bingos were removed.
        bingos_unmade = pre_tick_bingos - post_tick_bingos

        # Make the bonus text sent if a bingo is reversed by this.
        if bingos_unmade >= 1:
            bingo_bonus = "And that undid {}! {}".format(u_text.smart_text(bingos_unmade, "bingo"), ":tada:" * bingos_unmade)
        else:
            bingo_bonus = ""

        await ctx.reply("It's been unticked!\n\n{}".format(bingo_bonus))


    
    
    
    
    
    
    ######################################################################################################################################################
    ##### WEEKLY TICK GUIDE (weekly) #####################################################################################################################
    ######################################################################################################################################################
    
    @weekly_tick.command(
        name = "guide",
        brief = "Get a handy tile id guide for ticking.",
        description = "Get a handy tile id guide for ticking."
    )
    @commands.check(u_checks.bingo_tick_check)
    async def weekly_tick_guide(self, ctx):        
        u_images.render_board(
            database = database,
            tile_string = "".join([f"{i:03}" for i in range(81)]),
            enabled = 0,
            board_size = 9,
            tile_list = [{"name": f"{i + 1} ({(i % 9) + 1}, {(i // 9) + 1})"} for i in range(81)],
            force = True
        )

        await ctx.reply(content="Here you go!", file=discord.File(r'images/generated/bingo_board.png'))


    
    
    
    
    
    
    ######################################################################################################################################################
    ##### WEEKLY GENERATE (weekly) #######################################################################################################################
    ######################################################################################################################################################
        
    @weekly.command(
        name = "generate",
        brief = "Generates a 9x9 bingo board.",
        description = "Generates the tile string for a 9x9 bingo board."
    )
    async def weekly_generate(self, ctx):
        await ctx.reply("`{}`".format(u_bingo.generate_9x9_board(database=database)))


    
    
    
    
    
    
    ######################################################################################################################################################
    ##### WEEKLY RENDER (weekly) #########################################################################################################################
    ######################################################################################################################################################
    
    @weekly.command(
        name = "render",
        brief = "Renders a custom 9x9 board.",
        description = "Renders a custom 9x9 board.\nYou can get a random tile string using the '%weekly generate' command."
    )
    async def board_render(self, ctx,
            tile_string: typing.Optional[str] = commands.parameter(description = "A 243 character string that says what's on each tile."),
            enabled_number: typing.Optional[u_converters.parse_int] = commands.parameter(description = "Number between 0 and 2^81 - 1 that defines completed tiles.")
        ):
        if tile_string is None:
            await ctx.reply("You must provide a tile string.\nYou can get a random tile string via the `%weekly generate` command.")
            return
        
        tile_string = tile_string.replace(",", "")
        
        if len(tile_string) != 243:
            await ctx.reply("The length of the tile string must be 243.\nYou can get a random tile string via the `%weekly generate` command.")
            return
        
        if not u_converters.is_digit(tile_string):
            await ctx.reply("The tile string must be 243 numbers.\nYou can get a random tile string via the `%weekly generate` command.")
            return
        
        split_tile_string = u_text.split_chunks(tile_string, 3)
        objective_list = u_bingo.tile_list_9x9(database=database)

        for objective_id in split_tile_string:
            if int(objective_id) >= len(objective_list):
                await ctx.reply(f"One of the objectives in the tile list ({objective_id}) is greater than the max accepted value ({len(objective_list) - 1}.)")
                return
        
        if enabled_number is None:
            enabled_number = 0

        enabled_number = min(max(enabled_number, 0), 2417851639229258349412351)

        u_images.render_board_9x9(
            database = database,
            tile_string = tile_string,
            enabled = enabled_number
        )
        
        embed = u_interface.gen_embed(
            title = "Rendered board",
            description = f"Using a tile string of \"{tile_string}\" and an enabled number of {u_text.smart_number(enabled_number)}:",
            image_link = "attachment://bingo_board.png"
        )
        await ctx.reply(embed=embed, file=discord.File(f'images{SLASH}generated{SLASH}bingo_board.png'))



async def setup(bot: commands.Bot):
    global database
    database = bot.database

    cog = Bingo_cog()
    cog.bot = bot
    
    # Add attributes for sys.modules and globals() so the _reload_module() function in utility.custom can read it and get the module objects.
    cog.modules = sys.modules
    cog.globals = globals()
    
    await bot.add_cog(cog)