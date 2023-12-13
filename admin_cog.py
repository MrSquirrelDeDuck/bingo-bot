from discord.ext import commands
import discord
import typing
import traceback

import sys
import importlib

import utility.text as text
import utility.interface as interface
import utility.custom as custom

class Admin_cog(custom.CustomCog, name="Admin"):
    bot = None

    all_extensions = [
        "loop_cog",
        "other_cog",
        "bingo_cog"
    ]

    ######################
    ##### LISTENERS ######
    ######################

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # Command check errors.
        if isinstance(error, commands.errors.CheckFailure):
            # A command check failed.
            return
        
        if isinstance(error, commands.errors.CommandNotFound):
            # Someone tried to run a command that does not exist.
            return
        
        # Print the error, so it's easier to see.
        traceback.print_exception(error)

        # Let whoever ran the command know that something went awry.
        await interface.smart_reply(ctx, "Something went wrong processing that command.")

    #####################
    #####  CHECKS  ######
    #####################

    async def cog_check(self, ctx):
        if ctx.author.id == self.bot.owner_id:
            return True
        
        if ctx.guild is None:
            return False
        
        if ctx.author.guild_permissions.administrator:
            return True
        
        await interface.smart_reply(ctx, "I am sorry, but you do not have the permissions to use this command.")
        return False
    
    # Added via bot.add_check in add_checks.
    async def test(self, ctx):
        print(ctx.message.content, ctx.author)
        return True

    def add_checks(self):
        """Adds a list of global checks that are in Admin_cog."""
        self.bot.add_check(self.test, call_once = True)

    #################################
    ##### COG UTILITY FUNCTIONS #####
    #################################

    async def _load_all_extensions(self) -> None:
        """Uses self.all_extensions to load all listed cogs."""
        print("Loading all extensions.\nExtension list: {}".format(self.all_extensions))

        for extension in self.all_extensions:
            await self._load_extension(extension)

        print("Loaded all extensions.")

    async def _load_extension(self, extension_name: str) -> None:
        """Loads a cog if it is not already loaded."""
        print("Attempting to load extension \"{}\"".format(extension_name))
        
        try:
            # Try to load it.
            await self.bot.load_extension(extension_name)
        except:
            # If it isn't already loaded, but there's some other problem.
            raise

        # It was loaded!
        print("\"{}\" loaded successfully.".format(extension_name))
    
    async def _unload_extension(self, extension_name: str) -> None:
        """Unloads a cog, note that this can unload the admin cog."""
        print("Attempting to unload extension \"{}\"".format(extension_name))
        
        try:
            # Try to unload it.
            await self.bot.unload_extension(extension_name)
        except:
            # If it is loaded, but there's some other problem.
            raise

        # It was unloaded!
        print("\"{}\" unloaded successfully.".format(extension_name))

    async def _reload_extension(self, extension_name: str) -> None:
        print("Attempting to reload extension \"{}\"".format(extension_name))
        
        # Try to reload it.
        await self.bot.reload_extension(extension_name)

        print("Reloaded \"{}\" extension.".format(extension_name))
    
    async def _reload_module_universal(self, module_name: str) -> int:
        """Attempts to have all cogs reload a module by name.
        Returns the number of cogs that reloaded the module."""

        # Gets a list of all the cogs.
        all_cogs = self.bot.cogs

        # Just to track how many are reloaded, we set a variable to 0 and increase it whenever something is reloaded.
        reloaded_count = 0

        # Now, loop through all the cogs and run the _reload_module() function for them.
        for cog in all_cogs.values():
            result = cog._reload_module(module_name)
            if result:
                reloaded_count += 1
        
        return reloaded_count

    
    async def _smart_reload(self, extension_name: str) -> int:
        """Attempts to reload a cog via the extension name, and if there is no cog with that name tries to reload it as a module.
        Returns an int of the number of things reloaded."""

        try:
            # First, attempt to reload it via self._reload_extension, assuming it's a cog.
            await self._reload_extension(extension_name)

            return 1
        except commands.errors.ExtensionNotLoaded:
            # Okay, it's not a cog, now let's try to reload it assuming it's a module.
            reloaded = await self._reload_module_universal(extension_name)

            return reloaded
        except:
            raise

        return 0
    
    #####################
    ##### COMMANDS ######
    #####################

    @commands.group(
        name="admin",
        description="Administration commands for the Bingo-Bot.",
        brief="Administration commands for the Bingo-Bot.",
        pass_context=True,
        invoke_without_command=True,
        hidden=True
    )
    @commands.is_owner()
    async def admin(self, ctx):
        ctx = custom.CustomContext(ctx)
        
        await interface.smart_reply(ctx, "You're missing a subcommand.")
    

    @admin.command(
        name="load",
        pass_context=True,
        invoke_without_command=True,
        hidden=True
    )
    @commands.is_owner()
    async def load_cog(self, ctx, extension_name: typing.Optional[str]):
        ctx = custom.CustomContext(ctx)
        
        if extension_name is None:
            await interface.smart_reply(ctx, "You must provide a cog name.")
            return
        
        try:
            await interface.smart_reply(ctx, "Loading {}.".format(extension_name))

            await self._load_extension(extension_name)

            await interface.safe_send(ctx, "Done.")
        except:
            traceback.print_exc()
            await interface.safe_send(ctx, "Failed.")

    @admin.command(
        name="unload",
        pass_context=True,
        invoke_without_command=True,
        hidden=True
    )
    @commands.is_owner()
    async def unload_cog(self, ctx, extension_name: typing.Optional[str]):
        ctx = custom.CustomContext(ctx)
        
        if extension_name is None:
            await interface.smart_reply(ctx, "You must provide a cog name.")
            return
        
        try:
            await interface.smart_reply(ctx, "Unloading {}.".format(extension_name))

            await self._unload_extension(extension_name)

            await interface.safe_send(ctx, "Done.")
        except:
            traceback.print_exc()
            await interface.safe_send(ctx, "Failed.")
    

    @admin.command(
        name="reload",
        pass_context=True,
        invoke_without_command=True,
        hidden=True
    )
    @commands.is_owner()
    async def reload_cog(self, ctx, extension_name: typing.Optional[str]):
        ctx = custom.CustomContext(ctx)
        
        if extension_name is None:
            await interface.smart_reply(ctx, "You must provide a cog or utility name.")
            return
        
        try:
            await interface.smart_reply(ctx, "Reloading {}".format(extension_name))

            reload_count = await self._smart_reload(extension_name)

            await interface.safe_send(ctx, "Done. {} reloaded.".format(text.smart_text(reload_count, "item")))
        except:
            traceback.print_exc()
            await interface.safe_send(ctx, "Failed.")

    

        
async def setup(bot: commands.Bot):
    cog = Admin_cog()
    cog.bot = bot
    
    # Add attributes for sys.modules and globals() so the _reload_module() function in utility.custom can read it and get the module objects.
    cog.modules = sys.modules
    cog.globals = globals()

    await bot.add_cog(cog)