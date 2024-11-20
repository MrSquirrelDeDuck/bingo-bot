"""This cog is for utility commands for The Bread Game."""

from discord.ext import commands
import discord
import typing
import datetime
import copy
import math
import re
import random
import time

# pip install pytz
import pytz

# pip install scipy
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
import utility.bingo as u_bingo
import utility.images as u_images

database = None # type: u_files.DatabaseInterface

class Bread_cog(
        u_custom.CustomCog,
        name="Bread",
        description="Utility commands for The Bread Game!"
    ):
    currently_interacting = []

    bread_wiki_searching = False

    # This is a list of unix timestamps, such that if you use <t:time_keys[0]> it'll be the right time.
    # time_keys = ["1648850700", "1648854300", "1648857900", "1648861500", "1648865100", "1648868700", "1648785900", "1648789500", "1648793100", "1648796700", "1648800300", "1648803900", "1648807500", "1648811100", "1648814700", "1648818300", "1648821900", "1648825500", "1648829100", "1648832700", "1648836300", "1648839900", "1648843500", "1648847100"]
    time_keys = {
        0: "<t:1648850700:t>",
        1: "<t:1648854300:t>",
        2: "<t:1648857900:t>",
        3: "<t:1648861500:t>",
        4: "<t:1648865100:t>",
        5: "<t:1648868700:t>",
        6: "<t:1648785900:t>",
        7: "<t:1648789500:t>",
        8: "<t:1648793100:t>",
        9: "<t:1648796700:t>",
        10: "<t:1648800300:t>",
        11: "<t:1648803900:t>",
        12: "<t:1648807500:t>",
        13: "<t:1648811100:t>",
        14: "<t:1648814700:t>",
        15: "<t:1648818300:t>",
        16: "<t:1648821900:t>",
        17: "<t:1648825500:t>",
        18: "<t:1648829100:t>",
        19: "<t:1648832700:t>",
        20: "<t:1648836300:t>",
        21: "<t:1648839900:t>",
        22: "<t:1648843500:t>",
        23: "<t:1648847100:t>"
    }

    async def hourly_task(self: typing.Self):
        """Code that runs for every hour."""
        self.currently_interacting.clear()
        self.bread_wiki_searching = False

    ######################################################################################################################################################
    ##### UTILITY FUNCTIONS ##############################################################################################################################
    ######################################################################################################################################################

    def _get_reminder_data(self: typing.Self) -> dict:
        """Returns the reminder data as loaded from data/reminders.json."""
        return database.load("reminders")
    
    def _save_reminder_data(
            self: typing.Self,
            data: dict
        ) -> None:
        """Saves a dict to the reminder data file."""
        database.save("reminders", data=data)
    
    async def _send_reminder_list(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            target: discord.Member,
            footer: str,
            reminder_data: dict = None
        ) -> discord.Message:
        """Sends the list of reminders the author has, using ctx."""
        if reminder_data is None:
            reminder_data = self._get_reminder_data()

        reminder_list = []

        for reminder in reminder_data["reminder_list"]:
            if reminder["user"] == target.id:
                reminder_list.append("At {} ({}): {}".format(reminder["hour"], self.time_keys.get(reminder["hour"], "error"), reminder["text"]))
        
        if len(reminder_list) == 0:
            reminder_list = "You don't have any reminders set!\nTo add reminders, use `%bread reminder add`."
        else:
            reminder_list = "- {}\n{}".format("\n- ".join(reminder_list), footer)
        
        embed = u_interface.gen_embed(
            title = "Bread Reminders",
            description = reminder_list
        )
        
        return await ctx.reply(embed=embed)

    ######################################################################################################################################################
    ##### CHECKS #########################################################################################################################################
    ######################################################################################################################################################

    async def reminder_disallowed(ctx: commands.Context | u_custom.CustomContext) -> bool:
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
    async def bread(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        if ctx.invoked_subcommand is not None:
            return
        
        await ctx.send_help(self.bread)

    
    
    
    
    
      
    @bread.command(
        name = "help",
        description = "Sends the help text for the bread command.",
        brief = "Sends the help text for the bread command.",
        hidden = True
    )
    async def bread_help(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        await ctx.send_help(self.bread)

    
    
    
    
    
    
    @bread.command(
        name = "stonks",
        aliases = ["stonk"],
        description = "To use the Bingo-Bot's stonk commands, use '%stonks'.",
        brief = "To use the Bingo-Bot's stonk commands, use '%stonks'.",
        hidden = True
    )
    async def bread_stonks(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        await ctx.reply("To use the Bingo-Bot's stonk-related commands, use `%stonks` instead of `%bread stonks`.")

    
    
    
    
    
    
    ######################################################################################################################################################
    ##### BREAD TIME #####################################################################################################################################
    ######################################################################################################################################################
    
    @bread.command(
        name = "time",
        description = "Get the current time in Bread Standard Time.",
        brief = "Get the current time in Bread Standard Time."
    )
    async def bread_time(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        def is_dst(dt=None, timezone="UTC"):
            if dt is None:
                dt = datetime.datetime.now(tz=datetime.UTC)
            timezone = pytz.timezone(timezone)
            timezone_aware_date = timezone.localize(dt, is_dst=None)
            return timezone_aware_date.tzinfo._dst.seconds != 0

        apply_dst = is_dst(datetime.datetime.now(), timezone="US/Pacific")

        timestamp = ctx.message.created_at.replace(microsecond=0, tzinfo=None)

        if apply_dst:
            timestamp = timestamp + datetime.timedelta(hours=1)
        
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

        embed = u_interface.gen_embed(
            title = f"{hour_12}:{minutes}:{seconds} {time_suffix}",
            description = f"In Bread Standard Time is currently {hour_12}:{minutes}:{seconds} {time_suffix} ({boc_timedelta}) on the {day_text} of {names[month]}, {years} AB.\n\nThe next Bread o' clock is <t:{int((next_breadoclock - datetime.datetime(1970,1,1)).total_seconds())}:R>."
        )

        await ctx.reply(embed = embed)

    
    
    
    
    
    
    @commands.command(
        name = "breadtime",
        description = "Shortcut for '%bread time'",
        brief = "Shortcut for '%bread time'"
    )
    async def breadtime(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
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
    async def bread_reminder(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
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
    async def bread_reminder_add(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
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
        
        if hour < 0 or hour > 23:
            await ctx.reply("The hour must be between 0 and 23.")
            return
        
        if len(reminder_text) > 128:
            await ctx.reply("That text is a little too long, please make it 128 characters or fewer.")
            return
        
        if u_text.has_ping(reminder_text):
            await ctx.reply("Reminders cannot contain pings.")
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

        embed = u_interface.gen_embed(
            title = "Reminder added!",
            description = "Added reminder for {} ({}) with the text:\n{}".format(hour, self.time_keys.get(hour, "error"), reminder_text)
        )

        await ctx.reply(embed = embed)

    
    
    
    
    
    
    @bread_reminder.command(
        name = "remove",
        brief = "Remove an existing reminder.",
        description = "Remove an reminder.\nTakes a parameter that is the time of the reminder you want to remove."
    )
    @commands.check(reminder_disallowed)
    async def bread_reminder_remove(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
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

        embed = u_interface.gen_embed(
            title = "Reminder removed!",
            description = "Removed reminder for {} ({}) that had the text:\n{}".format(remove_data["hour"], self.time_keys.get(remove_data["hour"], "error"), remove_data["text"])
        )

        await ctx.reply(embed=embed)

    
    
    
    
    
    
    @bread_reminder.command(
        name = "edit",
        brief = "Edit an existing reminder.",
        description = "Edit an existing reminder, you can modify the text or the hour of the reminder."
    )
    @commands.check(reminder_disallowed)
    async def bread_reminder_edit(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            reminder_hour: typing.Optional[int] = commands.parameter(description = "The hour of the existing reminder you want to modify."),
            modification_type: typing.Optional[str] = commands.parameter(description = "The type of data that will be modified: 'hour' or 'text'."),
            new_information: typing.Optional[str] = commands.parameter(description = "The new information that will be used.")
        ):
        target = ctx.author

        if u_checks.in_authority(ctx):
            target = discord.utils.find(lambda m: m.id == reminder_hour, ctx.guild.members)
            if target is None:
                target = ctx.author
            else:
                if modification_type is not None:
                    reminder_hour = int(copy.copy(modification_type))
                if new_information is not None:
                    modification_type = copy.copy(new_information)
                if modification_type is not None:
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
            
            if u_text.has_ping(new_information):
                await ctx.reply("Reminder text cannot contain pings.")
                return
            
            if len(new_information) > 128:
                await ctx.reply("That text is a little too long, please shorten it to 128 characters or fewer.")
                return
            
            new_information = u_text.after_parameter(ctx, modification_type)

            reminder_modify["text"] = new_information
        
        reminder_data["reminder_list"][reminder_id] = reminder_modify

        self._save_reminder_data(reminder_data)

        embed = u_interface.gen_embed(
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
    async def bread_reminder_allow(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            target: typing.Optional[discord.Member] = commands.parameter(description = "Some identifier for the user to allow reminder usage.")
        ):
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
    async def bread_reminder_disallow(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            target: typing.Optional[discord.Member] = commands.parameter(description = "Some identifier for the user to disallow reminder usage.")
        ):
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
    async def bread_loaf_converter(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            current: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of Loaf Converters you currently have."),
            self_converting_yeast: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of Self Converting Yeast you currently have.")
        ):
        if ctx.invoked_subcommand is not None:
            return

        attempted_parse = await u_bread.parse_attempt(ctx.message, require_reply=True, require_stats=False)
        
        if attempted_parse:
            current, self_converting_yeast = attempted_parse["stats"].get("loaf_converter", 0), attempted_parse["stats"].get("loaf_converter_discount", 0)

        if current is None:
            await ctx.reply("You must provide the amount of Loaf Converters you have.\nSyntax: `%bread loaf_converter <current amount of lcs> <level of scy>`.")
            return
        
        if self_converting_yeast is None:
            self_converting_yeast = 0

        next_cost = (current + 1) * (256 - (self_converting_yeast * 12))

        embed = u_interface.gen_embed(
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
    async def bread_loaf_converter_calculate(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            current: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of Loaf Converters you currently have."),
            goal: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of Loaf Converters you would like to have."),
            self_converting_yeast: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of Self Converting Yeast you currently have.")
        ):
        attempted_parse = await u_bread.parse_attempt(ctx.message, require_reply=True, require_stats=False)

        if attempted_parse:
            goal = current
            current, self_converting_yeast = attempted_parse["stats"].get("loaf_converter", 0), attempted_parse["stats"].get("loaf_converter_discount", 0)

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

        embed = u_interface.gen_embed(
            title = "Loaf Converter calculation",
            description = f"It would require **{u_text.smart_number(dough_required)}** dough to purchase the {u_text.smart_text(goal - current, 'Loaf Converter')} needed.\nWith {u_text.smart_text(self_converting_yeast, 'level')} of Self Converting Yeast, you would save **{u_text.smart_number(dough_required_no_scy - dough_required)} dough**."
        )

        await ctx.reply(embed=embed)

    
    
    
    
    
    @bread_loaf_converter.command(
        name = "dough",
        brief = "Says how many Loaf Converters you can get with an amount of dough.",
        description = "Says how many Loaf Converters you can get with an amount of dough.\nIf you reply to a stats message it will use the stats given, and will determine how much dough you have from there. You can still provide a dough amount for it to use instead."
    )
    async def bread_loaf_converter_dough(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            dough: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of dough you have. Read above for more info."),
            current: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of Loaf Converters you currently have."),
            self_converting_yeast: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of Self Converting Yeast you currently have.")
        ):
        attempted_parse = await u_bread.parse_attempt(ctx.message, require_reply=True, require_stats=False)

        if attempted_parse:
            current, self_converting_yeast = attempted_parse["stats"].get("loaf_converter", 0), attempted_parse["stats"].get("loaf_converter_discount", 0)

            if dough is None:
                dough = attempted_parse["stats"]["total_dough"]

                for stonk in u_values.stonks:
                    if stonk not in attempted_parse["stats"]:
                        continue

                    dough += stonk.value(database=database) * attempted_parse["stats"][stonk]
        
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

        embed = u_interface.gen_embed(
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
    async def bread_gamble(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        if ctx.invoked_subcommand is not None:
            return
        
        await ctx.send_help(self.bread_gamble)

    
    
    
    
    @bread_gamble.command(
        name = "initial",
        brief = "Get the initial board of a gamble.",
        description = "Get the initial board of a gamble."
    )
    async def bread_gamble_initial(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        replied_to = u_interface.replying_mm_checks(ctx.message, require_reply = True, return_replied_to = True)

        if not replied_to:
            await ctx.reply("You must reply to a gamble message.")
            return
        
        gamble_messages = database.load("bread", "gamble_messages", default={})

        message_key = f"{replied_to.channel.id}.{replied_to.id}"

        if message_key not in gamble_messages:
            await ctx.reply("I don't have that gamble in my storage.\nI only store the last 500 gambles that occurred.")
            return
        
        embed = u_interface.gen_embed(
            title = "Initial board.",
            description = "The initial board of that gamble:\n\n{}".format(gamble_messages[message_key]["content"])
        )

        await ctx.reply(embed=embed)

    

        
    ######################################################################################################################################################
    ##### BREAD WIKI #####################################################################################################################################
    ######################################################################################################################################################

    def _wiki_correct_length(
            self: typing.Self,
            text: str,
            limit: int = 300
        ) -> str:
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
    async def bread_wiki(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            *, search_term: typing.Optional[str] = commands.parameter(description = "The search term to search the wiki with.")
        ):
        if self.bread_wiki_searching:
            await ctx.reply("This commmand is currently being used somewhere, please wait until it's done to try again.")
            return
        
        try:
            self.bread_wiki_searching = True

            await u_interface.handle_wiki_search(
                ctx = ctx,
                wiki_link = "https://bread.miraheze.org/wiki/",
                wiki_main_page = "https://bread.miraheze.org/wiki/The_Bread_Game_Wiki",
                wiki_name = "The Bread Game Wiki",
                wiki_api_url = "https://bread.miraheze.org/w/api.php",
                search_term = search_term
            )

            self.bread_wiki_searching = False
        except:
            self.bread_wiki_searching = False

            # After ensuring bread_wiki_searching has been reset, reraise the exception so the "Something went wrong processing that command." message is still sent.
            raise

    

        
    ######################################################################################################################################################
    ##### BREAD GEM VALUE ################################################################################################################################
    ######################################################################################################################################################
    
    @bread.command(
        name = "gem_value",
        brief = "Provides the value of gems.",
        description = "Provides the value of gems if they were made into chessatrons.\nYou can reply to a stats message to get information from it. You can also provide the amount of dough you get per tron to override the stats parser. You can also provide the amount of each gem you have.\nIf you do not reply to a stats message you msut provide the amount of dough you get per tron and the amount of each gem you have."
    )
    async def bread_gem_value(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            tron_value: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of dough you get per tron."),
            red_gems: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of red gems you have."),
            blue_gems: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of blue gems you have."),
            purple_gems: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of purple gems you have."),
            green_gems: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of green gems you have."),
            gold_gems: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of gold gems you have.")
        ):
        # Okay, so here's how the parameters need to work for the gems:
        # - If anything is provided in the command parameters, use it.
        # - If the user replies to a stats message that has the individual items, use that for any item not covered by parameters.
        # - If the user has stored data, use that for any items not already determined.

        # If the tron value is not provided in the command, if it's in the replied-to stats message, use that. Use the stored data as a backup if those two fail.

        resolve_values = {
            u_values.gem_red: red_gems,
            u_values.gem_blue: blue_gems,
            u_values.gem_purple: purple_gems,
            u_values.gem_green: green_gems,
            u_values.gem_gold: gold_gems
        }

        using_stored_data = False

        parsed_data = None
        stored_data = None

        async def get_parsed():
            nonlocal parsed_data
            if parsed_data is None:
                replied = u_interface.replying_mm_checks(
                    message = ctx.message,
                    require_reply = True,
                    return_replied_to = True
                )

                if not replied:
                    parsed_data = {}
                    return parsed_data

                parsed_data = await u_bread.parse_stats(replied)

                if parsed_data.get("parse_successful"):
                    parsed_data = parsed_data.get("stats")
                else:
                    parsed_data = {}

            return parsed_data

        def get_stored():
            nonlocal stored_data, using_stored_data
            if stored_data is None:
                stored_data = u_bread.get_stored_data(
                    database = database,
                    user_id = ctx.author.id
                )
                using_stored_data = True
            return stored_data

        for gem in u_values.all_shiny:
            if resolve_values.get(gem) is None:
                if parsed_data is None:
                    parsed_data = await get_parsed()
                
                if gem in parsed_data:
                    resolve_values[gem] = parsed_data[gem]
                    continue

                if stored_data is None:
                    stored_data = get_stored()

                resolve_values[gem] = stored_data.get(gem, 0)

        if tron_value is None:
            if parsed_data is None:
                parsed_data = await get_parsed()

            if "prestige_level" in parsed_data and \
               "chessatron_shadow_boost" in parsed_data and \
               u_values.omega_chessatron in parsed_data and \
               u_values.shadowmega_chessatron in parsed_data:
                tron_value = u_bread.calculate_tron_value(
                    ascension = parsed_data["prestige_level"],
                    omega_count = parsed_data[u_values.omega_chessatron],
                    shadowmegas = parsed_data[u_values.shadowmega_chessatron],
                    chessatron_contraption = parsed_data["chessatron_shadow_boost"]
                )
            else:
                if stored_data is None:
                    stored_data = get_stored()
                
                tron_value = stored_data.tron_value

        red_gems, blue_gems, purple_gems, green_gems, gold_gems = resolve_values.values()
        
        gem_sum = sum([red_gems, blue_gems, purple_gems, green_gems, gold_gems * 4])

        possible_trons = gem_sum // 32

        # Generate the commands list.
        command_list = []

        gem_amounts = {
            u_values.gem_red: red_gems,
            u_values.gem_blue: blue_gems,
            u_values.gem_purple: purple_gems,
            u_values.gem_green: green_gems,
            u_values.gem_gold: gold_gems * 4
        }
        gem_raw = list(gem_amounts.values())
        
        for iterator, gem in reversed(list(enumerate(gem_amounts.keys()))):
            if sum(gem_raw[iterator + 1:]) == 0:
                continue

            command_list.append("$bread distill {amount} {gem} {recipe} y".format(
                amount = sum(gem_raw[iterator + 1:]) // (4 if gem == u_values.gem_green else 1),
                gem = gem.internal_name,
                recipe = 1 if gem == u_values.gem_red else 2
            ))
        
        command_list.append(f"$bread gem_chessatron {possible_trons}")

        if using_stored_data:
            using_stored_data = "(Using stored data, use `%bread data` for more info.)\n"
        else:
            using_stored_data = str()
        
        # Generate the embed to send.
        embed = u_interface.gen_embed(
            title = "Gem Value",
            description = f"{using_stored_data}- {u_values.gem_red.internal_emoji}: {u_text.smart_number(red_gems)}\n- {u_values.gem_blue.internal_emoji}: {u_text.smart_number(blue_gems)}\n- {u_values.gem_purple.internal_emoji}: {u_text.smart_number(purple_gems)}\n- {u_values.gem_green.internal_emoji}: {u_text.smart_number(green_gems)}\n- {u_values.gem_gold.internal_emoji}: {u_text.smart_number(gold_gems)} -> {u_text.smart_number(gold_gems * 4)} (x4 recipe to greens)\nGem sum: {u_text.smart_number(gem_sum)}.\nPossible trons: {u_text.smart_number(possible_trons)}.\nAt a rate of {u_text.smart_number(tron_value)} per tron: **{u_text.smart_number(tron_value * possible_trons)} dough**.",
            fields = [
                ("Commands:", "\n".join(command_list), False)
            ],
            footer_text = "On mobile you can tap and hold on the commands section to copy it."
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
    async def bread_tron_value(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            omegas: typing.Optional[u_converters.parse_int] = commands.parameter(description = "How many Omega Chessatrons you have."),
            shadowmegas: typing.Optional[u_converters.parse_int] = commands.parameter(description = "How many Shadowmega Chessatrons you have."),
            cc_level: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The level of Chessatron Contraption you have."),
            ascension: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The ascension you're on.")
        ):
        
        # This needs to be in the same order as the command parameters.
        resolve_values = {
            u_values.omega_chessatron: omegas,
            u_values.shadowmega_chessatron: shadowmegas,
            "chessatron_shadow_boost": cc_level,
            "prestige_level": ascension
        }

        resolved = await u_interface.resolve_conflict(
            database = database,
            ctx = ctx,
            resolve_keys = list(resolve_values.keys()),
            command_provided = list(resolve_values.values())
        )
        
        using_stored_data, stored_data, omegas, shadowmegas, cc_level, ascension = resolved

        tron_value = u_bread.calculate_tron_value(
            ascension = ascension,
            omega_count = omegas,
            shadowmegas = shadowmegas,
            chessatron_contraption = cc_level
        )
        
        embed = u_interface.gen_embed(
            title = "Chessatron value",
            description = "{}With {}, {}, and {} of Chessatron Contraption on a{}, you would make **{} dough** from each Chessatron.".format(
                "(Using stored data, use `%bread data` for more info.)\n" if using_stored_data else "",
                u_text.smart_text(omegas, "Omega Chessatron"),
                u_text.smart_text(shadowmegas, "Shadowmega Chessatron"),
                u_text.smart_text(cc_level, "level"),
                u_text.smart_number(ascension),
                u_text.smart_number(tron_value)
            )
        )

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
    async def bread_timestamps(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        timestamp_list = [
            ("Bread o' clock", 1648591500),
            ("1st stonk tick", 1648602300),
            ("2nd stonk tick", 1648537500),
            ("3rd stonk tick", 1648559100),
            ("4th stonk tick", 1648580700)
        ]

        embed = u_interface.gen_embed(
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
        aliases = ["percentage"],
        brief = "Calculates percentages of values.",
        description = "Calculates percentages of values.\nAccepted percentage formats are 0.## or ##%, with ## being the number, of course."
    )
    async def bread_percent(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            percent: typing.Optional[u_converters.parse_percent] = commands.parameter(description = "The percentage to use."),
            value: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The number to get the precentage of."),
        ):
        if percent is None or value is None:
            await ctx.reply("You must provide the percentage to use and the value to use.\nSyntax: `%bread percent <percentage> <value>`.\nFor example, `%bread percent 75% 1,738,983`")
            return
        
        try:
            embed = u_interface.gen_embed(
                title = "Percentage",
                description = "{}% of {} is:".format(u_text.smart_number(percent * 100), u_text.smart_number(value)),
                fields = [("{:,.2f}".format(value * percent), "", False)],
                footer_text = "On mobile, you can tap and hold on the number to copy it."
            )
        except OverflowError:
            await ctx.reply("Unfortunately that is too large to calculate.")
            return
        
        await ctx.reply(embed=embed)

    

        
    ######################################################################################################################################################
    ##### BREAD GOLD GEM #################################################################################################################################
    ######################################################################################################################################################
    
    @bread.command(
        name = "gold_gem",
        aliases = ["gem_gold"],
        brief = "Figures out how many gold gems you can make from other gems.",
        description = "Figures out how many gold gems you can make from other gems.\nNote that this uses the data stored with the `%bread data` feature.\n\nModifier list:\n- `[item name]>[amount]` will tell the solver to leave you with the amount or more of that item.\n- `[item name]=[amount]` will tell the solver to leave you with exactly that of that item."
    )
    async def bread_gold_gem(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            *, modifiers: typing.Optional[str] = commands.parameter(description = "Modifiers to give the solver. See above for modifier info.")
        ):
        replied = u_interface.replying_mm_checks(
            message = ctx.message,
            require_reply = False,
            return_replied_to = True
        )

        async def parse_attempt() -> bool:
            if not replied:
                return False
            
            parse = await u_bread.parse_stats(replied)

            if not parse.get("parse_successful"):
                return False
            
            if not (parse.get("stats_type") == "main" or parse.get("stats_type") == "dump"):
                return False

            return parse
        
        parsed = await parse_attempt()

        if not parsed:
            using_stored = True
            stats = u_bread.get_stored_data(
                database = database,
                user_id = ctx.author.id
            )
            if not stats.loaded:
                await ctx.reply("Please reply to a message that contains your gem stats or use stored data.\nUse `%bread data` to get more information on how to store data.")
                return
        else:
            using_stored = False
            stats = parsed.get("stats", {})

        ###################################################

        if modifiers is None:
            modifiers = ""

        modifier_list = modifiers.split(" ")

        disabled_items = []
        minimum_items = {}
        equal_items = {}

        for modifier in modifier_list:
            if modifier.startswith("!"):
                item_name = modifier.replace("!", "", 1)
                get_item = u_values.get_item(item_name)
                if get_item:
                    disabled_items.append(get_item)
            if modifier.count(">") == 1:
                potential_item, potential_amount = modifier.split(">")

                potential_item = u_values.get_item(potential_item)

                if potential_item is None:
                    continue

                try:
                    potential_amount = u_converters.parse_int(potential_amount)
                except ValueError:
                    continue

                minimum_items[potential_item] = potential_amount
            if modifier.count("=") == 1:
                potential_item, potential_amount = modifier.split("=")

                potential_item = u_values.get_item(potential_item)

                if potential_item is None:
                    continue

                try:
                    potential_amount = u_converters.parse_int(potential_amount)
                except ValueError:
                    continue

                equal_items[potential_item] = potential_amount

        ###################################################

        gems = {
            u_values.gem_red: stats.get(u_values.gem_red),
            u_values.gem_blue: stats.get(u_values.gem_blue),
            u_values.gem_purple: stats.get(u_values.gem_purple),
            u_values.gem_green: stats.get(u_values.gem_green),
            u_values.gem_gold: stats.get(u_values.gem_gold)
        }
        
        if any([value > 1_000_000_000_000 for value in gems.values() if value is not None]):
            await ctx.reply("For optimization purposes, you can only provide up to 1 trillion of each gem.")
            return
        
        try:
            await ctx.message.add_reaction("✅")
        except:
            pass

        try:
            disabled_recipes = stats.disallowed_recipes
        except AttributeError:
            disabled_recipes = None

        full_result = u_solvers.solver_wrapper(
            items = gems,
            maximize = u_values.gem_gold,
            disabled_recipes = disabled_recipes,
            disabled_items = disabled_items,
            minimum_items = minimum_items,
            equal_items = equal_items
        )

        if not full_result:
            if full_result is None:
                embed = u_interface.gen_embed(
                    title = "Gold gem solver",
                    description = "Timeout reached.\nThe solver took too long to run and was stopped before it found a solution. Please do not try again, as the same thing will likely occur."
                )
                await ctx.reply(embed=embed)
                return
            else:
                embed = u_interface.gen_embed(
                    title = f"Gold gem solver",
                    description = "Impossible restraints.\nThe solver does not think a solution is possible given the restraints.\nIf you're setting the amount of an item to end up with (like `gold_gem=25`), that is likely the problem."
                )
                await ctx.reply(embed=embed)
                return

        command_list, post_alchemy, solver_result = full_result

        try:
            ascension_multiplier = 1 + (0.1 * stats.get("prestige_level", 0))
        except AttributeError:
            ascension_multiplier = 1
        
        embed = u_interface.gen_embed(
            title = "Gold gem solver",
            description = "{}{}\nYou should be able to make **{}**.\nDough gain: {} ({} with [Gold Ring](<https://bread.miraheze.org/wiki/Gold_Ring>).)".format(
                "(Using stored data, use `%bread data` for more info.)\n" if using_stored else "",
                "\n".join([
                    f"{gem}: {u_text.smart_number(gems[gem])} -> {u_text.smart_number(post_alchemy[gem])}"
                    for gem in gems
                    if gems[gem] != post_alchemy[gem] # Kinda useless, but whatever.
                ]),
                u_text.smart_text(solver_result["gem_gold_total"], "gold gem"),
                u_text.smart_number(round(solver_result["gem_gold_total"] * 5000 * ascension_multiplier)),
                u_text.smart_number(round(solver_result["gem_gold_total"] * 10000 * ascension_multiplier))
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
        "%bread tron quick",
        "%bread tron max",
        "%bread tron_value",
        "%bread gem_value",
        "%bread gold_gem",
        "%bread omega",
        "%bread solver",
    ]
    
    @bread.group(
        name = "data",
        brief = "Store data for use in other commands.",
        description = "Store data for use in other commands.\n\nThe following commands use this feature:\n{}".format("\n".join([f"- {item}" for item in bread_data_usage])),
        invoke_without_command = True,
        pass_context = True
    )
    async def bread_data(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        if ctx.invoked_subcommand is not None:
            return
        
        stored = u_bread.get_stored_data(
            database = database,
            user_id = ctx.author.id
        )

        stored_message = "You have stored data!" if stored.loaded else "You do not have any stored data."

        embed = u_interface.gen_embed(
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
    async def bread_data_store(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        replied_to = u_interface.replying_mm_checks(ctx.message, require_reply=False, return_replied_to=True)

        if not replied_to:
            await ctx.reply("You must reply to a stats message.")
            return
        
        parsed = await u_bread.parse_stats(replied_to)

        if not parsed["parse_successful"]:
            await ctx.reply("You must reply to a stats message.")
            return
        
        existing = u_bread.get_stored_data(
            database = database,
            user_id = ctx.author.id
        )

        if parsed["stats_type"] == "dump":
            existing.clear_stored_data(database = database)

        existing.update_from_dict(
            parsed["stats"]
        )

        existing.update_stored_data(
            database = database
        )

        if parsed["stats_type"] != "dump":
            guide = "Just a note, it's better to use `$bread export` for this due to it having all the stats in a single message.\n"
        else:
            guide = ""

        embed = u_interface.gen_embed(
            title = "Stored data",
            description = f"Data stored!\n{guide}\nUse `%bread data inventory` to view the current stored data.\nUse `%bread data clear` to clear the stored data.\n\nTo get a list of all the commands that use the stored data feature, use `%help bread data`."
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
    async def bread_data_inventory(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            page: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The page of the inventory to view.")
        ):
        if page is None:
            page = 1

        page = max(page - 1, 0)

        stored = u_bread.get_stored_data(
            database = database,
            user_id = ctx.author.id
        )

        if not stored.loaded:
            await ctx.reply("You do not have any stored data.\nUse `%bread data` to get more information on how to store data.")
            return
        
        PAGE_SIZE = 20 # How many items to show on each page.

        data_keys = list(stored.data.keys())
        max_page = math.ceil(len(data_keys) / PAGE_SIZE)

        page = min(page, max_page - 1)

        start = page * PAGE_SIZE
        end = min((page + 1) * PAGE_SIZE, len(data_keys))

        keys_show = data_keys[start:end]

        lines = []

        for key in keys_show:
            value = stored.get(key)
            if isinstance(value, dict):
                lines.append("{}: {}".format(
                    key,
                    ", ".join([u_values.get_item(item).internal_emoji for item in value.keys()])
                ))
                continue
            
            if isinstance(value, int):
                value = u_text.smart_number(value)
                
            lines.append(f"{key}: {value}")
        
        embed = u_interface.gen_embed(
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
        aliases = ["clean"],
        brief = "Clears your current stored data.",
        description = "Clears your current stored data.\n\nTo get a list of all the command that use the stored data feature, use '%help bread data'"
    )
    async def bread_data_clear(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        existing = u_bread.get_stored_data(
            database = database,
            user_id = ctx.author.id
        )

        existing.clear_stored_data(
            database = database
        )
        
        embed = u_interface.gen_embed(
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
    async def bread_chessatron(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
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
        description = "The chessatron solver.\nThis does require storing data with the `%bread data` feature.\n\nModifier list:\n- '-gems' will include gems in the solving.\n- `[item name]>[amount]` will tell the solver to leave you with the amount or more of that item.\n- `[item name]=[amount]` will tell the solver to leave you with the exactly that amount of that item."
    )
    async def bread_chessatron_solve(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            *, modifiers: typing.Optional[str] = commands.parameter(description = "Optional modifiers, see above for modifier list.")
        ):
        stored_data = u_bread.get_stored_data(
            database = database,
            user_id = ctx.author.id
        )

        if not stored_data.loaded:
            await ctx.reply("You do not have any stored data.\nUse `%bread data` to get more information on how to store data.")
            return

        ################

        if modifiers is None:
            modifiers = ""

        modifier_list = modifiers.split(" ")

        ################

        disabled_items = []
        minimum_items = {}
        equal_items = {}
        
        items = {}

        attributes = [u_values.all_chess_pieces, u_values.all_rares, u_values.all_specials]
        for attribute in attributes:
            for item in attribute:
                items[item] = stored_data.get(item, 0)

        items[u_values.bread] = stored_data.get(u_values.bread, 0) # Bread has no attributes we can search for :(
        
        for modifier in modifier_list:
            if modifier == "-gems":
                for gem in u_values.all_shiny:
                    items[gem] = stored_data.get(gem, 0)
            
            if modifier.startswith("!"):
                item_name = modifier.replace("!", "", 1)
                get_item = u_values.get_item(item_name)
                if get_item:
                    disabled_items.append(get_item)

            if modifier.count(">") == 1:
                potential_item, potential_amount = modifier.split(">")

                potential_item = u_values.get_item(potential_item)

                if potential_item is None:
                    continue

                try:
                    potential_amount = u_converters.parse_int(potential_amount)
                except ValueError:
                    continue

                minimum_items[potential_item] = potential_amount

            if modifier.count("=") == 1:
                potential_item, potential_amount = modifier.split("=")

                potential_item = u_values.get_item(potential_item)

                if potential_item is None:
                    continue

                try:
                    potential_amount = u_converters.parse_int(potential_amount)
                except ValueError:
                    continue

                equal_items[potential_item] = potential_amount

        
        items[u_values.chessatron] = stored_data.get(u_values.chessatron, 0)

        # Run the solver.
        try:
            await ctx.message.add_reaction("✅")
        except:
            pass
        
        full_result = u_solvers.solver_wrapper(
            items = items,
            maximize = u_values.chessatron,
            disabled_recipes = stored_data.disallowed_recipes,
            disabled_items = disabled_items,
            minimum_items = minimum_items,
            equal_items = equal_items
        )

        if not full_result:
            if full_result is None:
                embed = u_interface.gen_embed(
                    title = "Chessatron solver",
                    description = "Timeout reached.\nThe solver took too long to run and was stopped before it found a solution. Please do not try again, as the same thing will likely occur."
                )
                await ctx.reply(embed=embed)
                return
            else:
                embed = u_interface.gen_embed(
                    title = f"Chessatron solver",
                    description = "Impossible restraints.\nThe solver does not think a solution is possible given the restraints.\nIf you're setting the amount of an item to end up with (like `chessatron=25`), that is likely the problem."
                )
                await ctx.reply(embed=embed)
                return

        command_list, post_alchemy, solver_result = full_result

        if stored_data.get("auto_chessatron", False) and len(command_list) > 1: # If the length is 0 no trons are possible, and 1 is trons are possible but don't need chess piece alchemy.
            command_list.insert(0, "$bread auto_chessatron off")

        ################
        
        embed = u_interface.gen_embed(
            title = "Chessatron solver",
            description = "{}\nYou should be able to make **{}** {} with an estimated gain of **{} dough**.".format(
                "\n".join([
                    f"{item}: {u_text.smart_number(items[item])} -> {u_text.smart_number(post_alchemy[item])}"
                    for item in items
                    if items[item] != post_alchemy[item]
                ]),
                u_text.smart_number(solver_result["chessatron_total"]),
                u_values.chessatron,
                u_text.smart_number(round(solver_result["chessatron_total"] * stored_data.tron_value))
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
    async def bread_chessatron_quick(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        stored_data = u_bread.get_stored_data(
            database = database,
            user_id = ctx.author.id
        )

        if not stored_data.loaded:
            await ctx.reply("You do not have any stored data.\nUse `%bread data` to get more information on how to store data.")
            return
        
        bpawn = stored_data.get(u_values.bpawn, 0)
        wpawn = stored_data.get(u_values.wpawn, 0)

        initial_subtaction = bpawn - wpawn
        first_division = initial_subtaction / 3
        addition = first_division + wpawn
        final_division = addition / 8

        tron_value = stored_data.tron_value

        embed = u_interface.gen_embed(
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
    async def bread_chessatron_value(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            user: typing.Optional[discord.Member] = commands.parameter(description = "The person to gift the dough to."),
            tron_value: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of dough you get per tron."),
            percentage: typing.Optional[u_converters.parse_percent] = commands.parameter(description = "What percentage of the tron dough to gift."),
            stonk: typing.Optional[u_values.StonkConverter] = commands.parameter(description = "The stonk to use, will use whatever is closest if nothing is given.") # type: ignore
        ):
        stored = u_bread.get_stored_data(
            database = database,
            user_id = ctx.author.id
        )

        if not stored.loaded:
            await ctx.reply("You do not have any stored data.\nUse `%bread data` to get more information on how to store data.")
            return
        
        if user is None:
            await ctx.reply("You must provide a person to gift the stonks to.")
            return
        
        if tron_value is None:
            tron_value = stored.tron_value
        
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
        gem_contribution_final = gem_contribution_initial / 64

        total_trons = int(pawn_contribution_final + gem_contribution_final)
        total_dough = round(total_trons * tron_value)
        after_percentage = round(total_dough * percentage)

        if stonk is None:
            stonk = u_stonks.closest_to_dough(dough_amount=after_percentage, database=database)
        
        gift_amount, remaining = divmod(after_percentage, stonk.value(database = database))

        sm = u_text.smart_number
        
        embed = u_interface.gen_embed(
            title = "Chessatron value estimation",
            description = f"{u_values.bpawn}: {sm(bpawns)}, {u_values.wpawn}: {sm(wpawns)}\n{', '.join([f'{gem}: {sm(gems[gem])}' for gem in u_values.all_shiny])}",
            fields = [
                ("", f"Trons from pieces: {sm(round(pawn_contribution_final, 2))}\nTrons from gem chessatron: {sm(round(gem_contribution_final, 2))}\nTotal chessatrons: **{u_text.smart_text(total_trons, 'chessatron')}**, which, at a rate of {sm(tron_value)} per chessatron, is worth **{sm(total_dough)} dough**.\n\nWith a percentage of {percentage * 100}%, it results in **{sm(after_percentage)} dough**.\n\nGifting {sm(gift_amount)} {stonk} results in {sm(remaining)} remaining dough.", False),
                ("Equation:", f"- {sm(bpawns)} + {sm(wpawns)} = {sm(pawn_contribution_initial)}\n- {sm(pawn_contribution_initial)} / 16 = {sm(pawn_contribution_final)}\n\n- {sm(gem_contribution_initial)} (Sum of gems in red gems.)\n- {sm(gem_contribution_initial)} / 64 = {sm(gem_contribution_final)}\n\n- {sm(pawn_contribution_final)} + {sm(gem_contribution_final)} = {sm(total_trons)}\n- {sm(tron_value)} * {sm(total_trons)} = {sm(total_dough)}\n\n- {percentage * 100}% * {sm(total_dough)} = {sm(after_percentage)}", True),
                ("Commands:", f"$bread gift {user.id} {gift_amount} {stonk}", True)
            ],
            footer_text = "On mobile you can tap and hold on the commands section to copy it."
        )

        await ctx.reply(embed=embed)

    

        
    ######################################################################################################################################################
    ##### BREAD CHESSATRON MAX ###########################################################################################################################
    ######################################################################################################################################################
    
    @bread_chessatron.command(
        name = "max",
        brief = "Calculates the maximum possible amount of trons.",
        description = "Calculates the maximum possible amount of trons using only recipe 1 (and 2 for pawns). This does also work for anarchy trons as well as regular trons.\n\nThis is using the data stored with the `%bread data` feature."
    )
    async def bread_chessatron_max(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        replied = u_interface.replying_mm_checks(
            message = ctx.message,
            require_reply = False,
            return_replied_to = True
        )

        async def parse_attempt() -> bool:
            if not replied:
                return False
            
            parse = await u_bread.parse_stats(replied)

            if not parse.get("parse_successful"):
                return False
            
            if not (parse.get("stats_type") == "chess" or parse.get("stats_type") == "dump"):
                return False

            return parse
        
        parsed = await parse_attempt()

        if not parsed:
            using_stored = True
            stats = u_bread.get_stored_data(
                database = database,
                user_id = ctx.author.id
            )
            if not stats.loaded:
                await ctx.reply("Please reply to a message that contains your chess stats or use stored data.\nUse `%bread data` to get more information on how to store data.")
                return
        else:
            using_stored = False
            stats = parsed.get("stats", {})
        
        regular_pieces = {
            piece: stats.get(piece, 0)
            for piece in u_values.all_chess_pieces
        }
        anarchy_pieces = {
            piece: stats.get(piece, 0)
            for piece in u_values.all_anarchy_pieces
        }

        regular_kings = (regular_pieces[u_values.bking] + regular_pieces[u_values.wking]) / 2
        regular_queens = (regular_pieces[u_values.bqueen] + regular_pieces[u_values.wqueen]) / 2
        regular_rooks = (regular_pieces[u_values.brook] + regular_pieces[u_values.wrook]) / 4
        regular_bishops = (regular_pieces[u_values.bbishop] + regular_pieces[u_values.wbishop]) / 4
        regular_knights = (regular_pieces[u_values.bknight] + regular_pieces[u_values.wknight]) / 4
        regular_pawns = ((regular_pieces[u_values.bpawn] - regular_pieces[u_values.wpawn]) / 3 + regular_pieces[u_values.wpawn]) / 8

        anarchy_kings = (anarchy_pieces[u_values.bking_anarchy] + anarchy_pieces[u_values.wking_anarchy]) / 2
        anarchy_queens = (anarchy_pieces[u_values.bqueen_anarchy] + anarchy_pieces[u_values.wqueen_anarchy]) / 2
        anarchy_rooks = (anarchy_pieces[u_values.brook_anarchy] + anarchy_pieces[u_values.wrook_anarchy]) / 4
        anarchy_bishops = (anarchy_pieces[u_values.bbishop_anarchy] + anarchy_pieces[u_values.wbishop_anarchy]) / 4
        anarchy_knights = (anarchy_pieces[u_values.bknight_anarchy] + anarchy_pieces[u_values.wknight_anarchy]) / 4
        anarchy_pawns = ((anarchy_pieces[u_values.bpawn_anarchy] - anarchy_pieces[u_values.wpawn_anarchy]) / 3 + anarchy_pieces[u_values.wpawn_anarchy]) / 8

        maximum_regular = int(min(regular_kings, regular_queens, regular_rooks, regular_bishops, regular_knights, regular_pawns))
        maximum_anarchy = int(min(anarchy_kings, anarchy_queens, anarchy_rooks, anarchy_bishops, anarchy_knights, anarchy_pawns))

        embed = u_interface.gen_embed(
            title = "Maximum Chessatrons",
            description = ("(Using stored data, use `%bread data` for more info.)\n\n" if using_stored else "") + "Maximum amount of Chessatrons and Anarchy Chessatrons possible using only recipe 1 (and 2 for pawns):",
            fields = [
                (
                    "Regular Chessatrons:",
                    f"- Kings: {u_text.smart_number(round(regular_kings, 2))}\n- Queens: {u_text.smart_number(round(regular_queens, 2))}\n- Rooks: {u_text.smart_number(round(regular_rooks, 2))}\n- Bishops: {u_text.smart_number(round(regular_bishops, 2))}\n- Knights: {u_text.smart_number(round(regular_knights, 2))}\n- Pawns: {u_text.smart_number(round(regular_pawns, 2))}\nMaximum amount of regular chessatrons: **{u_text.smart_number(maximum_regular)}**",
                    True
                ),
                (
                    "Anarchy Chessatrons:",
                    f"- Kings: {u_text.smart_number(round(anarchy_kings, 2))}\n- Queens: {u_text.smart_number(round(anarchy_queens, 2))}\n- Rooks: {u_text.smart_number(round(anarchy_rooks, 2))}\n- Bishops: {u_text.smart_number(round(anarchy_bishops, 2))}\n- Knights: {u_text.smart_number(round(anarchy_knights, 2))}\n- Pawns: {u_text.smart_number(round(anarchy_pawns, 2))}\nMaximum amount of anarchy chessatrons: **{u_text.smart_number(maximum_anarchy)}**",
                    True
                )
            ]
        )

        await ctx.reply(embed=embed)



    
 
        
    ######################################################################################################################################################
    ##### BREAD OMEGA ####################################################################################################################################
    ######################################################################################################################################################
    
    @bread.command(
        name = "omega",
        aliases = ["omega_chessatron"],
        brief = "Solver for the creation of Omegas.",
        description = "Solver for the creation of Omegas.\nThis does require storing data with the `%bread data` feature.\n\nModifier list:\n- `-tron`: Allows the solver to make chessatrons out of gems to increase the number of Omegas created.\n- `-chess`: The same as `-tron`, but it will allow for the use of gems and chess pieces to increase the number of Omegas made.\n- `[item name]>[amount]` will tell the solver to leave you with the amount or more of that item.\n- `[item name]=[amount]` will tell the solver to leave you with that exact amount of that item."
    )
    async def bread_omega(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            *, modifiers: typing.Optional[str] = commands.parameter(description = "Optional modifiers. See above for modifier list.")
        ):
        stored_data = u_bread.get_stored_data(
            database = database,
            user_id = ctx.author.id
        )

        if not stored_data.loaded:
            await ctx.reply("You do not have any stored data.\nUse `%bread data` to get more information on how to store data.")
            return

        ################
        # Get modifier list.

        if modifiers is None:
            modifiers = ""

        modifier_list = modifiers.split(" ")

        ################
        # Setup the item list.
        
        items = {}
        disabled_items = []
        minimum_items = {}
        equal_items = {}

        attributes = [u_values.all_shiny]

        if "-chess" in modifier_list:
            attributes.append(u_values.all_chess_pieces)
            attributes.append(u_values.all_rares)
            attributes.append(u_values.all_specials)
            items[u_values.bread] = stored_data.get(u_values.bread, 0)
            
            if "-tron" not in modifier_list:
                modifier_list.append("-tron")
        
        for modifier in modifier_list:
            if modifier.startswith("!"):
                item_name = modifier.replace("!", "", 1)
                get_item = u_values.get_item(item_name)
                if get_item:
                    disabled_items.append(get_item)
            if modifier.count(">") == 1:
                potential_item, potential_amount = modifier.split(">")

                potential_item = u_values.get_item(potential_item)

                if potential_item is None:
                    continue

                try:
                    potential_amount = u_converters.parse_int(potential_amount)
                except ValueError:
                    continue

                minimum_items[potential_item] = potential_amount
            if modifier.count("=") == 1:
                potential_item, potential_amount = modifier.split("=")

                potential_item = u_values.get_item(potential_item)

                if potential_item is None:
                    continue

                try:
                    potential_amount = u_converters.parse_int(potential_amount)
                except ValueError:
                    continue

                equal_items[potential_item] = potential_amount


        for attribute in attributes:
            for item in attribute:
                items[item] = stored_data.get(item, 0)

        items[u_values.anarchy_chess] = stored_data.get(u_values.anarchy_chess, 0)
        items[u_values.chessatron] = stored_data.get(u_values.chessatron, 0)
        items[u_values.omega_chessatron] = stored_data.get(u_values.omega_chessatron, 0)

        ################
        # Determine disabled recipes.

        disabled_recipes = []

        if "-tron" not in modifier_list:
            disabled_recipes.append("chessatron_recipe_1")
            disabled_recipes.append("chessatron_recipe_2")
        
        disabled_recipes.extend(stored_data.disallowed_recipes)

        ################
        # Run the solver.
        
        embed = await u_solvers.solver_embed(
            ctx = ctx,
            inventory = items,
            goal_item = u_values.omega_chessatron,
            disabled_recipes = disabled_recipes,
            disabled_items = disabled_items,
            minimum_items = minimum_items,
            equal_items = equal_items
        )

        await ctx.reply(embed=embed)

    

        
    ######################################################################################################################################################
    ##### BREAD SOLVER ###################################################################################################################################
    ######################################################################################################################################################
    
    @bread.command(
        name = "solver",
        aliases = ["solve", "universal_solver"],
        brief = "Universal solver to maximize an item.",
        description = "Universal solver to maximize an item.\nThis does require storing data with the `%bread data` feature.\n\nModifiers:\n- `!<item>_recipe_<recipe number>` can be used to disallow the solver from using that particular recipe. Internally chessatrons are stored as alchemy recipes, so recipe 1 is from chess pieces and recipe 2 is from 64 red gems.\n- `[item name]>[amount]` will tell the solver to leave you with the amount or more of that item.\n- `[item name]=[amount]` will tell the solver to leave you with exactly that of that item."
    )
    async def bread_solver(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            goal_item: typing.Optional[u_values.ItemConverter] = commands.parameter(description = "What item to try and maximize."),
            *, modifiers: typing.Optional[str] = commands.parameter(description = "Optional modifiers.")
        ):
        if goal_item is None:
            await ctx.reply("Please provide the item to maximize.")
            return
        
        ################
        # Get stored data.

        stored_data = u_bread.get_stored_data(
            database = database,
            user_id = ctx.author.id
        )

        if not stored_data.loaded:
            await ctx.reply("You do not have any stored data.\nUse `%bread data` to get more information on how to store data.")
            return

        ################
        # Get modifier list.

        if modifiers is None:
            modifiers = ""

        modifier_list = modifiers.split(" ")

        ################
        # Setup the item list.
        
        items = {}
        disabled_items = []
        minimum_items = {}
        equal_items = {}

        for item in u_values.all_items:
            items[item] = stored_data.get(item, 0)
        
        for modifier in modifier_list:
            if modifier.startswith("!"):
                item_name = modifier.replace("!", "", 1)
                get_item = u_values.get_item(item_name)
                if get_item:
                    disabled_items.append(get_item)

        ################
        # Determine disabled recipes.

        disabled_recipes = []
        pattern = re.compile("^!(.+)_recipe_(\d+)$")

        for modifier in modifier_list:
            if modifier.count(">") == 1:
                potential_item, potential_amount = modifier.split(">")

                potential_item = u_values.get_item(potential_item)

                if potential_item is None:
                    continue

                try:
                    potential_amount = u_converters.parse_int(potential_amount)
                except ValueError:
                    continue

                minimum_items[potential_item] = potential_amount
            if modifier.count("=") == 1:
                potential_item, potential_amount = modifier.split("=")

                potential_item = u_values.get_item(potential_item)

                if potential_item is None:
                    continue

                try:
                    potential_amount = u_converters.parse_int(potential_amount)
                except ValueError:
                    continue

                equal_items[potential_item] = potential_amount

            if not modifier.startswith("!"):
                continue
            
            found = pattern.match(modifier)

            if not found:
                continue

            disabled_recipes.append(f"{found.group(1)}_recipe_{found.group(2)}")
        
        disabled_recipes.extend(stored_data.disallowed_recipes)

        ################
        # Run the solver.
        
        embed = await u_solvers.solver_embed(
            ctx = ctx,
            inventory = items,
            goal_item = goal_item,
            disabled_recipes = disabled_recipes,
            disabled_items = disabled_items,
            minimum_items = minimum_items,
            equal_items = equal_items
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
    async def bread_probability(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
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
        
        if successes < 0:
            await ctx.reply("The number of successes must be greater than or equal to  0.")
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

        embed = u_interface.gen_embed(
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

    

        


    ######################################################################################################################################################
    ##### BREAD DAY ######################################################################################################################################
    ######################################################################################################################################################
    
    @bread.group(
        name = "day",
        aliases = ["today"],
        brief = "Get the current day's stats.",
        description = "Get the current day's stats.",
        invoke_without_command = True,
        pass_context = True
    )
    async def bread_day(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            day: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The day to get the stats for. Defaults to today.")
        ):
        if ctx.invoked_subcommand is not None:
            return
        
        highest_accepted = u_bingo.live(database).get("daily_board_id")
        if day is None or min(day, highest_accepted) == highest_accepted:
            day = highest_accepted
            stats = database.load("bread", "day_stats", default={})
        else:
            # If it's a day in history.
            history = u_files.load("data", "bread", "day_stats.json", default={}, join_file_path=True)

            if len(history.keys()) == 0:
                stats = database.load("bread", "day_stats", default={})
            else:
                lowest_accepted = int(min(history.keys()))

                day = max(day, lowest_accepted)
                stats = history[str(day)]        
        
        embed = u_interface.gen_embed(
            title = "Day stats",
            description = "Day {day_id}'s stats:\n{stats}".format(
                day_id = day,
                stats = "\n".join([f"- **{key}**: {u_text.smart_number(value)}" for key, value in stats.items()])
            ),
            fields = [
                ("", "If you don't see a stat here that means it hasn't occurred today.\n\nYou can get other days via '%bread day <day id>'\nYou can get a graph of a stat via '%bread day graph <stat name>'", False)
            ]
        )
        await ctx.reply(embed=embed)

    

        


    ######################################################################################################################################################
    ##### BREAD DAY GRAPH ################################################################################################################################
    ######################################################################################################################################################
    
    @bread_day.command(
        name = "graph",
        brief = "Get a graph of a stat.",
        description = "Get a graph of a stat.\n\nList of other stats:\n- '-start <day>': Sets the start day of the graph.\n- '-end <day>': Sets the end day of the graph.\n- '-log': Changes the Y axis to be a logarithmic scale."
    )
    async def bread_day_graph(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            stat_name: typing.Optional[str] = commands.parameter(description = "The name of the stat to graph."),
            *, other_args: typing.Optional[str] = commands.parameter(description = "Other arguments.")
        ):
        current = database.load("bread", "day_stats", default={})
        history = u_files.load("data", "bread", "day_stats.json", default={}, join_file_path=True)

        # Get a version with all the data.
        modified = history.copy()
        modified[str(u_bingo.live(database)["daily_board_id"])] = current

        stat_list = list(current.keys())

        for day_stats in modified.values():
            for key in day_stats:
                if key not in stat_list:
                    stat_list.append(key)
        
        if stat_name not in stat_list:
            embed = u_interface.gen_embed(
                title = "Stat list",
                description = "You need to provide a stat name.\nHere's a list of stats:\n{stat_list}".format(stat_list = ", ".join(stat_list))
            )
            await ctx.reply(embed=embed)
            return
        
        if other_args is None:
            other_args = ""

        split_args = other_args.split(" ")

        log = "-log" in split_args

        start = int(min(modified))
        end = int(max(modified))

        for arg in split_args:
            try:
                if arg.startswith("-start"):
                    start = u_converters.parse_int(arg.split(" ")[1])
                elif arg.startswith("-end"):
                    end = u_converters.parse_int(arg.split(" ")[1])
            except ValueError:
                pass
        
        start = max(int(min(modified)), start)
        end = int(max(modified))

        if end <= start:
            await ctx.reply("The start must be before the end.")
            return
        
        data = []

        found = False
        for tick_id in range(start, end + 1):
            if modified.get(str(tick_id), {}).get(stat_name, None) is None and not found:
                continue

            found = True
            data.append(
                (
                    tick_id,
                    modified.get(str(tick_id), {}).get(stat_name, 0)
                )
            )

        graph = u_images.generate_graph(
            lines = [{"values": data}],
            x_label = "Day number",
            y_label = stat_name.replace("_", " ").title(),
            log_scale = log
        )

        await ctx.reply(file=discord.File(graph))

    

        


    ######################################################################################################################################################
    ##### BREAD LEADERBOARD PARSE ########################################################################################################################
    ######################################################################################################################################################
    
    @bread.command(
        name = "parse_leaderboard",
        aliases = ["parse_lb", "lb_parse", "leaderboard_parse"],
        brief = "Parses a leaderboard to provide percentages.",
        description = "Parses a leaderboard to provide percentages.\nThis requires replying to a leaderboard message."
    )
    async def bread_parse_leaderboard(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        replied = u_interface.replying_mm_checks(ctx.message, require_reply = False, return_replied_to = True)

        if not replied or not replied.content.startswith("Leaderboard for"):
            await ctx.reply("You must reply to a Machine-Mind leaderboard message.")
            return
        
        total = u_text.extract_number(
            r"The combined amount between all people is (-?[\d,]+)\.",
            replied.content,
            default = 0
        )

        lines = []

        previous_placement = 0

        for match in re.finditer(r"([\d,]+)\. (.+) (-?[\d,]+)(.*)", replied.content):
            placement = u_text.return_numeric(match.group(1))
            username = match.group(2)
            amount = u_converters.parse_int(match.group(3))
            bonus = match.group(4)

            if total == 0:
                percent = 0
            else:
                percent = round(amount / total * 100, 2)
            
            if abs(placement - previous_placement) >= 2:
                lines.append("")
            
            previous_placement = placement
            lines.append(
                f"{u_text.smart_number(placement)}. {username} {percent}%{bonus}"
            )
        
        embed = u_interface.gen_embed(
            title = "Parsed leaderboard",
            description = "Total: {total}\n\nPercent breakdown by person:\n{leaderboard}".format(
                total = u_text.smart_number(total),
                leaderboard = "\n".join(lines)
            )
        )

        await ctx.reply(embed=embed)

    

        


    ######################################################################################################################################################
    ##### BREAD PROJECT ##################################################################################################################################
    ######################################################################################################################################################
    
    @bread.group(
        name = "project",
        aliases = ["credits", "project_credits", "projects", "credit", "project_credit"],
        brief = "Project credit related calculations.",
        description = "Project credit related calculations.",
        invoke_without_command = True,
        pass_context = True
    )
    async def bread_project(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        if ctx.invoked_subcommand is not None:
            return
        
        await ctx.send_help(self.bread_project)

    

        


    ######################################################################################################################################################
    ##### BREAD PROJECT USE ##############################################################################################################################
    ######################################################################################################################################################
    
    @bread_project.command(
        name = "use",
        brief = "Calculates how much to contribute to use an amount of credits.",
        description = "Calculates how many items to contribute to a project in order to use a specific amount of credits."
    )
    async def bread_project_use(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            credit_amount: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of credits to use."),
            maximum_items: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The total amount of items in the project.")
        ):
        if credit_amount is None:
            await ctx.reply("Please provide the amount of credits to use.")
            return

        if not(0 <= credit_amount <= 1000):
            await ctx.reply("The credit amount must be between 0 and 1,000.")
            return
        
        credit_percent = credit_amount / 2000

        project_percentage = (credit_percent + math.sqrt(credit_percent ** 2 + 4 * credit_percent)) / 2

        suffix = ""
        if maximum_items is not None:
            suffix = f"\nFor a project that has {u_text.smart_text(maximum_items, 'total item')} that would end up being **{u_text.smart_text(math.ceil(maximum_items * project_percentage), 'item')}**."
            
        embed = u_interface.gen_embed(
            title = "Project credits",
            description = f"In order to use {u_text.smart_text(credit_amount, 'credit')} you would need to contribute **{round(project_percentage * 100, 2)}%** of a project's total items.{suffix}"
        )
        
        await ctx.reply(embed=embed)

    

        


    ######################################################################################################################################################
    ##### BREAD ROLL OLD #################################################################################################################################
    ######################################################################################################################################################
    
    @bread.command(
        brief="Tasty bread roll",
        help="It's bread.",
        name = "roll_old"
    )
    @commands.check(u_checks.hide_from_help)
    async def bread_roll_old(self, ctx):
        # make sure that the person isn't overloading with spam
        if (ctx.author.id in self.currently_interacting):
            print("in process of rolling, rejecting")
            return
        #add them to the list, we'll remove them at the end
        self.currently_interacting.append(ctx.author.id)

        
        

        # no more breasic britch
        special_value = 0
        special_stat = None

        count = 1
        commentary = ""
        emoji = ":bread:"
        if random.randint(0,8191) == 0:
            emoji = random.choice(u_values.one_of_a_kinds).internal_emoji
            special_value = 2000
            
            
            print("Wow. "+emoji)
            commentary = "Wow."
            special_stat = "unique_token"
        elif random.randint(0,4095) == 0:
            print("Mega chance! CRAZY SHIT")
            for i in range(10):
                output = ""
                for i in range(1,90):
                    #special_value += 1
                    output += random.choice(u_values.all_breads).internal_emoji + " "
                    if (random.randint(0,5) == 0):
                        output += "\n"
                await ctx.reply(output)
            await ctx.reply("Error. Error. Error. Error. Error. Error.")
            special_stat = "lottery_win"
            special_value = 1000
            #self.json_interface.increase_value_in_file(ctx.author,"total_dough",count)
            #return
        elif random.randint(0,2047) == 0:
            print("Super rare chance! 12 breads")
            count = 12
            commentary = "Error. Number of breads (12) detected to be inconceivable. System overloaded."
            special_stat = "twelve_breads"
        elif random.randint(0,1023) == 0:
            print("Rare chance! 11 breads")
            count = 11
            commentary = "NANI?? ELEVEN BOREADOS??"
            special_stat = "eleven_breads"
        elif random.randint(0,512) == 0:
            if random.randint(0,3) == 0:
                emoji = random.choice(u_values.white_chess_pieces).internal_emoji
                special_value = 80
            else:
                emoji = random.choice(u_values.black_chess_pieces).internal_emoji
                special_value = 40
            print("Rare chance! Chess piece "+emoji)
            commentary = "You have now increased your elo by 10 points."
            special_stat = "chess_pieces"
        elif random.randint(0,128) == 0:
            print("Uncommon chance. Rare Bread.")
            emoji = random.choice(u_values.all_rares).internal_emoji
            commentary = "Tasty."
            special_value = 10
            special_stat = "special_bread"
        else:
            count = random.randint(1,10)
            if count == 10:
                commentary = "Congratulations! You found all 10 loaves!"
                special_stat = "ten_breads"
            elif count == 1:
                chance = random.randint(1,3)
                commentary = "Better luck next time."
                special_stat = "natural_1"
                #print ("1 bread. Random rolling for a 1, got "+str(chance))
                if chance == 1:
                    emoji = random.choice(u_values.all_breads).internal_emoji
                    if emoji != ":bread:":
                        commentary = "Interesting."
                        special_stat = "special_bread"
                        special_value = 5

        record = False

        print("dispensing "+str(count)+" bread for "+str(ctx.message.author)+" in "+str(ctx.message.channel))
        output = ""

        if special_value == 0: #if it's not a special case we do our usual
            for i in range(count) :
                output += emoji
        else: #just output once 
            output += emoji
        await ctx.reply(output)

        if commentary != "":
            await ctx.reply(commentary)
        
        # now we remove them from the list of rollers, this allows them to roll again without spamming
        self.currently_interacting.remove(ctx.author.id)

    

        


    ######################################################################################################################################################
    ##### BREAD LAB ######################################################################################################################################
    ######################################################################################################################################################
    
    @bread.group(
        name = "lab",
        brief = "Universal experimental projects for the entire Bingo-Bot.",
        description = """# The lab.                  

Universal experimental projects for the entire Bingo-Bot.
If you have any questions or ideas ping Duck.""",
        invoke_without_command = True,
        pass_context = True
    )
    async def bread_lab(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        if ctx.invoked_subcommand is not None:
            return
        
        await ctx.send_help(self.bread_lab)

    

        


    ######################################################################################################################################################
    ##### BREAD LAB ODDS #################################################################################################################################
    ######################################################################################################################################################
    
    @bread_lab.command(
        name = "odds",
        brief = "Calculates rolling odds for a space planet.",
        description = """Calculates rolling odds for a space planet.

Arguments:
- `priority:<item>`: The priority item.
- `raw_deviation:<float>`: The raw planet deviation.
- `deviation:<float>`: The calculated effective planet deviation. `raw_deviation`, `nebula`, and `black_hole` are not needed if this is provided.
- `nebula:<boolean>`: Whether the planet is in a nebula.
- `black_hole:<boolean>`: Whether the planet is in a black hole system.
- `tile_seed:<string>`: The tile seed.
- `day_seed:<string>`: The day seed. If this is provided it will calculate just that day's odds, but if it isn't then a trial of 10,000 days will be calculated.

If any of these are missing it'll generate them randomly, except for the priority item, that one is required."""
    )
    @commands.check(u_checks.sub_admin_check)
    async def bread_lab_odds(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            *, arguments: typing.Optional[str] = commands.parameter(description = "Arguments to use. See above for info.")
        ):
        if arguments is None:
            arguments = ""

        priority = None
        raw_deviation = None
        deviation = None
        nebula = None
        black_hole = None
        tile_seed = None
        day_seed = None

        for arg in arguments.split(" "):
            if arg.count(":") != 1:
                continue

            key, value = arg.split(":")

            try:
                if key == "priority":
                    priority = u_values.get_item(value)
                elif key == "raw_deviation":
                    raw_deviation = u_converters.parse_float(value)
                elif key == "deviation":
                    deviation = u_converters.parse_float(value)
                elif key == "nebula":
                    nebula = u_converters.extended_bool(value)
                elif key == "black_hole":
                    black_hole = u_converters.extended_bool(value)
                elif key == "tile_seed":
                    tile_seed = value
                elif key == "day_seed":
                    day_seed = value
            except (commands.BadArgument, ValueError):
                continue
        
        priority_types = {
            "bread": [u_values.bread],
            "special_bread": u_values.all_specials,
            "rare_bread": u_values.all_rares,
            "chess_piece": u_values.all_chess_pieces,
            "gem_red": [u_values.gem_red],
            "gem_blue": [u_values.gem_blue],
            "gem_purple": [u_values.gem_purple],
            "gem_green": [u_values.gem_green],
            "gem_gold": [u_values.gem_gold],
            "anarchy_chess": [u_values.anarchy_chess],
            "anarchy_piece": u_values.all_anarchy_pieces
        }

        for key, values in priority_types.items():
            if priority in values:
                priority = key
                break
        else:
            await ctx.reply("Unrecognized priority item, please include an item that can be found as a planet type.")
            return
        
        ##############################

        if raw_deviation is None:
            raw_deviation = random.normalvariate(
                mu = 1,
                sigma = 0.1
            )
        
        if nebula is None:
            nebula = random.randint(1, 2) == 1

        if black_hole is None:
            black_hole = random.randint(1, 2) == 1

        if tile_seed is None:
            tile_seed = "{:064x}".format(random.randrange(16 ** 64))

        ##############################
        
        # await ctx.reply(f"{priority} {raw_deviation} {deviation} {nebula} {black_hole} {tile_seed} {day_seed}")

        if day_seed is not None:
            result = u_bread.calculate_rolling_odds(
                priority = priority,
                tile_seed = tile_seed,
                day_seed = day_seed,
                planet_deviation = raw_deviation,
                in_nebula = nebula,
                black_hole = black_hole,
                effective_deviation = deviation
            ).get("odds")

            embed = u_interface.gen_embed(
                title = "Planet rolling odds",
                description = f"Parameters:\n- Priority: {priority}\n- Tile seed: {tile_seed}\n- Day seed: {day_seed}\n- Raw deviation: {raw_deviation}\n- Nebula: {nebula}\n- Black hole: {black_hole}\n- Effective deviation: {deviation}",
                fields = [
                    (
                        "Odds:",
                        "\n".join([f"- {priority_types[item][0]}: {value}" for item, value in result.items()]),
                        False
                    )
                ]
            )

            await ctx.reply(embed=embed)
            return
        
        data = []

        message = await ctx.reply("Generating data...\n0/100,000")

        amount = 100_000

        tenth = amount // 10

        start = time.time()
        for i in range(1, amount + 1):
            if i % tenth == 0:
                current = time.time()

                await message.edit(content=f"Generating data...\n{u_text.smart_number(i)}/100,000\nElapsed time: {u_text.smart_text(round(current - start, 3), 'second')}. Estimated time remaining: {u_text.smart_text(round(((current - start) / i) * (amount - i), 3), 'second')}.")

            day_seed = "{:064x}".format(random.randrange(16 ** 64))

            output = u_bread.calculate_rolling_odds(
                priority = priority,
                tile_seed = tile_seed,
                day_seed = day_seed,
                planet_deviation = raw_deviation,
                in_nebula = nebula,
                black_hole = black_hole,
                effective_deviation = deviation
            )

            if deviation is None:
                deviation = output.get("deviation")

            data.append(output.get("odds"))
        
        item_types = ["special_bread", "rare_bread", "chess_piece", "gem_red", "gem_blue", "gem_purple", "gem_green", "gem_gold", "anarchy_chess", "anarchy_piece"]

        first = {item: {} for item in item_types}

        for tick in data:
            for key, value in tick.items():
                mod = round(value, 4)
                if mod in first[key]:
                    first[key][mod] += 1
                else:
                    first[key][mod] = 1

        graph = u_images.generate_graph(
            lines = [{
                "label": key.replace("_", " ").title(),
                "values": list(dict(sorted(key_data.items())).items())
            } for key, key_data in first.items()],
            x_label = "Item odds",
            y_label = "Occurrence count"
        )

        embed = u_interface.gen_embed(
            title = "Planet rolling odds",
            description = f"Over a set of 100,000 days with the following parameters:\n- Priority: {priority}\n- Tile seed: {tile_seed}\n- Raw deviation: {raw_deviation}\n- Nebula: {nebula}\n- Black hole: {black_hole}\n- Effective deviation: {deviation}",
            image_link = "attachment://generated_graph.png",
            footer_text = f"Time to generate: {u_text.smart_text(round(current - start, 3), 'second')}"
        )

        await ctx.reply(embed=embed, file=discord.File(graph))
        await message.delete()





async def setup(bot: commands.Bot):
    global database
    database = bot.database

    cog = Bread_cog()
    cog.bot = bot
    
    # Add attributes for sys.modules and globals() so the _reload_module() function in utility.custom can read it and get the module objects.
    cog.modules = sys.modules
    cog.globals = globals()
    
    await bot.add_cog(cog)
