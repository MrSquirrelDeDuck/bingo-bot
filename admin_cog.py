"""This cog is for all the administration commands."""

from discord.ext import commands
import discord
import typing
import traceback
import copy
import os
import asyncio
import random
import re

import sys

import utility.text as u_text
import utility.custom as u_custom
import utility.checks as u_checks
import utility.interface as u_interface
import utility.algorithms as u_algorithms
import utility.images as u_images
import utility.converters as u_converters
import utility.files as u_files

database = None # type: u_files.DatabaseInterface

class Admin_cog(u_custom.CustomCog, name="Admin", description="Administration commands for the Bingo-Bot."):
    bot = None

    all_extensions = [
        "triggers_cog",
        "other_cog",
        "bingo_cog",
        "bread_cog",
        "stonk_cog",
        "secret_cog"
    ]






    ######################################################################################################################################################
    ##### GLOBAL UTILITY FUNCTIONS #######################################################################################################################
    ######################################################################################################################################################

    def reload_database(self):
        """Reloads the database."""
        self.bot.database.save_database(make_backup=True)
        self.bot.database = u_files.DatabaseInterface()
    
    def cog_unload(self):
        """This runs when the cog is unloaded."""
        database.save_database(make_backup=True)






    ######################################################################################################################################################
    ##### CHECKS #########################################################################################################################################
    ######################################################################################################################################################

    async def cog_check(self, ctx):
        if ctx.author.id == self.bot.owner_id:
            return True
        
        if ctx.guild is None:
            return False
        
        if ctx.author.guild_permissions.administrator:
            return True

        # Don't send the message if the check was invoked via the help command.
        if ctx.invoked_with != "help":
            await ctx.reply("I am sorry, but you do not have the permissions to use this command.")
        
        return False
    
    # Added via bot.add_check in add_checks.
    async def test(self, ctx):
        print(ctx.message.content, ctx.author)
        return True

    def add_checks(self):
        """Adds a list of global checks that are in Admin_cog."""
        self.bot.add_check(self.test, call_once = True)






    ######################################################################################################################################################
    ##### COG UTILITY FUNCTIONS ##########################################################################################################################
    ######################################################################################################################################################

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

        if extension_name == "all":
            return await self._reload_all()

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
    
    async def _reload_all(self) -> int:
        """Reloads all the cogs the bot has loaded and all the modules in the utility folder."""

        reloaded_count = 0

        for module_name in copy.deepcopy([i.replace(".py", "") for i in os.listdir("utility/") if i.endswith(".py")]):
            reloaded_count += await self._smart_reload("utility.{}".format(module_name))
            
        for cog_name in copy.deepcopy(list(dict(self.bot.cogs).keys())):
            reloaded_count += await self._smart_reload(f"{cog_name.lower()}_cog")
        
        return reloaded_count
    
    async def _await_confirmation(self, ctx: typing.Union[commands.Context, u_custom.CustomContext],
            message = "Are you sure you would like to proceed? y/n.",
            confirm: list[str] = ["y", "yes"], 
            cancel: list[str] = ["n", "no"],
            lower_response: bool = True
        ) -> bool:
        """Prompts a confirmation.

        Args:
            ctx (typing.Union[commands.Context, u_custom.CustomContext]): The context object.
            message (str, optional): The message to prompt with. Defaults to "Are you sure you would like to proceed? y/n.".
            confirm (list[str], optional): A list of strings that will be accepted. Defaults to ["y", "yes"].
            cancel (list[str], optional): A list of strings that will cancel. Defaults to ["n", "no"].
            lower_response (bool, optional): Whether to make the response lower case before checking it against the `confirm` and `cancel` lists. Defaults to True.

        Returns:
            bool: Whether the prompt was accepted.
        """

        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id 
        
        await ctx.reply(message)
        try:
            msg = await self.bot.wait_for('message', check = check, timeout = 60.0)
        except asyncio.TimeoutError: 
            # No message was sent by the person running the command in a minute, so just cancel it.
            await ctx.reply(f"Timed out.")
            return False
        
        response = msg.content

        if lower_response:
            response = response.lower()

        if response in confirm:
            await ctx.reply("Proceeding.")
            return True
        elif response in cancel:
            await ctx.reply("Cancelled.")
            return False
        else:
            await ctx.reply("Unknown response, cancelled.")
            return False

    
    
    
    
    
    
    
    
    
    ######################################################################################################################################################
    ##### ADMIN ##########################################################################################################################################
    ######################################################################################################################################################

    @commands.group(
        name="admin",
        description="Administration commands for the Bingo-Bot.",
        brief="Administration commands for the Bingo-Bot.",
        pass_context=True,
        invoke_without_command=True
    )
    @commands.is_owner()
    async def admin(self, ctx):
        await ctx.reply("You're missing a subcommand.")

        
            

        
    ######################################################################################################################################################
    ##### ADMIN DATABASE #################################################################################################################################
    ######################################################################################################################################################
    
    @admin.group(
        name="database",
        brief = "Commands for dealing with the database.",
        description = "Commands for dealing with the database.",
        pass_context = True,
        invoke_without_command = True
    )
    @commands.is_owner()
    async def admin_database(self, ctx):
        if ctx.invoked_subcommand is not None:
            return
        
        await ctx.send_help(self.admin_database)

        
            

        
    ######################################################################################################################################################
    ##### ADMIN DATABASE RELOAD ##########################################################################################################################
    ######################################################################################################################################################
    
    @admin_database.command(
        name="reload",
        aliases = ["rebuild"],
        brief = "Reloads the database.",
        description = "Reloads the database."
    )
    @commands.is_owner()
    async def admin_database_reload(self, ctx):
        self.reload_database()

        await ctx.reply("Done.")

        
            

        
    ######################################################################################################################################################
    ##### ADMIN DATABASE SAVE ############################################################################################################################
    ######################################################################################################################################################
    
    @admin_database.command(
        name="save",
        brief = "Saves the database.",
        description = "Saves the database."
    )
    @commands.is_owner()
    async def admin_database_save(self, ctx):
        database.save_database(make_backup=True)

        await ctx.reply("Done.")

        
            

        
    ######################################################################################################################################################
    ##### ADMIN DATABASE LOAD ############################################################################################################################
    ######################################################################################################################################################
    
    @admin_database.command(
        name="load",
        brief = "Loads the database.",
        description = "Loads the database."
    )
    @commands.is_owner()
    async def admin_database_load(self, ctx):
        database.load_database()

        await ctx.reply("Done.")

        
            

        
    ######################################################################################################################################################
    ##### ADMIN DATABASE DUMP #####################################################################################################################################
    ######################################################################################################################################################
    
    @admin_database.command(
        name="dump",
        brief = "Prints a part of the database.",
        description = "Prints a part of the database."
    )
    @commands.is_owner()
    async def admin_database_dump(self, ctx,
            *key: typing.Optional[str]
        ):
        if len(key) == 0:
            print("Dumping the entire database:")
            print(self.bot.database.database)
        else:
            print("Dumping key \"{}\":".format(key))
            print(self.bot.database.load(*key))
            
        await ctx.reply("Done.")

        
            

        
    ######################################################################################################################################################
    ##### ADMIN SHUTDOWN #################################################################################################################################
    ######################################################################################################################################################
    
    @admin.command(
        name = "shutdown",
        aliases = ["shutdown_bot"],
        brief = "Shuts the bot down.",
        description = "Shuts the bot down.\nPlease only use if it is the last option."
    )
    async def admin_shutdown(self, ctx):
        if not u_checks.shutdown_check(database, ctx):
            return
        
        letters = list("abcdefghijklmnopqrstuvwxyABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        security_code = "".join(random.choice(letters) for i in range(16))

        security = await self._await_confirmation(ctx, message = f"If you're sure you want to do this, send the following string:\n`{security_code}`", confirm = [security_code], cancel = [], lower_response = False)

        if security:
            # o7
            await ctx.send("Shutting down.\n<@658290426435862619>")

            await self.bot.close()
            return

        
            

        
    ######################################################################################################################################################
    ##### ADMIN LOAD #####################################################################################################################################
    ######################################################################################################################################################
    
    @admin.command(
        name="load",
        brief = "Load a cog.",
        description = "Load a cog."
    )
    @commands.is_owner()
    async def admin_load(self, ctx,
            extension_name: typing.Optional[str] = commands.parameter(description = "The name of the extension to load.")
        ):
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

        
            

        
    ######################################################################################################################################################
    ##### ADMIN UNLOAD ###################################################################################################################################
    ######################################################################################################################################################
            
    @admin.command(
        name="unload",
        brief = "Unload a cog.",
        description = "Unload a cog."
    )
    @commands.is_owner()
    async def admin_unload(self, ctx,
            extension_name: typing.Optional[str] = commands.parameter(description = "The name of the extension to unload.")
        ):
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

        
            

        
    ######################################################################################################################################################
    ##### ADMIN RELOAD ###################################################################################################################################
    ######################################################################################################################################################
    
    @admin.command(
        name="reload",
        brief = "Reload a cog/module.",
        description = "Reload a cog/module, note that to load a module like utility.bingo, you need to say 'utility.bingo'."
    )
    @commands.is_owner()
    async def admin_reload(self, ctx,
            extension_name: typing.Optional[str] = commands.parameter(description = "The name of the extension to reload.")
        ):
        if extension_name is None:
            await ctx.reply("You must provide a cog or utility name.")
            return
        
        try:
            await ctx.reply("Reloading {}".format(extension_name))

            reload_count = await self._smart_reload(extension_name)

            await ctx.send("Done. {} reloaded.".format(u_text.smart_text(reload_count, "item")))
        except:
            traceback.print_exc()
            await ctx.send("Failed.")

        
            

        
    ######################################################################################################################################################
    ##### ADMIN RESIMULATE ALGORITHMS ####################################################################################################################
    ######################################################################################################################################################
    
    @admin.command(
        name="resimulate_algorithms",
        brief = "Resimulates the stonk algorithms.",
        description = "Resimulates the stonk algorithms."
    )
    @commands.is_owner()
    async def admin_resimulate_algorithms(self, ctx):
        await ctx.reply("Resimulating stonk algorithms, this will take some time.")

        u_algorithms.resimulate_all(database)

        await ctx.reply("Done.")

        
            

        
    ######################################################################################################################################################
    ##### ADMIN GENERATE REPORT ##########################################################################################################################
    ######################################################################################################################################################
    
    @admin.command(
        name="generate_report",
        brief = "Re-generates the stonk report.",
        description = "Re-generates the stonk report."
    )
    @commands.is_owner()
    async def admin_generate_report(self, ctx):
        u_images.stonk_report(database)
        
        await ctx.reply(file=discord.File(f"images/generated/stonk_report.png"))

        
            

        
    ######################################################################################################################################################
    ##### ADMIN MODIFY PERMISSIONS #######################################################################################################################
    ######################################################################################################################################################
    
    @admin.command(
        name="modify_permissions",
        brief = "Modifies permissions.",
        description = "Modifies permissions."
    )
    @commands.is_owner()
    async def admin_modify_permissions(self, ctx,
            mode: typing.Optional[str] = commands.parameter(description = "The mode to use, 'allow' or 'disallow'."),
            permission: typing.Optional[str] = commands.parameter(description = "The permission name to allow or disallow."),
            user: typing.Optional[discord.Member] = commands.parameter(description = "The user to allow or disallow the permission.")
        ):
        if None in [mode, permission, user]:
            await ctx.reply("You must provide the mode to use, the permission name, and some user identifier.")
            return
        
        permission_data = database.load("permissions")
        
        if mode == "allow":
            if user.id in permission_data.get(permission, []):
                await ctx.reply("That user already has access to that permission.")
                return
            
            if permission not in permission_data:
                permission_data[permission] = []
            
            permission_data[permission].append(user.id)
        elif mode == "disallow":
            if user.id not in permission_data.get(permission, []):
                await ctx.reply("That user didn't have access to that permission in the first place.")
                return
            
            permission_data[permission].remove(user.id)
        
        database.save("permissions", data=permission_data)
        
        await ctx.reply("Done.")

        
            

        
    ######################################################################################################################################################
    ##### ADMIN MODIFY PINGLIST #######################################################################################################################
    ######################################################################################################################################################
    
    @admin.command(
        name="modify_pinglist",
        brief = "Modifies pinglists.",
        description = "Modifies pinglists."
    )
    @commands.is_owner()
    async def admin_modify_pinglist(self, ctx,
            mode: typing.Optional[str] = commands.parameter(description = "The mode to use, 'add' or 'remove'."),
            pinglist: typing.Optional[str] = commands.parameter(description = "The pinglist to use."),
            user: typing.Optional[discord.Member] = commands.parameter(description = "The user to add to or remove from the pinglist.")
        ):
        if None in [mode, pinglist, user]:
            await ctx.reply("You must provide the mode to use, the ping list name, and some user identifier.")
            return
        
        database.update_ping_list(pinglist, user.id, mode == "add")
        
        await ctx.reply("Done.")

        
            

        
    ######################################################################################################################################################
    ##### ADMIN SET COUNTER ##############################################################################################################################
    ######################################################################################################################################################
    
    @admin.command(
        name="set_counter",
        brief = "Sets a counter to a specific value.",
        description = "Sets a counter to a specific value."
    )
    @commands.is_owner()
    async def admin_set_counter(self, ctx,
            counter_name: typing.Optional[str] = commands.parameter(description = "The counter name to set."),
            new_value: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The new value for the counter.")
        ):
        if None in [counter_name, new_value]:
            await ctx.reply("You must provide a counter name and a new value for it.")
            return
        
        database.set_daily_counter(counter_name, new_value)
        
        await ctx.reply("Done.")

        
            

        
    ######################################################################################################################################################
    ##### ADMIN SET COUNT ################################################################################################################################
    ######################################################################################################################################################
    
    @admin.command(
        name="set_count",
        brief = "Sets a channel's counting progress.",
        description = "Sets a channel's counting progress."
    )
    @commands.is_owner()
    async def admin_set_count(self, ctx,
            channel_id: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The channel id of the channel."),
            new_value: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The new value for counting.")
        ):
        if None in [channel_id, new_value]:
            await ctx.reply("You must provide a counter name and a new value for it.")
            return
        
        old_data = database.get_counting_data(channel_id)
        
        database.set_counting_data(
            channel_id = channel_id, 
            count = new_value,
            sender = 0
        )
        
        await ctx.reply("Done, old count was {}.".format(u_text.smart_number(old_data.get("count", 0))))

        
            

        
    ######################################################################################################################################################
    ##### ADMIN REMOTE SAY ###############################################################################################################################
    ######################################################################################################################################################
    
    @admin.command(
        name="remote_say",
        brief = "Hehe",
        description = "Hehe"
    )
    async def admin_remote_say(self, ctx,
            message_link: typing.Optional[u_converters.parse_message_link] = commands.parameter(description = "Link to a message to reply to or send a message in."),
            to_reply: typing.Optional[u_converters.extended_bool] = commands.parameter(description = "Whether to reply to the message, or just send in the channel."),
            *, message_content: typing.Optional[str] = commands.parameter(description = "The content of the message to send.")
        ):
        if not u_checks.get_permission(database, ctx.author.id, "remote_say"):
            return
        
        if None in [message_link, to_reply, message_content]:
            await ctx.reply("You must provide a message link, whether to reply to the message ('yes' or 'no') and the message content.")
            return
        
        if not(await self.bot.is_owner(ctx.author)) and re.search("(<@&?\d+>)|(@(here|everyone))", message_content):
            await ctx.reply("Sorry, but I won't ping anyone in the text when remotely saying stuff.")
            return
        
        channel = await self.bot.fetch_channel(message_link["channel"])
        
        if not to_reply:
            sent = await channel.send(message_content)

            await ctx.reply(f"Done.\n[Message link.](<{sent.jump_url}>)")
            return

        message = channel.get_partial_message(message_link["message"])
        sent = await message.reply(message_content)

        await ctx.reply(f"Done.\n[Message link.](<{sent.jump_url}>)")

        
            

        
    ######################################################################################################################################################
    ##### ADMIN CHANGE STATUS ############################################################################################################################
    ######################################################################################################################################################
        
    @admin.command(
        name="change_status",
        brief = "Changes the bot's status.",
        description = "Changes the bot's status.",
        invoke_without_command=True,
        pass_context=True
    )
    async def admin_change_status(self, ctx,
            status_type: typing.Optional[str] = commands.parameter(description = "The type of status to change to."),
            *, text: typing.Optional[str] = commands.parameter(description = "The content of the status.")
        ):
        if status_type not in ["playing", "watching", "streaming", "listening", "custom", "competing"]:
            await ctx.reply("The activity type must be one of \"playing\", \"watching\", \"streaming\", \"listening\", \"custom\" or \"competing\".")
            return
        
        if text is None:
            await ctx.reply("You must provide the text of the status.")
            return
        
        url = None

        if status_type == "streaming":
            url, text = text.split(" ", 1)

            matched = re.match(r"https:\/\/w{0,3}\.?(youtu|twitch).?(be|tv)(.com)?\/(watch\?v=)?([\w-]+)", url)
            if not matched:
                await ctx.reply("I don't recognize that url.\nPlease provide a YouTube or Twitch url.")
                return
            
            if "youtu.be" in url:
                url = f"https://www.youtube.com/watch?v={matched.group(5)}"
                
        await u_interface.change_status(
            database = database,
            bot = self.bot,
            status_type = status_type,
            status_text = text,
            status_url = url
        )

        await ctx.reply("Done.\nStatus set to `{}`".format(u_text.ping_filter(text)))
            
        


        
async def setup(bot: commands.Bot):
    cog = Admin_cog()
    cog.bot = bot

    global database
    database = bot.database
    
    # Add attributes for sys.modules and globals() so the _reload_module() function in utility.custom can read it and get the module objects.
    cog.modules = sys.modules
    cog.globals = globals()

    await bot.add_cog(cog)