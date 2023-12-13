from discord.ext import commands
import discord
import typing

import sys
import importlib

import utility.custom as custom

class Other_cog(custom.CustomCog, name="Other"):
    bot = None
    
    ###########################
    ###########################
    ###########################

    @commands.command(
        name = "avatar",
        brief = "Get someone's avatar.",
        description = "Get someone's avatar.\nThis will use their global avatar, however the `display` parameter can be used to fetch server-specific avatars."
    )
    async def avatar(self, ctx, target: typing.Optional[discord.Member], display: typing.Optional[str]):
        # if ctx.invoked_subcommand is not None:
        #     return # If invoked_subcommand isn't none, then the display subcommand was used.

        # If a target was specified or not.
        if target is None:
            target = ctx.author
        
        # If it should use the display avatar, rather than the global one.
        display = display == "display"
        
        # Get the avatar url.
        if display:
            avatar_url = target.display_avatar
        else:
            avatar_url = target.avatar
        
        # Send the url.
        await ctx.reply(avatar_url)



async def setup(bot: commands.Bot):
    cog = Other_cog()
    cog.bot = bot
    
    # Add attributes for sys.modules and globals() so the _reload_module() function in utility.custom can read it and get the module objects.
    cog.modules = sys.modules
    cog.globals = globals()
    
    await bot.add_cog(cog)