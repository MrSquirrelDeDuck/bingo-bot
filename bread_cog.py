from discord.ext import commands
import discord
import typing
import datetime
import pytz
import copy
import math
import aiohttp
import traceback
import mediawiki
import re

import sys

import utility.files as u_files
import utility.converters as u_converters
import utility.text as u_text
import utility.interface as u_interface
import utility.checks as u_checks
import utility.bread as u_bread
import utility.values as u_values
import utility.custom as u_custom

class Bread_cog(u_custom.CustomCog, name="Bread"):
    # bread_wiki_object = mediawiki.MediaWiki(user_agent='pyMediaWiki-Bingo-Bot', url="https://bread.miraheze.org/w/api.php")
    bread_wiki_searching = False

    # This is a list of unix timestamps, such that if you use <t:time_keys[0]> it'll be the right time.
    time_keys = ["1648850700", "1648854300", "1648857900", "1648861500", "1648865100", "1648868700", "1648785900", "1648789500", "1648793100", "1648796700", "1648800300", "1648803900", "1648807500", "1648811100", "1648814700", "1648818300", "1648821900", "1648825500", "1648829100", "1648832700", "1648836300", "1648839900", "1648843500", "1648847100"]

    ######################################################################################################################################################
    ##### UTILITY FUNCTIONS ##############################################################################################################################
    ######################################################################################################################################################

    def _get_reminder_data(self: typing.Self) -> dict:
        """Returns the reminder data as loaded from data/reminders.json."""
        return u_files.load("data/reminders.json")
    
    def _save_reminder_data(self: typing.Self, data: dict) -> None:
        """Saves a dict to the reminder data file."""
        u_files.save("data/reminders.json", data)
    
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
            ctx = u_custom.CustomContext(ctx)
            await ctx.reply("I am sorry, but you have been disallowed from using reminders.\nIf you believe this was an error, please let the moderators know.")
            return False
        
        return True

    ######################################################################################################################################################
    ##### COMMANDS #######################################################################################################################################
    ######################################################################################################################################################

    @commands.group(
        name = "bread",
        description = "Header command for Bread Game related utility commands.",
        brief = "Header for Bread Game related commands.",
        invoke_without_command = True,
        pass_context = True
    )
    async def bread(self, ctx):
        ctx = u_custom.CustomContext(ctx)

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
        ctx = u_custom.CustomContext(ctx)

        await ctx.send_help(self.bread)

    
    
    
    
    
    
    @bread.command(
        name = "stonks",
        aliases = ["stonk"],
        description = "To use the Bingo-Bot's stonk commands, use '%stonks'.",
        brief = "To use the Bingo-Bot's stonk commands, use '%stonks'.",
        hidden = True
    )
    async def bread_stonks(self, ctx):
        ctx = u_custom.CustomContext(ctx)

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
        ctx = u_custom.CustomContext(ctx)

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
        ctx = u_custom.CustomContext(ctx)

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
        ctx = u_custom.CustomContext(ctx)

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
        ctx = u_custom.CustomContext(ctx)

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
        ctx = u_custom.CustomContext(ctx)

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
        ctx = u_custom.CustomContext(ctx)

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
        ctx = u_custom.CustomContext(ctx)

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
        ctx = u_custom.CustomContext(ctx)

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
        ctx = u_custom.CustomContext(ctx)

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
        ctx = u_custom.CustomContext(ctx)

        attempted_parse = u_bread.parse_attempt(ctx.message, require_reply=True)

        if attempted_parse:
            current, self_converting_yeast = attempted_parse["stats"]["loaf_converter"], attempted_parse["stats"]["loaf_converter_discount"]

            if dough is None:
                dough = attempted_parse["stats"]["total_dough"]

                for stonk in u_values.stonks:
                    if stonk not in attempted_parse["stats"]:
                        continue

                    dough += stonk.value * attempted_parse["stats"][stonk]
        
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

        print(purchasable_no_scy)

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
        ctx = u_custom.CustomContext(ctx)

        if ctx.invoked_subcommand is not None:
            return
        
        await ctx.send_help(self.bread_gamble)

    
    
    
    
    @bread_gamble.command(
        name = "initial",
        brief = "Get the initial board of a gamble.",
        description = "Get the initial board of a gamble."
    )
    async def bread_gamble_initial(self, ctx):
        ctx = u_custom.CustomContext(ctx)

        replied_to = u_interface.replying_mm_checks(ctx.message, require_reply = True, return_replied_to = True)

        if not replied_to:
            await ctx.reply("You must reply to a gamble message.")
            return
        
        gamble_messages = u_files.load("data/bread/gamble_messages.json")

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
        ctx = u_custom.CustomContext(ctx)

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
        ctx = u_custom.CustomContext(ctx)

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
        ctx = u_custom.CustomContext(ctx)

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
        ctx = u_custom.CustomContext(ctx)

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
        ctx = u_custom.CustomContext(ctx)

        if percent is None or value is None:
            await ctx.reply("You must provide the percentage to use and the value to use.\nSyntax: `%bread percent <percentage> <value>`.\nFor example, `%bread percent 75% 1,738,983`")
            return
        
        embed = u_interface.embed(
            title = "Percentage",
            description = "{}% of {} is **{}**".format(u_text.smart_number(percent * 100), u_text.smart_number(value), u_text.smart_number(round(value * percent, 2)))
        )
        await ctx.reply(embed=embed)

        
            

        
    ######################################################################################################################################################
    ##### BREAD STONK GIFT ###############################################################################################################################
    ######################################################################################################################################################
    
    @bread.command(
        name = "stonk_gift",
        brief = "Automates stonk gifting math.",
        description = "Figures out how much dough to invest in a stonk to get a specific amount of dough."
    )
    async def bread_stonk_gift(self, ctx,
            dough: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The amount of dough to use."),
            stonk: typing.Optional[u_values.StonkConverter] = commands.parameter(description = "The stonk to use. If nothing is provided it'll use whatever stonk is closest to the goal."),
            user: typing.Optional[discord.Member] = commands.parameter(description = "Optional user to generate a gift command for.")
        ):
        ctx = u_custom.CustomContext(ctx)

        if dough is None:
            await ctx.reply("You must provide the amount of dough to use.")
            return
        
        if stonk is None:
            distance = {stonk: dough % stonk.value for stonk in u_values.stonks}
            stonk = min(distance, key=distance.get)
        
        invest_amount = dough // stonk.value
        
        gift_command = ""

        if user is not None:
            gift_command = "\n$bread gift {} {} {}".format(user.id, u_text.smart_number(invest_amount), stonk.internal_emoji)
        
        embed = u_interface.embed(
            title = "Stonk gifting",
            description = "By investing in **{} {}** you would have {} dough remaining.".format(u_text.smart_number(invest_amount), stonk.internal_emoji, u_text.smart_number(dough - (invest_amount * stonk.value))),
            fields = [("Commands", "$bread invest {} {} {}".format(u_text.smart_number(invest_amount), stonk.internal_emoji, gift_command), True)],
            footer_text = "On mobile, you can tap and hold on the Commands section's text to copy it."
        )
        await ctx.reply(embed=embed)


async def setup(bot: commands.Bot):
    cog = Bread_cog()
    cog.bot = bot
    
    # Add attributes for sys.modules and globals() so the _reload_module() function in utility.custom can read it and get the module objects.
    cog.modules = sys.modules
    cog.globals = globals()
    
    await bot.add_cog(cog)