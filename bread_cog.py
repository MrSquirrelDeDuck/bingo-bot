"""This cog is for utility commands for The Bread Game."""

from discord.ext import commands
import discord
import typing
import datetime
import pytz
import copy
import math
import aiohttp
import traceback
from scipy.stats import binom

import sys

import utility.files as u_files
import utility.converters as u_converters
import utility.text as u_text
import utility.interface as u_interface
import utility.checks as u_checks
import utility.bread as u_bread
import utility.stonks as u_stonks
import utility.values as u_values
import utility.custom as u_custom
import utility.solvers as u_solvers

database = None # type: u_files.DatabaseInterface

class Bread_cog(u_custom.CustomCog, name="Bread", description="Utility commands for The Bread Game!"):
    bread_wiki_searching = False

    # This is a list of unix timestamps, such that if you use <t:time_keys[0]> it'll be the right time.
    time_keys = ["1648850700", "1648854300", "1648857900", "1648861500", "1648865100", "1648868700", "1648785900", "1648789500", "1648793100", "1648796700", "1648800300", "1648803900", "1648807500", "1648811100", "1648814700", "1648818300", "1648821900", "1648825500", "1648829100", "1648832700", "1648836300", "1648839900", "1648843500", "1648847100"]

    ######################################################################################################################################################
    ##### UTILITY FUNCTIONS ##############################################################################################################################
    ######################################################################################################################################################

    def _get_reminder_data(self: typing.Self) -> dict:
        """Returns the reminder data as loaded from data/reminders.json."""
        return database.load("reminders")
    
    def _save_reminder_data(self: typing.Self, data: dict) -> None:
        """Saves a dict to the reminder data file."""
        database.save("reminders", data=data)
    
    async def _send_reminder_list(self: typing.Self, ctx: typing.Union[commands.Context, u_custom.CustomContext], target: discord.Member, footer: str, reminder_data: dict = None) -> discord.Message:
        """Sends the list of reminders the author has, using ctx."""
        if reminder_data is None:
            reminder_data = self._get_reminder_data()

        reminder_list = []

        for reminder in reminder_data["reminder_list"]:
            if reminder["user"] == target.id:
                reminder_list.append("At {} (<t:{}:t>): {}".format(reminder["hour"], self.time_keys[reminder["hour"]], reminder["text"]))
        
        if len(reminder_list) == 0:
            reminder_list = "You don't have any reminders set!\nTo add reminders, use `%bread reminder add`."
        else:
            reminder_list = "- {}\n{}".format("\n- ".join(reminder_list), footer)
        
        embed = u_interface.embed(
            title = "Bread Reminders",
            description = reminder_list
        )
        
        return await ctx.reply(embed=embed)

    ######################################################################################################################################################
    ##### CHECKS #########################################################################################################################################
    ######################################################################################################################################################

    async def reminder_disallowed(ctx):
        reminder_data = Bread_cog._get_reminder_data(Bread_cog)

        if ctx.author.id in reminder_data["disallowed"]:
            await ctx.reply("I am sorry, but you have been disallowed from using reminders.\nIf you believe this was an error, please let the moderators know.")
            return False
        
        return True

    ######################################################################################################################################################
    ##### COMMANDS #######################################################################################################################################
    ######################################################################################################################################################

    @commands.group(
        name = "bread",
        description = "You might want `$bread` instead of this.\n\nHeader command for Bread Game related utility commands.",
        brief = "Header for Bread Game related commands.",
        invoke_without_command = True,
        pass_context = True
    )
    async def bread(self, ctx):
        if ctx.invoked_subcommand is not None:
            return
        
        await ctx.send_help(self.bread)

    
    
    
    
    
      
    @bread.command(
        name = "help",
        description = "Sends the help text for the bread command.",
        brief = "Sends the help text for the bread command.",
        hidden = True
    )
    async def bread_help(self, ctx):
        await ctx.send_help(self.bread)

    
    
    
    
    
    
    @bread.command(
        name = "stonks",
        aliases = ["stonk"],
        description = "To use the Bingo-Bot's stonk commands, use '%stonks'.",
        brief = "To use the Bingo-Bot's stonk commands, use '%stonks'.",
        hidden = True
    )
    async def bread_stonks(self, ctx):
        await ctx.reply("To use the Bingo-Bot's stonk-related commands, use `%stonks` instead of `%bread stonks`.")

    
    
    
    
    
    
    ######################################################################################################################################################
    ##### BREAD TIME #####################################################################################################################################
    ######################################################################################################################################################
    
    @bread.command(
        name = "time",
        description = "Get the current time in Bread Standard Time.",
        brief = "Get the current time in Bread Standard Time."
    )
    async def bread_time(self, ctx):
        def is_dst(dt=None, timezone="UTC"):
            if dt is None:
                dt = datetime.datetime.utcnow()
            timezone = pytz.timezone(timezone)
            timezone_aware_date = timezone.localize(dt, is_dst=None)
            return timezone_aware_date.tzinfo._dst.seconds != 0

        apply_dst = is_dst(datetime.datetime.now(), timezone="US/Pacific")

        timestamp = ctx.message.created_at.replace(microsecond=0, tzinfo=None)

        if apply_dst:
            timestamp = timestamp + datetime.timedelta(hour=1)
        
        breadoclock = datetime.datetime(timestamp.year, timestamp.month, timestamp.day, 23, 5, 0).replace(tzinfo=None)
        
        if not (timestamp.hour >= 23 and timestamp.minute >= 5):
            breadoclock = breadoclock - datetime.timedelta(days=1)
        
        next_breadoclock = breadoclock + datetime.timedelta(days=1)

        boc_timedelta = timestamp - breadoclock

        hours = int(boc_timedelta.total_seconds() // 3600)
        minutes = str(int((boc_timedelta.total_seconds() % 3600) // 60))
        seconds = str(int((boc_timedelta.total_seconds() % 3600) % 60))

        hour_12 = str(hours % 12)
        time_suffix = ["AM", "PM"][hours >= 12]

        if hour_12 == "0":
            hour_12 = "12"
        
        if len(minutes) == 1:
            minutes = f"0{minutes}"
        if len(seconds) == 1:
            seconds = f"0{seconds}"
        
        days = (timestamp - datetime.datetime(month=4, day=9, year=2022, hour=18, minute=5)).days - 1

        years, days = divmod(days, 365) 
        
        names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        permonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        
        month = 0
        days_remaining = days
        while days_remaining > permonth[month]:
            days_remaining -= permonth[month]
            month += 1
        
        day_text = str(days_remaining) + ["th", "st", "nd", "rd", "th", "th", "th", "th", "th", "th"][int(str(days_remaining)[-1])]

        embed = u_interface.embed(
            title = f"{hour_12}:{minutes}:{seconds} {time_suffix}",
            description = f"In Bread Standard Time is currently {hour_12}:{minutes}:{seconds} {time_suffix} ({boc_timedelta}) on the {day_text} of {names[month]}, {years} AB.\n\nThe next Bread o' clock is <t:{int((next_breadoclock - datetime.datetime(1970,1,1)).total_seconds())}:R>."
        )

        await ctx.reply(embed = embed)

    
    
    
    
    
    
    @commands.command(
        name = "breadtime",
        description = "Shortcut for '%bread time'",
        brief = "Shortcut for '%bread time'"
    )
    async def breadtime(self, ctx):
        await self.bread_time(ctx)

    
    
    
    
    
    ######################################################################################################################################################
    ##### BREAD REMINDERS ################################################################################################################################
    ######################################################################################################################################################
    
    @bread.group(
        name = "reminder",
        aliases = ["reminders"],
        description = "Setup hourly reminders.",
        brief = "Setup hourly reminders."
    )
    async def bread_reminder(self, ctx):
        if ctx.invoked_subcommand is not None:
            return
        
        reminder_data = self._get_reminder_data()

        await self._send_reminder_list(ctx, ctx.author, "Use `%bread reminder remove` to remove a reminder.\nUse `%bread reminder edit` to edit a reminder.\nUse `%bread time` to get the current time in Bread Standard Time.", reminder_data)

    
    
    
    
    
    
    @bread_reminder.command(
        name = "add",
        brief = "Add a reminder.",
        description = "Add a reminder.\nFirst parameter is the time in Bread Standard Time, then everything after that is the text of the reminder."
    )
    @commands.check(reminder_disallowed)
    async def bread_reminder_add(self, ctx,
            hour: typing.Optional[int] = commands.parameter(description = "The hour of the new reminder."),
            reminder_text: typing.Optional[str] = commands.parameter(description = "The text of the new reminder.")
        ):
        if hour is None:
            await ctx.reply("You must provide an hour in Bread Standard time.")
            return
        
        reminder_text = u_text.after_parameter(ctx, hour)

        if reminder_text in ["", None]:
            await ctx.reply("You need to provide the text for the reminder.")
            return
        
        reminder_data = self._get_reminder_data()

        for reminder in reminder_data["reminder_list"]:
            if reminder["user"] == ctx.author.id and reminder["hour"] == hour:
                await ctx.reply("Sorry, but you already have a reminder at that time.")
                return

        reminder_data["reminder_list"].append({
            "text": reminder_text,
            "user": ctx.author.id,
            "hour": hour
        })

        self._save_reminder_data(reminder_data)

        embed = u_interface.embed(
            title = "Reminder added!",
            description = "Added reminder for {} (<t:{}:t>) with the text:\n{}".format(hour, self.time_keys[hour], reminder_text)
        )

        await ctx.reply(embed = embed)

    
    
    
    
    
    
    @bread_reminder.command(
        name = "remove",
        brief = "Remove an existing reminder.",
        description = "Remove an reminder.\nTakes a parameter that is the time of the reminder you want to remove."
    )
    @commands.check(reminder_disallowed)
    async def bread_reminder_remove(self, ctx,
            hour: typing.Optional[int] = commands.parameter(description = "The hour of the reminder you want to remove.")
        ):
        reminder_data = self._get_reminder_data()
        
        if hour is None or not(0 <= hour <= 23):
            await self._send_reminder_list(ctx, ctx.author, "Add the reminder's time as a parameter to remove that reminder.\nFor example, `%bread reminder remove 5` would remove a reminder you have at 5 o' clock.\nAll times are in Bread Standard Time.", reminder_data)
            return
        
        remove_data = None

        for reminder in reminder_data["reminder_list"]:
            if reminder["user"] == ctx.author.id and reminder["hour"] == hour:
                remove_data = reminder
        
        if remove_data is None:
            await ctx.reply("You don't have a reminder at that time.")
            return
        
        reminder_data["reminder_list"].remove(remove_data)
        self._save_reminder_data(reminder_data)

        embed = u_interface.embed(
            title = "Reminder removed!",
            description = "Removed reminder for {} (<t:{}:t>) that had the text:\n{}".format(remove_data["hour"], self.time_keys[remove_data["hour"]], remove_data["text"])
        )

        await ctx.reply(embed=embed)

    
    
    
    
    
    
    @bread_reminder.command(
        name = "edit",
        brief = "Edit an existing reminder.",
        description = "Edit an existing reminder, you can modify the text or the hour of the reminder."
    )
    @commands.check(reminder_disallowed)
    async def bread_reminder_edit(self, ctx,
            reminder_hour: typing.Optional[int] = commands.parameter(description = "The hour of the existing reminder you want to modify."),
            modification_type: typing.Optional[str] = commands.parameter(description = "The type of data that will be modified: 'hour' or 'text'."),
            new_information: typing.Optional[str] = commands.parameter(description = "The new information that will be used.")
        ):
        target = ctx.author

        if await u_checks.in_authority(ctx):
            target = discord.utils.find(lambda m: m.id == reminder_hour, ctx.guild.members)
            if target is None:
                target = ctx.author
            else:
                reminder_hour = int(copy.copy(modification_type))
                modification_type = copy.copy(new_information)
                new_information = u_text.after_parameter(ctx, modification_type)


        reminder_data = self._get_reminder_data()

        if reminder_hour is None or not(0 <= reminder_hour <= 23):
            await self._send_reminder_list(ctx, target, "Add the reminder's time as a parameter to modify that reminder.\nFor example, `%bread reminder edit 3 hour 6` would edit a reminder you have at 3 o' clock, and move it to 6 o' clock.\nAll times are in Bread Standard Time.", reminder_data)
            return
        
        reminder_old = None
        reminder_modify = None
        reminder_id = -1

        for iterator, reminder in enumerate(reminder_data["reminder_list"]):
            if reminder["user"] == target.id and reminder["hour"] == reminder_hour:
                reminder_modify = reminder
                reminder_old = reminder.copy()
                reminder_id = iterator
                break
        
        if reminder_modify is None:
            await ctx.reply("You don't have a reminder at that time.")
            return
        
        if modification_type not in ["hour", "text"]:
            await ctx.reply("You must provide the type of data to modify.\nCurrently only 'hour' and 'text' are accepted.")
            return
        
        if new_information is None:
            await ctx.reply("You must say what to set the data to.")
            return
        
        if modification_type == "hour":
            if not new_information.isdigit():
                await ctx.reply("The new hour must be a number.")
                return
            
            if int(new_information) == reminder_modify["hour"]:
                await ctx.reply("The reminder is already at that time.")
                return
            
            if not(0 <= int(new_information) <= 23):
                await ctx.reply("The new hour must be a number between 0 and 23.")
                return
            
            new_information = int(new_information)

            reminder_modify["hour"] = new_information
        else:
            if new_information == reminder_modify["text"]:
                await ctx.reply("The reminder text is already that.")
                return
            new_information = u_text.after_parameter(ctx, modification_type)

            reminder_modify["text"] = new_information
        
        reminder_data["reminder_list"][reminder_id] = reminder_modify

        self._save_reminder_data(reminder_data)

        embed = u_interface.embed(
            title = "Reminder modified!",
            description = "Old hour: {}\nOld text:\n{}\n\nNew hour: {}\nNew text:\n{}".format(reminder_old["hour"], reminder_old["text"], reminder_modify["hour"], reminder_modify["text"])
        )

        await ctx.reply(embed=embed)

    
    
    
    
    
    
    @bread_reminder.command(
        name = "allow",
        brief = "Allow someone to use the bread reminders.",
        description = "Allow someone to use the bread reminders.",
    )
    @commands.check(u_checks.in_authority)
    async def bread_reminder_allow(self, ctx, target: typing.Optional[discord.Member] = commands.parameter(description = "Some identifier for the user to allow reminder usage.")):
        if target is None:
            await ctx.reply("You must provide some identifier for the user to allow reminder usage.\nAn id or username will suffice.")
            return
        
        reminder_data = self._get_reminder_data()

        if target.id not in reminder_data["disallowed"]:
            await ctx.reply("That member can already use the reminders.")
            return
        
        reminder_data["disallowed"].remove(target.id)

        self._save_reminder_data(reminder_data)

        await ctx.reply("Success, that user can now use reminders.")

    
    
    
    
    
    
    @bread_reminder.command(
        name = "disallow",
        brief = "Disallow someone to use the bread reminders.",
        description = "Disallow someone to use the bread reminders.",
    )
    @commands.check(u_checks.in_authority)
    async def bread_reminder_disallow(self, ctx, target: typing.Optional[discord.Member] = commands.parameter(description = "Some identifier for the user to disallow reminder usage.")):
        if target is None:
            await ctx.reply("You must provide some identifier for the user to disallow reminder usage.\nAn id or username will suffice.")
            return
        
        reminder_data = self._get_reminder_data()

        if target.id in reminder_data["disallowed"]:
            await ctx.reply("That member already can't use the reminders.")
            return
        
        reminder_data["disallowed"].append(target.id)

        self._save_reminder_data(reminder_data)

        await ctx.reply("Success, that user can no longer use reminders.")

    
    
    
    
    
    ######################################################################################################################################################
    ##### BREAD LOAF CONVERTER ###########################################################################################################################
    ######################################################################################################################################################
        
    @bread.group(
        name = "loaf_converter",
        aliases = ["lc"],
        brief = "Automated math regarding Loaf Converters.",
        description = "Automated math regarding Loaf Converters.\nWithout any subcommands, this command will tell you how much dough it costs to get the next loaf converter.\nYou can reply to bread stats to use the values given there."
    )
    async def bread_loaf_converter(self, ctx,
            current: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of Loaf Converters you currently have."),
            self_converting_yeast: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of Self Converting Yeast you currently have.")
        ):
        if ctx.invoked_subcommand is not None:
            return

        attempted_parse = u_bread.parse_attempt(ctx.message, require_reply=True)
        
        if attempted_parse:
            current, self_converting_yeast = attempted_parse["stats"]["loaf_converter"], attempted_parse["stats"]["loaf_converter_discount"]

        if current is None:
            await ctx.reply("You must provide the amount of Loaf Converters you have.\nSyntax: `%bread loaf_converter <current amount of lcs> <level of scy>`.")
            return
        
        if self_converting_yeast is None:
            self_converting_yeast = 0

        next_cost = (current + 1) * (256 - (self_converting_yeast * 12))

        embed = u_interface.embed(
            title = "Loaf Converters",
            description = f"With {u_text.smart_text(current, 'Loaf Converter')} and Self Converting Yeast level {u_text.smart_number(self_converting_yeast)} the next Loaf Converter will cost **{u_text.smart_number(next_cost)}** dough."
        )

        await ctx.reply(embed=embed)

    
    
    
    
    
    @bread_loaf_converter.command(
        name = "calculate",
        aliases = ["cowculate"],
        brief = "Get the total cost between two Loaf Converter amounts.",
        description = "Get the total cost between two Loaf Converter amounts.",
    )
    async def bread_loaf_converter_calculate(self, ctx,
            current: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of Loaf Converters you currently have."),
            goal: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of Loaf Converters you would like to have."),
            self_converting_yeast: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of Self Converting Yeast you currently have.")
        ):
        attempted_parse = u_bread.parse_attempt(ctx.message, require_reply=True)

        if attempted_parse:
            goal = current
            current, self_converting_yeast = attempted_parse["stats"]["loaf_converter"], attempted_parse["stats"]["loaf_converter_discount"]

        if current is None:
            await ctx.reply("You must provide the amount of Loaf Converters you currently have, or reply to a stats message.\nSyntax: `%bread loaf_converter calculate <current amount of lcs> <goal amount of lcs> <scy level>`, or reply to a stats message and just provide the goal.")
            return
        
        if goal is None:
            await ctx.reply("You must provide the amount of Loaf Converters you want to have.\nSyntax: `%bread loaf_converter calculate <current amount of lcs> <goal amount of lcs> <scy level>`, or reply to a stats message and just provide the goal.")
            return
        
        if self_converting_yeast is None:
            self_converting_yeast = 0
        
        if goal < current:
            await ctx.reply("The goal number of Loaf Converters must be smaller than the current amount.")
            return
        
        equation = lambda c, g, s: int(((g - c) * (256 - (12 * s)) * c) + (((g - c) * ((g - c) + 1) * (256 - (12 * s))) // 2))

        dough_required = equation(current, goal, self_converting_yeast)
        dough_required_no_scy = equation(current, goal, 0)

        embed = u_interface.embed(
            title = "Loaf Converter calculation",
            description = f"It would require **{u_text.smart_number(dough_required)}** dough to purchase the {u_text.smart_text(goal - current, 'Loaf Converter')} needed.\nWith {u_text.smart_text(self_converting_yeast, 'level')} of Self Converting Yeast, you would save **{u_text.smart_number(dough_required_no_scy - dough_required)} dough**."
        )

        await ctx.reply(embed=embed)

    
    
    
    
    
    @bread_loaf_converter.command(
        name = "dough",
        brief = "Says how many Loaf Converters you can get with an amount of dough.",
        description = "Says how many Loaf Converters you can get with an amount of dough.\nIf you reply to a stats message it will use the stats given, and will determine how much dough you have from there. You can still provide a dough amount for it to use instead."
    )
    async def bread_loaf_converter_dough(self, ctx,
            dough: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of dough you have. Read above for more info."),
            current: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of Loaf Converters you currently have."),
            self_converting_yeast: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of Self Converting Yeast you currently have.")
        ):
        attempted_parse = u_bread.parse_attempt(ctx.message, require_reply=True)

        if attempted_parse:
            current, self_converting_yeast = attempted_parse["stats"]["loaf_converter"], attempted_parse["stats"]["loaf_converter_discount"]

            if dough is None:
                dough = attempted_parse["stats"]["total_dough"]

                for stonk in u_values.stonks:
                    if stonk not in attempted_parse["stats"]:
                        continue

                    dough += stonk.value() * attempted_parse["stats"][stonk]
        
        SYNTAX = "Syntax: `%bread loaf_converter dough <amount of dough you have> <the current number of lcs> <scy level>`. You can reply to a stats message to automatically parse the stats, if this is done the amount of dough will be determinized, but an amount of dough can still be provided."
        
        if dough is None:
            await ctx.reply("You must provide the amount of dough you have.\n{}".format(SYNTAX))
            return
        
        if current is None:
            await ctx.reply("You must provide the amount of Loaf Converters you currently have.\n{}".format(SYNTAX))
            return
        
        if self_converting_yeast is None:
            self_converting_yeast = 0

        if self_converting_yeast >= 22:
            await ctx.reply("That level of Self Converting Yeast results in the cost multiplier for Loaf Converters being negative, and thus it would be possible to purchase infinite Loaf Converters.")
            return
            
        equation = lambda d, c, s: int((-1 * (2 * (256 - (12 * s)) * c + (256 - (12 * s))) + math.isqrt((2 * (256 - (12 * s)) * c + (256 - (12 * s))) ** 2 + 8 * (256 - (12 * s)) * d)) // (2 * (256 - (12 * s))))

        purchasable = equation(dough, current, self_converting_yeast)
        purchasable_no_scy = equation(dough, current, 0)

        embed = u_interface.embed(
            title = "Loaf Converter dough calculation",
            description = f"With {u_text.smart_number(dough)} dough, it would be possible to purchase **{u_text.smart_text(purchasable, 'Loaf Converter')}**.\nYou would go from {u_text.smart_text(current, 'Loaf Converter')} to {u_text.smart_number(purchasable + current)}.\nWith {u_text.smart_text(self_converting_yeast, 'level')} of Self Converting Yeast, you are able to purchase **{u_text.smart_text(purchasable - purchasable_no_scy, 'more Loaf Converter')}**."
        )

        await ctx.reply(embed=embed)

    
    
    
    
    
    ######################################################################################################################################################
    ##### BREAD GAMBLE ###################################################################################################################################
    ######################################################################################################################################################
        
    @bread.group(
        name = "gamble",
        brief = "Commands relating to bread gambles.",
        description = "Commands relating to bread gambles.",
        pass_context = True,
        invoked_without_command = True
    )
    async def bread_gamble(self, ctx):
        if ctx.invoked_subcommand is not None:
            return
        
        await ctx.send_help(self.bread_gamble)

    
    
    
    
    @bread_gamble.command(
        name = "initial",
        brief = "Get the initial board of a gamble.",
        description = "Get the initial board of a gamble."
    )
    async def bread_gamble_initial(self, ctx):
        replied_to = u_interface.replying_mm_checks(ctx.message, require_reply = True, return_replied_to = True)

        if not replied_to:
            await ctx.reply("You must reply to a gamble message.")
            return
        
        gamble_messages = database.load("bread", "gamble_messages")

        message_key = f"{replied_to.channel.id}.{replied_to.id}"

        if message_key not in gamble_messages:
            await ctx.reply("I don't have that gamble in my storage.\nI only store the last 500 gambles that occurred.")
            return
        
        embed = u_interface.embed(
            title = "Initial board.",
            description = "The initial board of that gamble:\n\n{}".format(gamble_messages[message_key])
        )

        await ctx.reply(embed=embed)

    

        
    ######################################################################################################################################################
    ##### BREAD WIKI #####################################################################################################################################
    ######################################################################################################################################################

    def _wiki_correct_length(self, text: str, limit: int = 300) -> str:
        """Corrects the length of the string, while, hopefully, keeping links intact."""

        period_location = text[:limit].rfind(".")
        addition = "".join([text, " "])

        if addition[period_location + 1] in [" ", "\\"]:
            return text[:period_location + 1]
        
        for char_id in range(len(text) - limit):
            if period_location + char_id >= 1000:
                break
            
            if addition[period_location + char_id] != ".":
                continue

            if addition[period_location + char_id + 1] not in [" ", "\\"]:
                continue
            
            return text[:period_location + char_id + 1]
        
        for char_id in range(limit):
            if period_location - char_id >= 1000:
                break

            if addition[period_location - char_id] != ".":
                continue

            if addition[period_location - char_id + 1] not in [" ", "\\"]:
                continue

            return text[:period_location - char_id + 1]
        
        text = text[:300]
        return text[:text.rfind(".") + 1]
    
    @bread.command(
        name = "wiki",
        brief = "Search the Bread Game Wiki!",
        description = "Search the Bread Game Wiki."
    )
    async def bread_wiki(self, ctx,
            *, search_term: typing.Optional[str] = commands.parameter(description = "The search term to search the wiki with.")
        ):
        if search_term is None:
            await ctx.reply("Here's a link to the wiki:\n<https://bread.miraheze.org/wiki/The_Bread_Game_Wiki>\nIf you want to search the wiki, use `%bread wiki <search term>`.")
            return
        
        if self.bread_wiki_searching:
            await ctx.reply("This commmand is currently being used somewhere, please wait until it's done to try again.")
            return
        
        async def error_message(embed: discord.Embed, sent_message: discord.Message) -> None:
            """Changes all 'Waiting to be loaded' messages to 'Something went wrong'"""
            modified = 0

            for field_id, field in enumerate(embed.fields):
                if "Waiting to be loaded" not in field.value:
                    continue
                
                embed.set_field_at(field_id, name=field.name, value=field.value.replace("Waiting to be loaded", "Something went wrong"), inline=field.inline)
                modified += 1
            
            if modified >= 1:
                await sent_message.edit(content=sent_message.content, embed=embed)
        
        embed = None
        sent_message = None

        try:
            self.bread_wiki_searching = True

            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://bread.miraheze.org/w/api.php?format=json&action=query&list=search&srlimit=3&srsearch={search_term}&redirects=true") as resp:
                    if resp.status != 200:
                        self.bread_wiki_searching = False
                        await ctx.reply("Something went wrong.")
                        return
                    
                    ret_json = await resp.json()

                description_prefix = f"Search results after searching for '{search_term}' on [The Bread Game Wiki](https://bread.miraheze.org/wiki/The_Bread_Game_Wiki):"
                
                if ret_json["query"]["searchinfo"]["totalhits"] == 0:
                    embed = u_interface.embed(
                        title = "Bread Wiki",
                        description = f"{description_prefix}\n\nThe search did not find any results, try different search terms."
                    )
                    await ctx.reply(embed=embed)
                    self.bread_wiki_searching = False
                    return
                
                search_results = []

                for page_info in ret_json["query"]["search"]:                    
                    search_results.append(page_info["title"])

                fields = [
                    (page_name, "[Link to wiki page.](https://bread.miraheze.org/wiki/{})\n\n*Waiting to be loaded.*".format(page_name.replace(" ", "_")), True)
                    for page_name in search_results
                ]

                embed = u_interface.embed(
                    title = "Bread Wiki",
                    description = f"{description_prefix}",
                    fields = fields + [("", "Not what you're looking for? Try different search terms.", False)]
                )

                sent_message = await ctx.reply(embed=embed)

                async with session.get("https://bread.miraheze.org/w/api.php?action=query&prop=revisions&titles={}&rvslots=*&rvprop=content&formatversion=2&format=json&redirects=true".format("|".join(search_results))) as resp:
                    if resp.status != 200:
                        self.bread_wiki_searching = False
                        await ctx.reply("Something went wrong.")
                        return
                    
                    ret_json = await resp.json()

                wiki_data = {}
                for data in ret_json["query"]["pages"]:
                    wiki_data[data["title"]] = data["revisions"][0]["slots"]["main"]["content"]

                redirect_data = {}
                if "redirects" in ret_json["query"]:
                    for data in ret_json["query"]["redirects"]:
                        redirect_data[data["from"]] = {"to": data["to"], "fragment": data.get("tofragment", None)}

                for field_id, page in enumerate(search_results):
                    page_get = page
                    page_fragment = None

                    redirect_text = ""
                    
                    for redirect_count in range(50):
                        if page_get in redirect_data:
                            page_fragment = redirect_data[page_get]["fragment"]
                            page_get = redirect_data[page_get]["to"]
                            redirect_text = f"*Redirected to {page_get}*\n"
                            continue
                        break

                    if page_fragment is None:
                        page_fragment = page_get
                    
                    sections = u_text.parse_wikitext(wiki_data[page_get], wiki_link="https://bread.miraheze.org/wiki/", page_title=page_get, return_sections=True)
                    
                    summary = "[Link to wiki page.](https://bread.miraheze.org/wiki/{})\n{}\n{}".format(page.replace(" ", "_"), redirect_text, sections[page_fragment])

                    if len(summary) > 900:
                        summary = self._wiki_correct_length(summary, 900)

                    embed.set_field_at(field_id, name=page, value=summary, inline=True)

                await sent_message.edit(content=sent_message.content, embed=embed)

            self.bread_wiki_searching = False
        except:
            self.bread_wiki_searching = False
            print(traceback.format_exc())

            if embed is not None and sent_message is not None:
                await error_message(embed, sent_message)

    

        
    ######################################################################################################################################################
    ##### BREAD GEM VALUE ################################################################################################################################
    ######################################################################################################################################################
    
    @bread.command(
        name = "gem_value",
        brief = "Provides the value of gems.",
        description = "Provides the value of gems if they were made into chessatrons.\nYou can reply to a stats message to get information from it. You can also provide the amount of dough you get per tron to override the stats parser. You can also provide the amount of each gem you have.\nIf you do not reply to a stats message you msut provide the amount of dough you get per tron and the amount of each gem you have."
    )
    async def bread_gem_value(self, ctx,
            tron_value: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of dough you get per tron."),
            red_gems: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of red gems you have."),
            blue_gems: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of blue gems you have."),
            purple_gems: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of purple gems you have."),
            green_gems: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of green gems you have."),
            gold_gems: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of gold gems you have.")
        ):
        ISSUE_TEXT = "If not replying to a stats message, provide the amount of dough per tron and the quantity of each gem. Reply to a stats message for automatic information retrieval. You can also specify the dough per tron to override the stats parser, as well as the quantity of each gem you possess."

        resolved_conflict = u_interface.resolve_conflict(
            message = ctx.message,
            stats_type = "main",
            user_provided = [tron_value, red_gems, blue_gems, purple_gems, green_gems, gold_gems],
            stat_keys = ["tron_value", u_values.gem_red, u_values.gem_blue, u_values.gem_purple, u_values.gem_green, u_values.gem_gold]
            )
        
        if not resolved_conflict:
            await ctx.reply(ISSUE_TEXT)
            return
        
        tron_value, red_gems, blue_gems, purple_gems, green_gems, gold_gems = resolved_conflict
        
        gem_sum = sum([red_gems, blue_gems, purple_gems, green_gems, gold_gems * 4])

        possible_trons = gem_sum // 32
        
        embed = u_interface.embed(
            title = "Gem Value",
            description = f"- {u_values.gem_red.internal_emoji}: {u_text.smart_number(red_gems)}\n- {u_values.gem_blue.internal_emoji}: {u_text.smart_number(blue_gems)}\n- {u_values.gem_purple.internal_emoji}: {u_text.smart_number(purple_gems)}\n- {u_values.gem_green.internal_emoji}: {u_text.smart_number(green_gems)}\n- {u_values.gem_gold.internal_emoji}: {u_text.smart_number(gold_gems)} -> {u_text.smart_number(gold_gems * 4)} (x4 recipe to greens)\nGem sum: {u_text.smart_number(gem_sum)}.\nPossible trons: {u_text.smart_number(possible_trons)}.\nAt a rate of {u_text.smart_number(tron_value)} per tron: **{u_text.smart_number(tron_value * possible_trons)} dough**."
        )

        await ctx.reply(embed=embed)

        
            

        
    ######################################################################################################################################################
    ##### BREAD TRON VALUE ###############################################################################################################################
    ######################################################################################################################################################
    
    @bread.command(
        name = "tron_value",
        aliases = ["chessatron_value"],
        brief = "Says how much dough you get per tron.",
        description = "Says how much dough you get per tron."
    )
    async def bread_tron_value(self, ctx,
            omegas: typing.Optional[u_converters.parse_int] = commands.parameter(description = "How many Omega Chessatrons you have."),
            shadowmegas: typing.Optional[u_converters.parse_int] = commands.parameter(description = "How many Shadowmega Chessatrons you have."),
            cc_level: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The level of Chessatron Contraption you have."),
            ascension: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The ascension you're on.")
        ):
        def generate_embed(omega, shadow, cc, a):
            return u_interface.embed(
                title = "Chessatron value",
                description = "With {}, {}, and {} of Chessatron Contraption on a{}, you would make **{} dough** from each Chessatron.".format(
                    u_text.smart_text(omega, "Omega Chessatron"),
                    u_text.smart_text(shadow, "Shadowmega Chessatron"),
                    u_text.smart_text(cc, "level"),
                    u_text.smart_number(a),
                    u_text.smart_number(u_bread.calculate_tron_value(ascension=a, omega_count=omega, shadowmegas=shadow, chessatron_contraption=cc))
                )
            )
    
        if None not in [omegas, shadowmegas, cc_level, ascension]:
            embed = generate_embed(omegas, shadowmegas, cc_level, ascension)
            await ctx.reply(embed=embed)
            return
        
        replied_to = u_interface.replying_mm_checks(ctx.message, require_reply=True, return_replied_to=True)

        if not replied_to:
            if omegas is None: omegas = 0
            if shadowmegas is None: shadowmegas = 0
            if cc_level is None: cc_level = 0
            if ascension is None: ascension = 0

            embed = generate_embed(omegas, shadowmegas, cc_level, ascension)
            await ctx.reply(embed=embed)
            return
        
        parsed = u_bread.parse_stats(replied_to)

        if parsed.get("stats_type") != "main":
            await ctx.reply("You must reply to bread stats, or provide the amount of each item you have.")
            return
        
        if omegas is None: omegas = parsed["stats"][u_values.omega_chessatron]
        if shadowmegas is None: shadowmegas = parsed["stats"][u_values.shadowmega_chessatron]
        if cc_level is None: cc_level = parsed["stats"]["chessatron_shadow_boost"]
        if ascension is None: ascension = parsed["stats"]["prestige_level"]

        embed = generate_embed(omegas, shadowmegas, cc_level, ascension)
        await ctx.reply(embed=embed)

        
            

        
    ######################################################################################################################################################
    ##### BREAD TIMESTAMPS ###############################################################################################################################
    ######################################################################################################################################################
    
    @bread.command(
        name = "timestamps",
        aliases = ["timestamp"],
        brief = "Provides a list of useful timestamps.",
        description = "Provides a list of useful timestamps, automatically converted into your time zone."
    )
    async def bread_timestamps(self, ctx):
        timestamp_list = [
            ("Bread o' clock", 1648591500),
            ("1st stonk tick", 1648602300),
            ("2nd stonk tick", 1648537500),
            ("3rd stonk tick", 1648559100),
            ("4th stonk tick", 1648580700)
        ]

        embed = u_interface.embed(
            title = "Timestamps",
            description = "All time are automatically converted into your time zone:\n{}".format(
                "\n".join(
                    [f"- {name}: <t:{time}:t>" for name, time in timestamp_list]
                )
            ),
        )

        await ctx.reply(embed=embed)

        
            

        
    ######################################################################################################################################################
    ##### BREAD PERCENT ##################################################################################################################################
    ######################################################################################################################################################
    
    @bread.command(
        name = "percent",
        brief = "Calculates percentages of values.",
        description = "Calculates percentages of values.\nAccepted percentage formats are 0.## or ##%, with ## being the number, of course."
    )
    async def bread_percent(self, ctx,
            percent: typing.Optional[u_converters.parse_percent] = commands.parameter(description = "The percentage to use."),
            value: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The number to get the precentage of."),
        ):
        if percent is None or value is None:
            await ctx.reply("You must provide the percentage to use and the value to use.\nSyntax: `%bread percent <percentage> <value>`.\nFor example, `%bread percent 75% 1,738,983`")
            return
        
        embed = u_interface.embed(
            title = "Percentage",
            description = "{}% of {} is **{}**".format(u_text.smart_number(percent * 100), u_text.smart_number(value), u_text.smart_number(round(value * percent, 2)))
        )
        await ctx.reply(embed=embed)

    

        
    ######################################################################################################################################################
    ##### BREAD GOLD GEM #################################################################################################################################
    ######################################################################################################################################################
    
    @bread.command(
        name = "gold_gem",
        aliases = ["gem_gold"],
        brief = "Figures out how many gold gems you can make.",
        description = "Figures out how many gold gems you can make.\nYou can reply to a stats message to get information from it. You can also provide the amount of each gem you have to override the stats parser.\nIf you do not reply to a stats message you msut provide the amount of each gem you have."
    )
    async def bread_gold_gem(self, ctx,
            red_gems: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of red gems you have."),
            blue_gems: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of blue gems you have."),
            purple_gems: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of purple gems you have."),
            green_gems: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of green gems you have."),
            gold_gems: typing.Optional[u_converters.parse_int] = commands.parameter(description = "Optional amount of gold gems you have.")
        ):

        ISSUE_TEXT = "If not replying to a stats message, provide the quantity of each gem you have aside from gold gems. Reply to a stats message to parse the stats. You can also specify the quantity of each gem you possess to override the stats parser."      

        async def determine_gems() -> bool | None:
            nonlocal red_gems, blue_gems, purple_gems, green_gems, gold_gems
            if None not in [red_gems, blue_gems, purple_gems, green_gems, gold_gems]:
                return
            
            replied_to = u_interface.replying_mm_checks(ctx.message, require_reply=True, return_replied_to=True)

            if not replied_to:
                if gold_gems is None and all([red_gems, blue_gems, purple_gems, green_gems]):
                    gold_gems = 0
                    return
                
                await ctx.reply(ISSUE_TEXT)
                return True
            
            parsed = u_bread.parse_stats(replied_to)

            if parsed.get("stats_type") != "main":
                if gold_gems is None:
                    gold_gems = 0
                    return
                
                await ctx.reply(ISSUE_TEXT)
                return True
            
            if red_gems is None:
                red_gems = parsed["stats"].get(u_values.gem_red, 0)
            if blue_gems is None:
                blue_gems = parsed["stats"].get(u_values.gem_blue, 0)
            if purple_gems is None:
                purple_gems = parsed["stats"].get(u_values.gem_purple, 0)
            if green_gems is None:
                green_gems = parsed["stats"].get(u_values.gem_green, 0)
            if gold_gems is None:
                gold_gems = parsed["stats"].get(u_values.gem_gold, 0)
        
        determined = await determine_gems()

        if determined: # True is only returned if a message is sent.
            return

        if gold_gems is None:
            gold_gems = 0

        gems = {
            u_values.gem_red: red_gems,
            u_values.gem_blue: blue_gems,
            u_values.gem_purple: purple_gems,
            u_values.gem_green: green_gems,
            u_values.gem_gold: gold_gems
        }
        
        if any([value > 1_000_000_000_000 for value in gems.values() if value is not None]):
            await ctx.reply("For optimization purposes, you can only provide up to 1 trillion of each gem.")
            return

        command_list, post_alchemy, solver_result = u_solvers.solver_wrapper(items = gems, maximize = u_values.gem_gold)
        
        embed = u_interface.embed(
            title = "Gold gem solver",
            description = "{}\nYou should be able to make **{}**.\nDough gain: {} ({} with [Gold Ring](<https://bread.miraheze.org/wiki/Gold_Ring>).)".format(
                "\n".join([f"{gem}: {u_text.smart_number(gems[gem])} -> {u_text.smart_number(post_alchemy[gem])}" for gem in gems]),
                u_text.smart_text(solver_result["gem_gold_total"], "gold gem"),
                u_text.smart_number(round(solver_result["gem_gold_total"] * 5000)),
                u_text.smart_number(round(solver_result["gem_gold_total"] * 10000))
            ),
            fields = [
                ("Commands:", "\n".join(command_list), False)
            ],
            footer_text = "On mobile you can tap and hold on the commands section to copy it."
        )
        
        await ctx.reply(embed=embed)

    

        
    ######################################################################################################################################################
    ##### BREAD DATA #####################################################################################################################################
    ######################################################################################################################################################
    
    bread_data_usage = [
        "%bread tron solve",
        "%bread tron quick"
    ]
    
    @bread.group(
        name = "data",
        brief = "Store data for use in other commands.",
        description = "Store data for use in other commands.\n\nThe following commands use this feature:\n{}".format("\n".join([f"- {item}" for item in bread_data_usage])),
        invoke_without_command = True,
        pass_context = True
    )
    async def bread_data(self, ctx):
        if ctx.invoked_subcommand is not None:
            return
        
        stored = u_bread.get_stored_data(
            database = database,
            user_id = ctx.author.id
        )

        stored_message = "You do not have any stored data." if stored is None else "You have stored data!"

        embed = u_interface.embed(
            title = "Stored data",
            description = f"{stored_message}\n\nUse `%bread data store` when replying to stats to store the data.\nUse `%bread data inventory` to view the current stored data.\nUse `%bread data clear` to clear the stored data.\n\nTo get a list of all the commands that use this feature, use `%help bread data`."
        )
        await ctx.reply(embed=embed)
        return
            
    

        
    ######################################################################################################################################################
    ##### BREAD DATA STORE ###############################################################################################################################
    ######################################################################################################################################################
    
    @bread_data.command(
        name = "store",
        brief = "Store data by replying to stats messages.",
        description = "Store data by replying to stats messages.\n\nTo get a list of all the command that use the stored data feature, use '%help bread data'"
    )
    async def bread_data_store(self, ctx):
        replied_to = u_interface.replying_mm_checks(ctx.message, require_reply=False, return_replied_to=True)

        if not replied_to:
            await ctx.reply("You must reply to stats message.")
            return
        
        parsed = u_bread.parse_stats(replied_to)

        if not parsed["parse_successful"]:
            await ctx.reply("You must reply to stats message.")
            return
        
        u_bread.update_stored_data(
            database = database,
            user_id = ctx.author.id,
            data = parsed["stats"]
        )

        embed = u_interface.embed(
            title = "Stored data",
            description = "Data stored!\n\nUse `%bread data inventory` to view the current stored data.\nUse `%bread data clear` to clear the stored data.\n\nTo get a list of all the commands that use the stored data feature, use `%help bread data`."
        )

        await ctx.reply(embed=embed)
            
    

        
    ######################################################################################################################################################
    ##### BREAD DATA INVENTORY ###########################################################################################################################
    ######################################################################################################################################################
    
    @bread_data.command(
        name = "inventory",
        brief = "View your current stored data.",
        description = "View your current stored data.\n\nTo get a list of all the command that use the stored data feature, use '%help bread data'"
    )
    async def bread_data_inventory(self, ctx,
            page: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The page of the inventory to view.")
        ):
        if page is None:
            page = 1

        page = max(page - 1, 0)

        stored = u_bread.get_stored_data(
            database = database,
            user_id = ctx.author.id
        )

        if stored is None:
            await ctx.reply("You do not have any stored data.\nUse `%bread data` to get more information on how to store data.")
            return
        
        PAGE_SIZE = 20 # How many items to show on each page.

        data_keys = list(stored.keys())
        max_page = math.ceil(len(data_keys) / PAGE_SIZE)

        page = min(page, max_page - 1)

        start = page * PAGE_SIZE
        end = min((page + 1) * PAGE_SIZE, len(data_keys))

        keys_show = data_keys[start:end]

        lines = []

        for key in keys_show:
            value = stored[key]
            if isinstance(value, dict):
                lines.append("{}: {}".format(
                    key,
                    ", ".join([u_values.get_item(item).internal_emoji for item in value.keys()])
                ))
                continue

            lines.append(f"{key}: {u_text.smart_number(stored[key])}")
        
        embed = u_interface.embed(
            title = "Stored data inventory",
            description = "Page {} of {}, showing items {} to {}.\nUse `%bread data inventory <page>` to specify a different page.".format(page + 1, max_page, start, end),
            fields = [
                ("", "\n".join(lines), False),
                ("", "Use `%bread data store` when replying to stats to store the data.\nUse `%bread data clear` to clear the stored data.\n\nTo get a list of all the commands that use the stored data feature, use `%help bread data`.", False)
            ]
        )
        await ctx.reply(embed=embed)
            
    

        
    ######################################################################################################################################################
    ##### BREAD DATA CLEAR ###############################################################################################################################
    ######################################################################################################################################################
    
    @bread_data.command(
        name = "clear",
        brief = "Clears your current stored data.",
        description = "Clears your current stored data.\n\nTo get a list of all the command that use the stored data feature, use '%help bread data'"
    )
    async def bread_data_clear(self, ctx):
        u_bread.clear_stored_data(
            database = database,
            user_id = ctx.author.id
        )
        
        embed = u_interface.embed(
            title = "Stored data cleared",
            description = "Your stored data has been cleared.\n\nUse `%bread data store` when replying to stats to store the data.\nUse `%bread data inventory` to view the current stored data.\n\nTo get a list of all the commands that use this feature, use `%help bread data`."
        )

        await ctx.reply(embed = embed)
        
            
    

        
    ######################################################################################################################################################
    ##### BREAD CHESSATRON ###############################################################################################################################
    ######################################################################################################################################################
    
    @bread.group(
        name = "chessatron",
        aliases = ["tron"],
        brief = "Chessatron related utility commands, including a solver.",
        description = "Chessatron related utility commands, including a solver.\nMost of these require having data stored with the `%bread data` feature.",
        invoke_without_command = True,
        pass_context = True
    )
    async def bread_chessatron(self, ctx):
        if ctx.invoked_subcommand is not None:
            return
        
        await ctx.send_help(self.bread_chessatron)

    

        
    ######################################################################################################################################################
    ##### BREAD CHESSATRON SOLVE #########################################################################################################################
    ######################################################################################################################################################
    
    @bread_chessatron.command(
        name = "solve",
        aliases = ["solver"],
        brief = "The chessatron solver.",
        description = "The chessatron solver.\nThis does require storing data with the `%bread data` feature."
    )
    async def bread_chessatron_solve(self, ctx):
        stored_data = u_bread.get_stored_data(
            database = database,
            user_id = ctx.author.id
        )

        if stored_data is None:
            await ctx.reply("You do not have any stored data.\nUse `%bread data` to get more information on how to store data.")
            return
        
        items = {}

        attributes = [u_values.all_chess_pieces, u_values.all_rares, u_values.all_specials]
        for attribute in attributes:
            for item in attribute:
                items[item] = stored_data.get(item, 0)

        items[u_values.bread] = stored_data.get(u_values.bread, 0) # Bread has no attributes we can search for :(
        items[u_values.chessatron] = stored_data.get(u_values.chessatron, 0)

        # Run the solver.
        
        command_list, post_alchemy, solver_result = u_solvers.solver_wrapper(
            items = items,
            maximize = u_values.chessatron
        )

        ################
        
        embed = u_interface.embed(
            title = "Chessatron solver",
            description = "{}\nYou should be able to make **{}** {} with an estimated gain of **{} dough**.".format(
                "\n".join([f"{item}: {u_text.smart_number(items[item])} -> {u_text.smart_number(post_alchemy[item])}" for item in items]),
                u_text.smart_number(solver_result["chessatron_total"]),
                u_values.chessatron,
                u_text.smart_number(round(solver_result["chessatron_total"] * u_bread.calculate_tron_value(
                    ascension = stored_data.get("prestige_level"),
                    omega_count = stored_data.get(u_values.omega_chessatron),
                    shadowmegas = stored_data.get(u_values.shadowmega_chessatron),
                    chessatron_contraption = stored_data.get("chessatron_shadow_boost")
                )))
            ),
            fields = [
                ("Commands:", "\n".join(command_list), False)
            ],
            footer_text = "On mobile you can tap and hold on the commands section to copy it."
        )
        
        await ctx.reply(embed=embed)

    

        
    ######################################################################################################################################################
    ##### BREAD CHESSATRON QUICK #########################################################################################################################
    ######################################################################################################################################################
    
    @bread_chessatron.command(
        name = "quick",
        brief = "Tells how many chessatrons can be made from just pawns.",
        description = "Tells how many chessatrons can be made from just pawns.\nNote that this uses the data stored with the `%bread data` feature.\nThis is assuming pawns are the limiting factor.\nIt uses this formula:\n((bpawn - wpawn) / 3 + wpawn) / 8\n\nThis does require storing data with the `%bread data` feature."
    )
    async def bread_chessatron_solve(self, ctx):
        stored_data = u_bread.get_stored_data(
            database = database,
            user_id = ctx.author.id
        )

        if stored_data is None:
            await ctx.reply("You do not have any stored data.\nUse `%bread data` to get more information on how to store data.")
            return
        
        bpawn = stored_data.get(u_values.bpawn, 0)
        wpawn = stored_data.get(u_values.wpawn, 0)

        initial_subtaction = bpawn - wpawn
        first_division = initial_subtaction / 3
        addition = first_division + wpawn
        final_division = addition / 8

        tron_value = u_bread.calculate_tron_value(
            ascension = stored_data.get("prestige_level"),
            omega_count = stored_data.get(u_values.omega_chessatron),
            shadowmegas = stored_data.get(u_values.shadowmega_chessatron),
            chessatron_contraption = stored_data.get("chessatron_shadow_boost")
        )

        embed = u_interface.embed(
            title = "Quick chessatrons",
            description = f"{u_values.bpawn}: {u_text.smart_number(bpawn)}\n{u_values.wpawn}: {u_text.smart_number(wpawn)}\nResult: **{u_text.smart_text(int(final_division), 'chessatron')}**.\nAt a rate of {u_text.smart_number(tron_value)} per tron: **{u_text.smart_number(round(int(final_division) * tron_value))} dough**",
            fields = [
                ("Equation:", f"- {u_text.smart_number(round(bpawn))} - {u_text.smart_number(round(wpawn))} = {u_text.smart_number(round(initial_subtaction))}\n- {u_text.smart_number(round(initial_subtaction))} / 3 = {u_text.smart_number(round(first_division, 2))}\n- {u_text.smart_number(round(first_division, 2))} + {u_text.smart_number(round(wpawn))} = {u_text.smart_number(round(addition, 2))}\n- {u_text.smart_number(round(addition, 2))} / 8 = {u_text.smart_number(round(final_division, 2))}", False)
            ]
        )
        await ctx.reply(embed=embed)

    

        
    ######################################################################################################################################################
    ##### BREAD CHESSATRON VALUE #########################################################################################################################
    ######################################################################################################################################################
    
    @bread_chessatron.command(
        name = "value",
        brief = "Estimation of tron value and gives gifting commands.",
        description = "Estimates the value of the chess pieces and gems in your stored data and gives you commands for gifting them to someone else via stonks.\nYou can provide a percentage to multiply the total value by.\n\nThis is using the data stored with the `%bread data` feature."
    )
    async def bread_chessatron_solve(self, ctx,
            user: typing.Optional[discord.Member] = commands.parameter(description = "The person to gift the dough to."),
            tron_value: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of dough you get per tron."),
            percentage: typing.Optional[u_converters.parse_percent] = commands.parameter(description = "What percentage of the tron dough to gift."),
            stonk: typing.Optional[u_values.StonkConverter] = commands.parameter(description = "The stonk to use, will use whatever is closest if nothing is given.")
        ):
        stored = u_bread.get_stored_data(
            database = database,
            user_id = ctx.author.id
        )

        if stored is None:
            await ctx.reply("You do not have any stored data.\nUse `%bread data` to get more information on how to store data.")
            return
        
        if user is None:
            await ctx.reply("You must provide a person to gift the stonks to.")
            return
        
        if tron_value is None:
            tron_value = u_bread.calculate_tron_value(
                ascension = stored.get("prestige_level"),
                omega_count = stored.get(u_values.omega_chessatron),
                shadowmegas = stored.get(u_values.shadowmega_chessatron),
                chessatron_contraption = stored.get("chessatron_shadow_boost")
            )
        
        if percentage is None:
            percentage = 1
        
        bpawns = stored.get(u_values.bpawn, 0)
        wpawns = stored.get(u_values.wpawn, 0)

        gems = {
            gem: stored.get(gem, 0)
            for gem in u_values.all_shiny
        }

        pawn_contribution_initial = bpawns + wpawns
        pawn_contribution_final = pawn_contribution_initial / 16

        gem_contribution_initial = sum(gems.values()) + (gems.get(u_values.gem_gold) * 3)
        gem_contribution_final = gem_contribution_initial / 32

        total_trons = int(pawn_contribution_final + gem_contribution_final)
        total_dough = round(total_trons * tron_value)
        after_percentage = round(total_dough * percentage)

        if stonk is None:
            stonk = u_stonks.closest_to_dough(after_percentage)
        
        gift_amount, remaining = divmod(after_percentage, stonk.value())

        sm = u_text.smart_number
        
        embed = u_interface.embed(
            title = "Chessatron value estimation",
            description = f"{u_values.bpawn}: {sm(bpawns)}, {u_values.wpawn}: {sm(wpawns)}\n{', '.join([f'{gem}: {sm(gems[gem])}' for gem in u_values.all_shiny])}",
            fields = [
                ("", f"Trons from pieces: {sm(round(pawn_contribution_final, 2))}\nTrons from gem chessatron: {sm(round(gem_contribution_final, 2))}\nTotal chessatrons: **{u_text.smart_text(total_trons, 'chessatron')}**, which, at a rate of {sm(tron_value)} per chessatron, is worth **{sm(total_dough)} dough**.\n\nWith a percentage of {percentage * 100}%, it results in **{sm(after_percentage)} dough**.\n\nGifting {sm(gift_amount)} {stonk} results in {sm(remaining)} remaining dough.", False),
                ("Equation:", f"- {sm(bpawns)} + {sm(wpawns)} = {sm(pawn_contribution_initial)}\n- {sm(pawn_contribution_initial)} / 16 = {sm(pawn_contribution_final)}\n\n- {sm(gem_contribution_initial)} (Sum of gems in red gems.)\n- {sm(gem_contribution_initial)} / 32 = {sm(gem_contribution_final)}\n\n- {sm(pawn_contribution_final)} + {sm(gem_contribution_final)} = {sm(total_trons)}\n- {sm(tron_value)} * {sm(total_trons)} = {sm(total_dough)}\n\n- {percentage * 100}% * {sm(total_dough)} = {sm(after_percentage)}", True),
                ("Commands:", f"$bread gift {user.id} {gift_amount} {stonk}", True)
            ],
            footer_text = "On mobile you can tap and hold on the commands section to copy it."
        )

        await ctx.reply(embed=embed)

    

        
    ######################################################################################################################################################
    ##### BREAD PROBABILITY ##############################################################################################################################
    ######################################################################################################################################################
    
    @bread.command(
        name = "probability",
        brief = "Calculates probability via Binomial Distribution.",
        description = "Calculates probability via Binomial Distribution."
    )
    async def bread_probability(self, ctx,
            chance: typing.Optional[u_converters.parse_percent] = commands.parameter(description = "The chance of success."),
            trials: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The number of trials."),
            successes: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The number of successes.")
        ):
        if None in [chance, trials, successes]:
            await ctx.reply("You must provide the chance of success, the number of trials, and the number of successes.")
            return
        
        chance = max(min(chance, 1), 0)
        
        if trials < 1:
            await ctx.reply("The number of trials must be greater than 0.")
            return
        
        if successes < 1:
            await ctx.reply("The number of successes must be greater than 0.")
            return
        
        if trials > 1_000_000_000_000:
            await ctx.reply("That is too many trials.")
            return
        
        if trials < successes:
            await ctx.reply("The number of trials must be greater than the number of successes.")
            return
        
        equal = binom.pmf(successes, trials, chance)
        less = binom.cdf(successes, trials, chance, loc=True)
        less_or_equal = binom.cdf(successes, trials, chance)
        greater = 1 - less_or_equal
        greater_or_equal = 1 - less

        embed = u_interface.embed(
            title = "Probability",
            description = "With {} trials and {} successes with a {}% chance of success:".format(u_text.smart_number(trials), u_text.smart_number(successes), round(chance * 100, 2)),
            fields = [
                ("", "Exactly that many successes: **{}%**\nThat many successes *or* more: **{}%**\nMore than that many successes: **{}%**\nThat many successes *or* fewer: **{}%**\nFewer than that many successes: **{}%**".format(
                    u_text.smart_number(round(equal * 100, 2)),
                    u_text.smart_number(round(greater_or_equal * 100, 2)),
                    u_text.smart_number(round(greater * 100, 2)),
                    u_text.smart_number(round(less_or_equal * 100, 2)),
                    u_text.smart_number(round(less * 100, 2))
                ), False)
            ]
        )
        await ctx.reply(embed=embed)

async def setup(bot: commands.Bot):
    cog = Bread_cog()
    cog.bot = bot

    global database
    database = bot.database
    
    # Add attributes for sys.modules and globals() so the _reload_module() function in utility.custom can read it and get the module objects.
    cog.modules = sys.modules
    cog.globals = globals()
    
    await bot.add_cog(cog)