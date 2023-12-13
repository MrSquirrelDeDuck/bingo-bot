from discord.ext import commands
import discord
import typing

import sys
import importlib

import utility.bingo as bingo
import utility.images as images
import utility.checks as checks
import utility.text as text
import utility.custom as custom

class Bingo_cog(custom.CustomCog, name="Bingo"):
    bot = None
    
    #############################
    ##### UTILITY FUNCTIONS #####
    #############################

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
    
    #######################
    ##### DAILY BOARD #####
    #######################

    @commands.command(
        name = "gen_board_5x5",
        aliases = ["gen_board"],
        brief = "Generates a bingo board.",
        description = "Generates the tile string for a 5x5 bingo board.",
        hidden = True
    )
    async def gen_board_5x5(self, ctx):
        await ctx.reply("`{}`".format(bingo.generate_5x5_board()))
    
    @commands.group(
        name = "board",
        brief = "Shows the current 5x5 bingo board.",
        description = "Shows the current 5x5 bingo board.",
        pass_context = True,
        invoke_without_command = True
    )
    async def board(self, ctx):
        live_data = bingo.live()

        images.render_board_5x5(
            tile_string = live_data["daily_tile_string"],
            enabled = live_data["daily_enabled"]
        )

        await ctx.reply(content="This is bingo board #{}!".format(live_data["daily_board_id"]), file=discord.File(r'images/generated/bingo_board.png'))
    
    @commands.group(
        name = "tick",
        brief = "Tick off a tile on the bingo board.",
        description = "Tick off a tile on the bingo board.",
        hidden = True
    )
    @commands.check(checks.bingo_tick_check)
    async def tick(self, ctx, coord_x: typing.Optional[int], coord_y: typing.Optional[int]):
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
        if bingo.get_tile_state_5x5(tile_id):
            await ctx.reply("That tile is already ticked.")
            return
        
        # Tick the tile, and then convert the result into three variables.
        ticked_data = bingo.tick_5x5(tile_id)
        pre_tick_bingos, post_tick_bingos, objective_id = ticked_data

        # Determine how many bingos were made.
        bingos_made = post_tick_bingos - pre_tick_bingos
        
        # Get the name and description of the tile that was ticked.
        objective_data = bingo.get_objective_5x5(objective_id)

        # Make the bonus text sent if a bingo is made.
        if bingos_made >= 1:
            bingo_bonus = "And that made {}! {}".format(text.smart_text(bingos_made, "bingo"), ":tada:" * bingos_made)
        else:
            bingo_bonus = ""

        await ctx.reply("It's been ticked off!\n\nThe objective was id {}, which has the name `{}` and description:\n{}\n\n{}".format(objective_id, objective_data["name"], objective_data["description"], bingo_bonus))

    @commands.command(
        name = "untick",
        brief = "Untick a tile on the bingo board.",
        description = "Untick a tile on the bingo board.",
        hidden = True
    )
    @commands.check(checks.bingo_tick_check)
    async def untick(self, ctx, coord_x: typing.Optional[int], coord_y: typing.Optional[int]):
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
        if not bingo.get_tile_state_5x5(tile_id):
            await ctx.reply("That tile isn't already ticked.")
            return
        
        # Tick the tile, and then convert the result into two variables.
        ticked_data = bingo.untick_5x5(tile_id)
        pre_tick_bingos, post_tick_bingos = ticked_data

        # Determine how many bingos were removed.
        bingos_unmade = pre_tick_bingos - post_tick_bingos

        # Make the bonus text sent if a bingo is reversed by this.
        if bingos_unmade >= 1:
            bingo_bonus = "And that undid {}! {}".format(text.smart_text(bingos_unmade, "bingo"), ":tada:" * bingos_unmade)
        else:
            bingo_bonus = ""

        await ctx.reply("It's been unticked!\n\n{}".format(bingo_bonus))

    
    ########################
    ##### WEEKLY BOARD #####
    ########################

    @commands.command(
        name = "gen_board_9x9",
        brief = "Generates a 9x9 bingo board.",
        description = "Generates the tile string for a 9x9 bingo board.",
        hidden = True
    )
    async def gen_board_9x9(self, ctx):
        await ctx.reply("`{}`".format(bingo.generate_9x9_board()))
    
    @commands.group(
        name = "weekly",
        brief = "Shows the current weekly bingo board.",
        description = "Shows the current weekly bingo board.",
        pass_context = True,
        invoke_without_command = True
    )
    async def weekly(self, ctx):
        live_data = bingo.live()

        images.render_board_9x9(
            tile_string = live_data["weekly_tile_string"],
            enabled = live_data["weekly_enabled"]
        )

        await ctx.reply(
            content = "This is weekly board #{}!".format(live_data["weekly_board_id"]),
            file = discord.File(r'images/generated/bingo_board.png')
        )


async def setup(bot: commands.Bot):
    cog = Bingo_cog()
    cog.bot = bot
    
    # Add attributes for sys.modules and globals() so the _reload_module() function in utility.custom can read it and get the module objects.
    cog.modules = sys.modules
    cog.globals = globals()
    
    await bot.add_cog(cog)