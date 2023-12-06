from discord.ext import commands
import discord
import typing

import sys
import importlib

import utility.bingo as bingo

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

async def setup(bot: commands.Bot):
    cog = Bingo_cog()
    cog.bot = bot
    
    await bot.add_cog(cog)