from discord.ext import commands
import typing
import traceback

class Admin_cog(commands.Cog, name="Admin"):
    bot = None

    all_extensions = [
        "loop_cog",
        "other_cog"
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
        await ctx.reply("Something went wrong processing that command.")

    #####################
    #####  CHECKS  ######
    #####################

    async def cog_check(self, ctx):
        if ctx.author.id == self.bot.owner_id:
            return True
        
        if ctx.guild is None:
            return False
        
        return ctx.author.guild_permissions.administrator
    
    # Added via bot.add_check in add_checks.
    async def test(self, ctx):
        print(ctx.message.content, ctx.author)
        return True

    #################################
    ##### COG UTILITY FUNCTIONS #####
    #################################

    def add_checks(self):
        # Adds a list of global checks here.
        self.bot.add_check(self.test)

    async def _load_all_extensions(self) -> None:
        print("Loading all extensions.\nExtension list: {}".format(self.all_extensions))

        for extension in self.all_extensions:
            await self._load_extension(extension)

        print("Loaded all extensions.")

    async def _load_extension(self, extension_name: str) -> None:
        print("Attempting to load extension \"{}\"".format(extension_name))
        
        try:
            # Try to load it.
            await self.bot.load_extension(extension_name)
        except:
            # If it isn't already loaded, but there's some other problem.
            raise

        # It was loaded!
        print("\"{}\" loaded successfully.".format(extension_name))
    
    async def _reload_extension(self, extension_name: str) -> None:
        print("Attempting to reload extension \"{}\"".format(extension_name))
        
        # Try to reload it.
        await self.bot.reload_extension(extension_name)

        print("Reloaded \"{}\" extension.".format(extension_name))

    async def _unload_extension(self, extension_name: str) -> None:
        print("Attempting to unload extension \"{}\"".format(extension_name))
        
        try:
            # Try to unload it.
            await self.bot.unload_extension(extension_name)
        except:
            # If it is loaded, but there's some other problem.
            raise

        # It was unaded!
        print("\"{}\" unloaded successfully.".format(extension_name))
    
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
        if ctx.invoked_subcommand is None:
            await ctx.reply("You're missing a subcommand.")
    

    @admin.command(
        name="load",
        pass_context=True,
        invoke_without_command=True,
        hidden=True
    )
    @commands.is_owner()
    async def load_cog(self, ctx, extension_name: typing.Optional[str]):
        if extension_name is None:
            await ctx.reply("You must provide a cog name.")
            return
        
        try:
            await ctx.reply("Loading {}.".format(extension_name))

            await self._load_extension(extension_name)

            await ctx.send("Done.")
        except:
            traceback.print_exc()
            await ctx.send("Failed.")

    @admin.command(
        name="unload",
        pass_context=True,
        invoke_without_command=True,
        hidden=True
    )
    @commands.is_owner()
    async def unload_cog(self, ctx, extension_name: typing.Optional[str]):
        if extension_name is None:
            await ctx.reply("You must provide a cog name.")
            return
        
        try:
            await ctx.reply("Unloading {}.".format(extension_name))

            await self._unload_extension(extension_name)

            await ctx.send("Done.")
        except:
            traceback.print_exc()
            await ctx.send("Failed.")
    

    @admin.command(
        name="reload",
        pass_context=True,
        invoke_without_command=True,
        hidden=True
    )
    @commands.is_owner()
    async def reload_cog(self, ctx, extension_name: typing.Optional[str]):
        if extension_name is None:
            await ctx.reply("You must provide a cog name.")
            return

        try:
            await ctx.reply("Reloading {}".format(extension_name))

            await self._reload_extension(extension_name)

            await ctx.send("Done.")
        except:
            traceback.print_exc()
            await ctx.send("Failed.")

    

        
async def setup(bot: commands.Bot):
    cog = Admin_cog()
    cog.bot = bot
    await bot.add_cog(cog)