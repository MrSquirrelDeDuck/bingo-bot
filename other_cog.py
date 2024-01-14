from discord.ext import commands
import discord
import typing

import sys
import importlib

import utility.custom as u_custom

class Other_cog(u_custom.CustomCog, name="Other", description="Commands that don't fit elsewhere, and are kind of silly."):
    bot = None
    
    ###########################
    ###########################
    ###########################

    @commands.command(
        name = "avatar",
        brief = "Get someone's avatar.",
        description = "Get someone's avatar.\nThis will use their global avatar, however the `display` parameter can be used to fetch server-specific avatars."
    )
    async def avatar(self, ctx,
            target: typing.Optional[discord.Member] = commands.parameter(description = "The member to use, if nothing is provided it'll use you."),
            display: typing.Optional[str] = commands.parameter(description = "If 'display' is provided it will use server avatars.")
        ):
        ctx = u_custom.CustomContext(ctx)

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