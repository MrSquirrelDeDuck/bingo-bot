from discord.ext import commands
import discord
import typing

import sys
import importlib

class Other_cog(commands.Cog, name="Other"):
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
    
    await bot.add_cog(cog)