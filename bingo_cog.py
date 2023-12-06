from discord.ext import commands
import discord
import typing

import sys
import importlib

import utility.bingo as bingo
import utility.images as images

class Bingo_cog(commands.Cog, name="Bingo"):
    bot = None

    ###########################
    ##### ADMIN FUNCTIONS #####
    ###########################
    
    def _reload_module(self, module_name: str) -> bool:
        """Reloads a module by name.
        For imports that are in a folder, the folder name must be included. For instance: `utility.files` would reload the utility.files code.
        Returns a bool for whether anything was reloaded, so the number of reloads can be counted."""

        # Get a list of the names of every module in globals(). This can be done with a list comprehension but this is easier to read.
        globals_modules = []

        for module in globals().values():
            if hasattr(module, "__name__"):
                globals_modules.append(module.__name__)
        
        # Get a list of every imported module via cross-checking globals_modules and sys.modules.
        all_modules = set(sys.modules) & set(globals_modules)

        # If the provided module name 
        if module_name not in all_modules:
            return False
        
        # Get the module object.
        module = sys.modules[module_name]

        # Reload the module via importlib.reload.
        importlib.reload(module)
        print("- {} has reloaded {}.".format(self.qualified_name, module_name))

        # Return True, since it has been reloaded in theory.
        return True
    
    ###########################
    ###########################
    ###########################

    @commands.command(
        name = "gen_board_5x5",
        aliases = ["gen_board"],
        brief = "Generates a bingo board.",
        description = "Generates the tile string for a 5x5 bingo board.",
        hidden = True
    )
    async def gen_board_5x5(self, ctx):
        await ctx.reply("`{}`".format(bingo.generate_5x5_board()))

    @commands.command(
        name = "gen_board_9x9",
        brief = "Generates a 9x9 bingo board.",
        description = "Generates the tile string for a 9x9 bingo board.",
        hidden = True
    )
    async def gen_board_9x9(self, ctx):
        await ctx.reply("`{}`".format(bingo.generate_9x9_board()))
    
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
    
    await bot.add_cog(cog)