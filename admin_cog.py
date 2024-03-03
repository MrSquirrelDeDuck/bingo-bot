"""This cog is for all the administration commands."""

from discord.ext import commands
import discord
import typing
import traceback
import copy
import os
from os.path import sep as SLASH
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

MAIN_GUILD = 958392331671830579

class Admin_cog(
        u_custom.CustomCog,
        name="Admin",
        description="Administration commands for the Bingo-Bot."
    ):

    bot = None

    all_extensions = [
        "triggers_cog",
        "other_cog",
        "bingo_cog",
        "bread_cog",
        "stonk_cog",
        "secret_cog",
        "games_cog"
    ]






    ######################################################################################################################################################
    ##### GLOBAL UTILITY FUNCTIONS #######################################################################################################################
    ######################################################################################################################################################

    def reload_database(self: typing.Self):
        """Reloads the database."""
        self.bot.database.save_database(make_backup=True)
        self.bot.database = u_files.DatabaseInterface()
    
    def cog_unload(self: typing.Self):
        """This runs when the cog is unloaded."""
        database.save_database(make_backup=True)






    ######################################################################################################################################################
    ##### CHECKS #########################################################################################################################################
    ######################################################################################################################################################

    async def cog_check(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        if ctx.author.id == self.bot.owner_id:
            return True
        
        if u_checks.get_permission(ctx.author.id, "shutdown") or u_checks.get_permission(ctx.author.id, "remote_say"):
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
    async def dm_check(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ) -> bool:
        """Disables commands in DMs, with a few exceptions."""
        
        if ctx.guild is not None:
            return True
        
        if ctx.author.id == self.bot.owner_id:
            return True
        
        if ctx.invoked_with != "admin" and not ctx.message.content.startswith(f"{self.bot.command_prefix}help admin"):
            return False
        
        if u_checks.get_permission(ctx.author.id, "shutdown") or u_checks.get_permission(ctx.author.id, "remote_say"):
            return True

        return False
    
    # Added via bot.add_check in add_checks.
    async def disabled_check(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ) -> bool:
        """Bot check that returns False and sends a message if the command is disabled."""

        invoked_command = ctx.command.qualified_name

        invoked_command = invoked_command.replace(" ", "-")

        toggled = database.load("command_toggle", default={})

        if not toggled.get(invoked_command, True):
            await ctx.reply("I am sorry, but this command has been disabled.")
            return False
        
        parents = ctx.command.parents

        if len(parents) != 0:
            for parent in parents:
                if not toggled.get(parent.qualified_name.replace(" ", "-"), True):
                    await ctx.reply("I am sorry, but this command has been disabled.")
                    return False
        
        return True


    def add_checks(self: typing.Self):
        """Adds a list of global checks that are in Admin_cog."""
        self.bot.add_check(self.dm_check)
        self.bot.add_check(self.disabled_check)






    ######################################################################################################################################################
    ##### COG UTILITY FUNCTIONS ##########################################################################################################################
    ######################################################################################################################################################

    async def _load_all_extensions(self: typing.Self) -> None:
        """Uses self.all_extensions to load all listed cogs."""
        print("Loading all extensions.\nExtension list: {}".format(self.all_extensions))

        for extension in self.all_extensions:
            await self._load_extension(extension)

        print("Loaded all extensions.")

    async def _load_extension(
            self: typing.Self,
            extension_name: str
        ) -> None:
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
    
    async def _unload_extension(
            self: typing.Self,
            extension_name: str
        ) -> None:
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

    async def _reload_extension(
            self: typing.Self,
            extension_name: str
        ) -> None:
        print("Attempting to reload extension \"{}\"".format(extension_name))
        
        # Try to reload it.
        await self.bot.reload_extension(extension_name)

        print("Reloaded \"{}\" extension.".format(extension_name))
    
    async def _reload_module_universal(
            self: typing.Self,
            module_name: str
        ) -> int:
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

    
    async def _smart_reload(
            self: typing.Self,
            extension_name: str
        ) -> int:
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
    
    async def _reload_all(self: typing.Self) -> int:
        """Reloads all the cogs the bot has loaded and all the modules in the utility folder."""

        reloaded_count = 0

        for module_name in copy.deepcopy([i.replace(".py", "") for i in os.listdir("utility/") if i.endswith(".py")]):
            reloaded_count += await self._smart_reload("utility.{}".format(module_name))
            
        for cog_name in copy.deepcopy(list(dict(self.bot.cogs).keys())):
            reloaded_count += await self._smart_reload(f"{cog_name.lower()}_cog")
        
        return reloaded_count

    
    
    
    
    
    
    
    
    
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
    async def admin(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
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
    async def admin_database(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
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
    async def admin_database_reload(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
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
    async def admin_database_save(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
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
    async def admin_database_load(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
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
    async def admin_database_dump(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
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
    @commands.check(u_checks.shutdown_check)
    async def admin_shutdown(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):        
        letters = list("abcdefghijklmnopqrstuvwxyABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        security_code = "".join(random.choice(letters) for i in range(16))

        security = await u_interface.await_confirmation(self.bot, ctx, message = f"If you're sure you want to do this, send the following string:\n`{security_code}`", confirm = [security_code], cancel = [], lower_response = False)

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
    @commands.check(u_checks.sub_admin_check)
    async def admin_load(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
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
    @commands.check(u_checks.sub_admin_check)
    async def admin_unload(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
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
    @commands.check(u_checks.sub_admin_check)
    async def admin_reload(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
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
    ##### ADMIN UPDATE BOT ###############################################################################################################################
    ######################################################################################################################################################
    
    @admin.command(
        name="update_bot",
        brief = "Pulls from Git and updates the bot.",
        description = "Pulls from Git and updates the bot."
    )
    @commands.check(u_checks.sub_admin_check)
    async def admin_update_bot(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        await ctx.reply("Pulling from Git.")

        os.system("git pull")

        await ctx.send("Done, reloading everything.")

        await self._reload_all()

        # Reload everything twice, to ensure things like utility.values is reloaded fully.
        await self._reload_all()

        await ctx.reply("Done.")

        
            

        
    ######################################################################################################################################################
    ##### ADMIN REFRESH PUBLIC ###########################################################################################################################
    ######################################################################################################################################################
    
    @admin.command(
        name="refresh_public",
        brief = "Refreshes the public folder in the Git repository.",
        description = "Refreshes the public folder in the Git repository."
    )
    @commands.check(u_checks.sub_admin_check)
    async def admin_refresh_public(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        cogs = self.bot.cogs

        done = False

        for name, obj in cogs.items():
            if name != "Secret":
                continue
            
            try:
                done = obj.update_public_git()
            except AttributeError:
                traceback.print_exc()
        
        if done:
            await ctx.reply("Done.")
        else:
            await ctx.reply("Failed, check the log.")

        
            

        
    ######################################################################################################################################################
    ##### ADMIN RESIMULATE ALGORITHMS ####################################################################################################################
    ######################################################################################################################################################
    
    @admin.command(
        name="resimulate_algorithms",
        brief = "Resimulates the stonk algorithms.",
        description = "Resimulates the stonk algorithms."
    )
    @commands.is_owner()
    async def admin_resimulate_algorithms(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
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
    async def admin_generate_report(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
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
    async def admin_modify_permissions(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            mode: typing.Optional[str] = commands.parameter(description = "The mode to use, 'allow' or 'disallow'."),
            permission: typing.Optional[str] = commands.parameter(description = "The permission name to allow or disallow."),
            user: typing.Optional[discord.Member] = commands.parameter(description = "The user to allow or disallow the permission.")
        ):
        if None in [mode, permission, user]:
            await ctx.reply("You must provide the mode to use, the permission name, and some user identifier.")
            return
        
        if mode not in ["allow", "disallow"]:
            await ctx.reply("The mode must be 'allow' or 'disallow'.")
            return
        
        permission_data = u_files.load("data", "misc", "permissions.json", default = {}, join_file_path=True)
        
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
        
        u_files.save("data", "misc", "permissions.json", data=permission_data, join_file_path=True)
        
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
    async def admin_modify_pinglist(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
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
    async def admin_set_counter(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
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
    async def admin_set_count(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            channel_id: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The channel id of the channel."),
            new_value: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The new value for counting.")
        ):
        if None in [channel_id, new_value]:
            await ctx.reply("You must provide a channel id and a new value for it.")
            return
        
        old_data = database.get_counting_data(channel_id)
        
        database.set_counting_data(
            channel_id = channel_id, 
            count = new_value,
            sender = 0
        )
        
        await ctx.reply("Done, old count was {}.".format(u_text.smart_number(old_data.get("count", 0))))

        
            

        
    ######################################################################################################################################################
    ##### ADMIN SET CHAIN ################################################################################################################################
    ######################################################################################################################################################
    
    @admin.command(
        name="set_chain",
        brief = "Sets a channel's chain state.",
        description = "Sets a channel's chain stats."
    )
    @commands.is_owner()
    async def admin_set_chain(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            channel_id: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The channel id of the channel."),
            amount: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of messages in a row that have been sent."),
            *, message: typing.Optional[str] = commands.parameter(description = "The message that has been chained.")
        ):
        if None in [channel_id, amount, message]:
            await ctx.reply("You must provide a channel id, the amount of times the message was chained, and the message that has been chained.")
            return
        
        database.save(
            "chains_data", str(channel_id),
            data= {
                "message": message,
                "sender": None,
                "count": amount
            }
        )
        
        await ctx.reply("Done.")

        
            

        
    ######################################################################################################################################################
    ##### ADMIN REMOTE SAY ###############################################################################################################################
    ######################################################################################################################################################
    
    @admin.command(
        name="remote_say",
        brief = "Hehe",
        description = "Hehe"
    )
    @commands.check(u_checks.remote_say_check)
    async def admin_remote_say(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            message_link: typing.Optional[u_converters.parse_message_link] = commands.parameter(description = "Link to a message to reply to or send a message in."),
            to_reply: typing.Optional[u_converters.extended_bool] = commands.parameter(description = "Whether to reply to the message, or just send in the channel."),
            *, message_content: typing.Optional[str] = commands.parameter(description = "The content of the message to send.")
        ):        
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
    ##### ADMIN SNAPSHOT ROLES ###########################################################################################################################
    ######################################################################################################################################################
        
    @admin.command(
        name="snapshot_roles",
        brief = "Creates a new snapshot of the roles.",
        description = "Creates a new snapshot of the roles."
    )
    @commands.is_owner()
    async def admin_snapshot_roles(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        u_interface.snapshot_roles(
            guild = self.bot.get_guild(MAIN_GUILD)
        )
        await ctx.reply("Done.")

        
            

        
    ######################################################################################################################################################
    ##### ADMIN FROM SNAPSHOT ############################################################################################################################
    ######################################################################################################################################################

    @admin.command(
        name="from_snapshot",
        brief = "Restores someone's roles from a snapshot.",
        description = "Restores someone's roles from a snapshot."
    )
    @commands.check(u_checks.in_authority)
    async def admin_from_snapshot(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            member: typing.Optional[discord.Member],
            snapshot_id: typing.Optional[str]
        ):
        if ctx.guild is None:
            await ctx.reply("This can't be run in DMs.")
            return
        if ctx.guild.id != MAIN_GUILD:
            await ctx.reply("This isn't available in this server, sorry.")
            return
        
        if member is None:
            await ctx.reply("You must provide a member to restore the roles from.\nThis can be done via a username, id, mention, or any other identification method.")
            return
        
        snapshot_list = [item.replace(".json", "") for item in os.listdir(f"data{SLASH}role_snapshots{SLASH}snapshots{SLASH}") if item.endswith(".json")]
        snapshot_list_sorted = list(sorted(snapshot_list, reverse=True)) # Goes newest to oldest.

        snapshots_containing = {}

        for snapshot in snapshot_list_sorted:
            loaded_data = u_files.load("data", "role_snapshots", "snapshots", f"{snapshot}.json", default={}, join_file_path=True)

            if str(member.id) not in loaded_data:
                continue
            
            snapshots_containing[snapshot] = loaded_data

            if len(snapshots_containing) >= 10:
                break
        
        async def send_list():
            embed = u_interface.gen_embed(
                title = "Role restoration",
                description = "Available snapshots:\n" + "\n".join(
                    [f"- `{item}` (<t:{item.split('.')[0]}>)" for item in snapshots_containing.keys()]
                ),
            )
            await ctx.reply(embed=embed)
        
        if snapshot_id == "latest":
            snapshot_id = max(snapshots_containing.keys())

        if snapshot_id not in snapshots_containing:
            await send_list()
            return
        
        filter_list = [ # This is a list of roles that the bot either can't add or shouldn't be adding.
            961202779072909312, 958755031820161025, 970510247372394517, 958515508905406464, 963542265870053427, 978381737442820096,
            958774733225230397, 968431452993769502, 1066596562165301248, 958512048306815056, 1119445209923723396, 970549665055522850,
            958392331671830579, 958920124314816532, 959220485672026142, 958920155025539132, 958920265792892938, 958920201557119036,
            959247044701216848, 980602604847501362, 958920326006308914, 959254553562349608
        ]

        if ctx.guild.id not in filter_list:
            filter_list.append(ctx.guild.id)

        roles_added = []
        blacklisted_roles = []
        already_has = []

        member_roles = [role.id for role in member.roles]

        for role_id in snapshots_containing[snapshot_id][str(member.id)]:
            if role_id in filter_list:
                blacklisted_roles.append(role_id)
                continue

            if role_id in member_roles:
                already_has.append(role_id)
                continue
            
            try:
                role = ctx.guild.get_role(role_id)
                if role is not None:
                    roles_added.append(role_id)
                    await member.add_roles(role)
            except discord.Forbidden:
                await ctx.reply("I don't have the permissions to give people roles.")
                return
            except discord.HTTPException:
                pass
        
        embed = u_interface.gen_embed(
            title = "Role restoration",
            description = "Restored from snapshot {} (<t:{}>.)\n\nNumber of added roles: {}\nNumber of roles in blacklist: {}\nNumber of roles the member already had: {}".format(
                snapshot_id,
                snapshot_id.split(".")[0],
                len(roles_added),
                len(blacklisted_roles),
                len(already_has)
            ),
            fields = [
                ("Added roles:", ", ".join(
                    [f"<@&{item}>" for item in roles_added]
                ), False),
                ("Blacklisted roles:", "These are roles that are in the blacklist, but the member had them in the snapshot.\n\n" + ", ".join(
                    [f"<@&{item}>" for item in blacklisted_roles]
                ), False),
                ("Already had:", "These are roles that the member had in the snapshot and already had when the command was run.\n\n" + ", ".join(
                    [f"<@&{item}>" for item in already_has]
                ), False)
            ]
        )
        await ctx.reply(embed=embed)
            

        
        
        
            

        
    ######################################################################################################################################################
    ##### ADMIN REFRESH STATUS ###########################################################################################################################
    ######################################################################################################################################################
        
    @admin.command(
        name="refresh_status",
        brief = "Refreshes the status from the database.",
        description = "Refreshes the status from the database."
    )
    @commands.is_owner()
    async def admin_refresh_status(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        await u_interface.refresh_status(
            bot = self.bot,
            database = database
        )
        await ctx.reply("Done.")

        
            

        
    ######################################################################################################################################################
    ##### ADMIN CHANGE STATUS ############################################################################################################################
    ######################################################################################################################################################
        
    @admin.command(
        name="change_status",
        brief = "Changes the bot's status.",
        description = "Changes the bot's status."
    )
    @commands.is_owner()
    async def admin_change_status(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
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

        
            

        
    ######################################################################################################################################################
    ##### ADMIN CHANGE NICKNAME ##########################################################################################################################
    ######################################################################################################################################################
        
    @admin.command(
        name="change_nickname",
        brief = "Changes the bot's nickname.",
        description = "Changes the bot's nickname in the specified server."
    )
    @commands.is_owner()
    async def admin_change_nickname(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            guild_id: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The id of the server to change the nickname in."),
            *, text: typing.Optional[str] = commands.parameter(description = "The new nickname.")
        ):
        if guild_id is None:
            await ctx.reply("You must provide the guild id.")
            return
        
        try:
            guild = await self.bot.fetch_guild(guild_id)
            bot_member = await guild.fetch_member(self.bot.user.id)
            
            await bot_member.edit(nick=text)

            await ctx.reply("Done.")
            return
        except discord.Forbidden:
            await ctx.reply("I don't have the permissions to do that.")

        
            

        
    ######################################################################################################################################################
    ##### ADMIN TOGGLE COMMAND ###########################################################################################################################
    ######################################################################################################################################################
        
    @admin.command(
        name="toggle_command",
        brief = "Universally enables and disables commands.",
        description = "Universally enables and disables commands.\n\nUse the 'fetch' parameter to fetch the current state of the command."
    )
    @commands.check(u_checks.sub_admin_check)
    async def admin_toggle_command(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            new_state: typing.Optional[str] = commands.parameter(description = "The new toggled state for the command or 'fetch'."),
            *, command_name: typing.Optional[str] = commands.parameter(description = "The name of the command to toggle.")
        ):
        if new_state != "fetch":
            try:
                new_state = u_converters.extended_bool(new_state)
            except commands.BadArgument:
                new_state = None

        if new_state is None:
            await ctx.reply("You must provide the new state in a boolean and the command name.")
            return
        """
        {
            "command_name": {
                "object": command_object,
                "aliases": ["alias_1", "alias_2"],
                "subcommands": {
                    "subcommand_name": {
                        "object": subcommand_object,
                        "aliases": []
                        "subcommands": {
                            ...
                        }
                    },
                    "subcommand_name_2": {
                        "object": subcommand_object_2,
                        "aliases": []
                        "subcommands": {}
                    }
                }
            }
        }"""

        def extract(input_command: commands.Command | commands.Group) -> dict:
            """Recursivly fetch all the subcommands of a command."""
            out = {
                "object": input_command,
                "aliases": input_command.aliases,
                "subcommands": {}
            }
            try:
                for cmd in input_command.commands:
                    out["subcommands"][cmd.name] = extract(cmd)
            except AttributeError:
                pass
            
            return out
        
        command_dict = {c.name: extract(c) for c in self.bot.commands}

        if command_name is None:
            await ctx.reply("Commands:\n- {}".format("\n- ".join(command_dict.keys())))
            return
    
        command_split = command_name.split(" ")

        if command_split[0] not in command_dict:
            await ctx.reply("Commands:\n- {}".format("\n- ".join(command_dict.keys())))
            return

        try:
            subcommand = command_dict[command_split[0]]
            for cmd in command_split[1:]:
                subcommand = subcommand["subcommands"][cmd]
        except KeyError:
            await ctx.reply("Subcommands of {}:\n- {}".format(subcommand["object"].name, "\n- ".join(subcommand["subcommands"].keys())))
            return
        
        current = database.load("command_toggle", default={})

        internal_name = command_name.replace(" ", "-")

        if new_state == "fetch":
            await ctx.reply("Current status of {}:\n{}.".format(command_name, "Enabled" if current.get(internal_name, True) else "Disabled"))
            return

        if internal_name in ["admin-toggle_command", "admin"]:
            await ctx.reply("Unfortunately, this command cannot be toggled.")
            return
        current[internal_name] = new_state

        database.save("command_toggle", data=current)

        await ctx.reply("Done, command '{}' is now {}.".format(command_name, "enabled" if new_state else "disabled"))



            
        


        
async def setup(bot: commands.Bot):
    global database
    database = bot.database

    cog = Admin_cog()
    cog.bot = bot
    
    # Add attributes for sys.modules and globals() so the _reload_module() function in utility.custom can read it and get the module objects.
    cog.modules = sys.modules
    cog.globals = globals()

    await bot.add_cog(cog)