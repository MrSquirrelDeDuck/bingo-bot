from discord.ext import commands
import discord
import typing

import sys
import importlib

import utility.bingo as bingo

class Bingo_cog(commands.Cog, name="Bingo"):
    bot = None

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

