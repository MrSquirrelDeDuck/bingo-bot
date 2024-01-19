"""Custom versions of discord.py objects.

Note that in order to reload this code utility.custom needs to be reloaded, and then every cog that uses it."""

import typing
import discord
from discord.ext import commands

import importlib

import utility.text as u_text
import utility.interface as u_interface

everyone_prevention = discord.AllowedMentions(everyone=False)

class CustomCog(commands.Cog):
    """Custom discord.ext.commands cog that is used by the cog files to allow for universal code."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
    
    def _reload_module(self, module_name: str) -> bool:
        """Reloads a module by name.
        For imports that are in a folder, the folder name must be included. For instance: `utility.files` would reload the utility.files code.
        Returns a bool for whether anything was reloaded, so the number of reloads can be counted."""

        # Get a list of the names of every module in globals(). This can be done with a list comprehension but this is easier to read.
        globals_modules = []

        for module in self.globals.values():
            if hasattr(module, "__name__"):
                globals_modules.append(module.__name__)
        
        # Get a list of every imported module via cross-checking globals_modules and sys.modules.
        all_modules = set(self.modules) & set(globals_modules)

        # If the provided module name 
        if module_name not in all_modules:
            return False
        
        # Get the module object.
        module = self.modules[module_name]

        # Reload the module via importlib.reload.
        importlib.reload(module)
        print("- {} has reloaded {}.".format(self.qualified_name, module_name))

        # Return True, since it has been reloaded in theory.
        return True
    
    async def _on_stonk_tick(self: typing.Self, message: discord.Message) -> None:
        """Code that runs for every stonk tick."""
        pass
    
    async def _hourly_task(self: typing.Self) -> None:
        """Code that runs for every hour."""
        pass
    
    async def _daily_task(self: typing.Self) -> None:
        """Code that runs for every day."""
        pass

class CustomContext(commands.Context):    
    async def safe_reply(ctx, content: str = "", **kwargs) -> discord.Message:        
        kwargs["allowed_mentions"] = everyone_prevention

        return await super().reply(content, **kwargs)
    
    async def send(ctx, content: str = "", **kwargs) -> discord.Message:
        kwargs["allowed_mentions"] = everyone_prevention

        return await super().send(content, **kwargs)
    
    async def reply(self, content: str = "", **kwargs) -> discord.Message:
        try:
            return await self.safe_reply(content, **kwargs)
        except discord.HTTPException:
            # If something went wrong replying.
            if kwargs.get("mention_author", True):
                return await self.send(f"{self.author.mention},\n\n{content}", **kwargs)
            else:
                return await self.send(f"{u_text.ping_filter(u_interface.get_display_name(self.author))},\n\n{content}", **kwargs)

class CustomBot(commands.Bot):
    async def get_context(self, message: discord.Message, *, cls=CustomContext):
        return await super().get_context(message, cls=cls)


