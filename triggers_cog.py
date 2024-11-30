"""This cog is for events like on_message along with the hourly and daily loops.
The PluralKit and Latent-Dreamer explanation commands are also here."""

from discord.ext import commands
from discord.ext import tasks
import discord
import datetime
import asyncio
import time
import traceback
import re
import random
import time
import typing
import pytz

# pip install aiohttp
import aiohttp

import sys

import utility.files as u_files
import utility.interface as u_interface
import utility.custom as u_custom
import utility.checks as u_checks
import utility.bread as u_bread
import utility.text as u_text
import utility.converters as u_converters
import utility.stonks as u_stonks
import utility.algorithms as u_algorithms
import utility.images as u_images
import utility.bingo as u_bingo
import utility.detection as u_detection
import utility.solvers as u_solvers
# import utility.rulette as u_rulette

# pip install python-dotenv
from dotenv import load_dotenv
from os import getenv

load_dotenv()
try:
    UPDATE_GIT = u_converters.extended_bool(getenv('UPDATE_GIT'))
except:
    print(traceback.format_exc())
    UPDATE_GIT = False
try:
    OUTPUT_ERRORS = u_converters.extended_bool(getenv('OUTPUT_ERRORS'))
except:
    print(traceback.format_exc())
    OUTPUT_ERRORS = False

ERROR_WEBHOOK = getenv('ERROR_WEBHOOK')

def in_dst():
    dt = datetime.datetime.now()
    timezone = pytz.timezone("US/Pacific")
    timezone_aware_date = timezone.localize(dt, is_dst=None)
    return timezone_aware_date.tzinfo._dst.seconds != 0

bingo_hour = 23
if in_dst():
    bingo_hour = 22

bingo_time = datetime.time(
    hour = bingo_hour,
    minute = 0,
    tzinfo = datetime.timezone.utc
)

MAIN_GUILD = 958392331671830579

REMINDERS_CHANNEL = 1138583859508813955
PING_LISTS_CHANNEL = 1060344552818483230
DAILY_BOARD_CHANNEL = 958705808860921906
WEEKLY_BOARD_CHANNEL = 958763826025742336
RULETTE_RULES_CHANNEL = 1223276940681678931
# lol they get longer by 1 letter each time

database = None # type: u_files.DatabaseInterface

class Triggers_cog(
        u_custom.CustomCog,
        name="Triggers",
        description="Hey there! owo\n\nyou just lost the game >:3"
    ):
    bot: commands.Bot | u_custom.CustomBot = None

    bingo_cache = {}
    parsed_bingo_cache = {}

    # chains_data = u_files.load("data/chains_data.json")

    last_pk_trigger = 0
    pk_triggers = ["why is the bot talking", "why is this bot talking", "why bot talk", "why are you a bot", "are you actually a bot", "are you a bot", "what is this bot", "what is pk",
        "is this bot sentient", "are you an actual bot", "whats this bot", "whats this bot", "thru a bot", "through a bot", "what kind of bot is that", "you are a bot", "its a bot",
        "its a bot", "whats up with all these bots", "what is this bot", "whats this bot", "sentient bot", "ur a bot", "bot say it", "actually a bot", "bot tag" "are you a bot",
        "are u a bot", "understand this bot", "why is a bot", "is this new bot", "got a new bot", "if theyre bots", "is this chatgpt", "is this user gpt", "is this user a bot",
        "talking to a bot", "bot or a human", "bot or human", "why is the bot alive", "why is this bot alive", "why is there a bot talking", "why is a bot talking", "why is bot talking",
        "it has a bot tag", "what is pluralkit", "what is plural kit", "whats pluralkit", "whats plural kit"
    ]
    pk_trigger_blacklist = [594222637773881350, 1060254289899044954] # List of account ids that shouldn't be able to trigger the PluralKit explanation.

    pk_triggers = [f" {item} " for item in pk_triggers] # Add spaces on both sides of each trigger, so there isn't a Scunthorpe problem.

    def __init__(self: typing.Self) -> None:
        super().__init__()
        self.hourly_loop.start()
        self.daily_loop.start()

        self.bingo_cache = u_bingo.live(database=database)
        self.bingo_cache_updated()
    
    def cog_unload(self: typing.Self):
        self.hourly_loop.cancel()
        self.daily_loop.cancel()
    
    def bingo_cache_updated(self: typing.Self) -> None:
        """Runs whenever the bingo cache is updated."""
        self.parsed_bingo_cache = {
            "daily_tile_string": u_text.split_chunks(self.bingo_cache["daily_tile_string"], 3),
            "daily_enabled": u_bingo.decompile_enabled(self.bingo_cache["daily_enabled"], 5),
            "daily_board_id": self.bingo_cache["daily_board_id"],
            "weekly_tile_string": u_text.split_chunks(self.bingo_cache["weekly_tile_string"], 3),
            "weekly_enabled": u_bingo.decompile_enabled(self.bingo_cache["weekly_enabled"], 9),
            "weekly_board_id": self.bingo_cache["weekly_board_id"]
        }
    
    def _get_channel_chain(self, channel_id: int) -> dict:
        """Returns the chains data for a specific channel."""
        return database.load("chains_data", str(channel_id), default = {"message": None, "sender": 0, "count": 0})

    def _update_channel_chain(self, channel_id: int, data: dict) -> None:
        """Updates the chains data for a specific channel."""
        database.save("chains_data", str(channel_id), data=data)



    
    
    ######################################################################################################################################################
    ##### UTILITY FUNCTIONS ##############################################################################################################################
    ######################################################################################################################################################
    
    def get_pk_explanation(
            self: typing.Self,
            replace_pings: bool = False,
            auto_trigger: bool = True
        ) -> str:
        """Returns the PluralKit explanation with replacements made as told.
        
        Arguments:
            replace_pings (bool, optional): Whether or not to replace the role pings with user pings. Defaults to False.
        
        Returns:
            str: The PluralKit explanation with replacements made as told."""
        text = "On the server, you might see some users that appear to be talking with a bot or app tag. However, unless they have a color role (e.g. <@&960885443153522691>, <@&1032864473700122687>, <@&966569150468210723>, <@&973840335841140769>), they are not bots. They are using <@466378653216014359>, an integration that allows them to talk under different profiles, each with a custom name and profile picture, while using the same account. This is useful for multiple people sharing one body, aka systems, who want to be differentiated from one another when using their discord account. Even though they show up with a bot or app tag, again, **they are not bots**. Please refrain from referring to them as bots, or joking about it.\n\nMore information on plurality can be found here:\n<https://morethanone.info/>"
        
        if replace_pings:
            text = text.replace(
                "<@&960885443153522691>", "<@960869046323134514>"
            ).replace(
                "<@&1032864473700122687>", "<@1029793702136254584>"
            ).replace(
                "<@&966569150468210723>", "<@966474721619238972>"
            ).replace(
                "<@&973840335841140769>", "<@973811353036927047>"
            )
        
        if auto_trigger:
            text = f"{text}\n\n*This was triggered automatically by something you said. If I misinterpreted the context and this relates to the bot Latent-Dreamer, run `%ld` for an explanation. If I misinterpreted the context, it was not relating to Latent-Dreamer and this makes no sense, feel free to ignore this, or ping my creator to let them know.*"
        
        return text
    
    async def refresh_status(self: typing.Self) -> None:
        await u_interface.refresh_status(
            bot = self.bot,
            database = database
        )




    
            
    ######################################################################################################################################################
    ##### VERY FEW COMMANDS ##############################################################################################################################
    ######################################################################################################################################################
        
    @commands.command(
        name = "add_stonk_tick",
        description = "Adds a missing stonk tick.",
        brief = "Adds a missing stonk tick.",
        hidden = True
    )
    @commands.is_owner()
    async def add_stonk_tick_command(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        if not u_interface.is_reply(ctx.message):
            await ctx.reply("Please reply to the stonk tick.")
            return
        
        msg = ctx.message.reference.resolved

        await self.on_stonk_tick(msg)
        
    @commands.command(
        name = "daily_loop",
        description = "Runs the daily loop.",
        brief = "Runs the daily loop.",
        aliases = ["daily_task"],
        hidden = True
    )
    @commands.is_owner()
    async def daily_loop_command(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        await self.daily_loop()
        await ctx.reply("Done.")
        
    @commands.command(
        name = "hourly_loop",
        description = "Runs the hourly loop.",
        brief = "Runs the hourly loop.",
        aliases = ["hourly_task"],
        hidden = True
    )
    @commands.is_owner()
    async def hourly_loop_command(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        await self.hourly_loop()
        await ctx.reply("Done.")
        
    @commands.group(
        name = "pk",
        description = "Provides a more tailored PluralKit description.",
        brief = "Provides a more tailored PluralKit description.",
        invoke_without_command = True,
        pass_context = True
    )
    @commands.check(u_checks.hide_from_help)
    async def pk_explanation_command(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        if ctx.invoked_subcommand is not None:
            return
        
        if ctx.guild.id != 958392331671830579:
            await ctx.reply(self.get_pk_explanation(replace_pings=True, auto_trigger=False))
            return
        
        await ctx.reply(self.get_pk_explanation(auto_trigger=False))


        
        

    
    @pk_explanation_command.group(
        name = "counter",
        description = "Days since the last PluralKit confusion.",
        brief = "Days since the last PluralKit confusion.",
        invoke_without_command = True,
        pass_context = True
    )
    async def pk_explanation_counter(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        if ctx.invoked_subcommand is not None:
            return
        
        counter_data = database.get_daily_counter("pk_counter")
        record = database.get_daily_counter("pk_counter_record")

        embed = u_interface.gen_embed(
            title = "PluralKit Counter",
            description = "Days since the last PluralKit confusion:\n# {}\nThe current record is **{}**.".format(u_text.smart_number(counter_data), u_text.smart_text(record, 'day'))
        )
        await ctx.reply(embed=embed)


        
        

    
    @pk_explanation_counter.command(
        name = "reset",
        description = "Resets the PluralKit counter.",
        brief = "Resets the PluralKit counter."
    )
    async def pk_explanation_counter_reset(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        # List of non-sub admin user ids that are allowed to use the command.
        whitelisted = [
            1060254289899044954
        ]
        if not (ctx.author.id in whitelisted or u_checks.sub_admin_check(ctx)):
            await ctx.reply("I''m sorry, but you do not have the permissions to use this command.")
            return
        
        counter_data = database.get_daily_counter("pk_counter")
        record = database.get_daily_counter("pk_counter_record")

        is_record = counter_data > record

        database.set_daily_counter("pk_counter", 0)
        if is_record:
            database.set_daily_counter("pk_counter_record", counter_data)

        embed = u_interface.gen_embed(
            title = "PluralKit Counter",
            description = "The counter has been reset to 0.\nIt was at **{}** before it was reset.\n\n{}".format(
                u_text.smart_number(counter_data),
                "This beaks the previous record of **{}**.".format(u_text.smart_number(record)) if is_record else ""
            )
        )
        await ctx.reply(embed=embed)


        
        

    @commands.command(
        name = "ld",
        brief="Provides a description of Latent-Dreamer.",
        description="Provides a description of Latent-Dreamer.",
        aliases=["latent", "latent-dreamer"]
    )
    @commands.check(u_checks.hide_from_help)
    async def latent_explanation_command(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        await ctx.reply("Latent-Dreamer is a bot that creates new responses via ChatGPT when triggered by specific phrases.\nWhen triggered she will send a message based on what the trigger was.\nThings like 'google en passant' and 'chess 2' always use the same prompt. Triggers such as 'what is ...' and 'google ...' will have ChatGPT provide an answer to the question or generate a list of search terms, depending on which was triggered.\n\nLatent-Dreamer also has a credits system to limit the amount of times people can trigger her per day.\nMore information about the credits system can be found [here](<https://discord.com/channels/958392331671830579/958392332590387262/1110078862286671962>) or by pinging Latent-Dreamer with the word 'credits'.")


        
        

    # @commands.command(
    #     name = "get_rules",
    #     brief="Gives you the current rules.",
    #     description="Gives you the current rules."
    # )
    # @commands.check(u_checks.hide_from_help)
    # async def get_rules(
    #         self: typing.Self,
    #         ctx: commands.Context | u_custom.CustomContext
    #     ):
    #     rules = u_rulette.get_rules()

    #     lines = []
    #     for rule in rules:
    #         lines.append(f"- {rule.describe()}")
        
    #     await ctx.reply("\n".join(lines))


        
    

    
    
    ######################################################################################################################################################
    ##### HOURLY LOOP ####################################################################################################################################
    ######################################################################################################################################################

    @tasks.loop(
        minutes = 60
    )
    async def hourly_loop(self: typing.Self):
        print("Hourly loop triggered at {}.".format(datetime.datetime.now()))

        try:
            ### REMINDERS ###

            bst_time = u_bread.bst_time()

            reminder_data = database.load("reminders", default=None)

            if reminder_data is None:
                data = {
                    "disallowed": [],
                    "reminder_list": []
                }
                database.save("reminders", data=data)
                
                reminder_data = data.copy()

            reminder_channel = None

            for reminder in reminder_data["reminder_list"]:
                if reminder["hour"] != bst_time:
                    continue
                
                if reminder_channel is None:
                    reminder_channel = await self.bot.fetch_channel(REMINDERS_CHANNEL)

                ping_id = reminder["user"]

                if not str(ping_id).startswith("&"): # Filter out role pings.
                    found_member = discord.utils.find(lambda m: str(m.id) == str(ping_id), reminder_channel.guild.members)

                    if found_member is None:
                        continue

                embed = u_interface.gen_embed(
                    title = "You had a reminder set for now!",
                    description = reminder["text"]
                )
                await reminder_channel.send(content="<@{}>".format(ping_id), embed=embed)
            
            ### XKCD PINGLIST ###
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://xkcd.com/info.0.json") as resp:
                    if resp.status != 200:
                        return
                    
                    return_json = await resp.json()
            
            ping_list_data = database.load("ping_lists", default={})

            if return_json["num"] > ping_list_data.get("xkcd_previous", return_json["num"]):
                ping_list_channel = await self.bot.fetch_channel(PING_LISTS_CHANNEL) # type: discord.TextChannel

                embed = u_interface.gen_embed(
                    title = "{}: {}".format(return_json["num"], return_json["safe_title"]),
                    title_link = "https://xkcd.com/{}/".format(return_json["num"]),
                    image_link = return_json["img"],
                    footer_text = return_json["alt"]
                )

                ping_list_members = ping_list_data.get("xkcd_strips", [])
                try:
                    ping_list_members = list(filter(u_interface.Filter_Member_In_Guild(ping_list_channel.guild), ping_list_members))
                except:
                    pass

                # For funzies, shuffle the pinglist order.
                random.shuffle(ping_list_members)

                content = "New xkcd strip!!\n\nPinglist:\n{}\nUse `%xkcd ping` to add or remove yourself from the pinglist.".format("".join([f"<@{str(item)}>" for item in ping_list_members]))

                xkcd_message = await ping_list_channel.send(content=content, embed=embed)

                ping_list_data["xkcd_previous"] = return_json["num"]
                database.save("ping_lists", data=ping_list_data)

                try:
                    created_thread = await xkcd_message.create_thread(
                        name=f"Comic #{return_json['num']}: {return_json['title']} discussion thread",
                        auto_archive_duration=4320,
                        reason="Auto thread creation for xkcd pinglist."
                    )
                    await created_thread.send(f"Discussion for this comic goes here!\n[Explain xkcd link.](<https://www.explainxkcd.com/wiki/index.php/{return_json['num']}>)")
                except:
                    print("Issue with creating xkcd thread.")
                    print(traceback.format_exc())
            
            # Update the bot status.
            try:
                await self.refresh_status()
            except:
                print(traceback.format_exc())
            
            # Save and backup database.
            database.save_database(make_backup=True)

            # Running hourly_task in other cogs.
            for cog in self.bot.cogs.values():
                if cog.__cog_name__ == self.__cog_name__:
                    continue

                try:
                    await cog.hourly_task()
                except AttributeError:
                    pass
        except Exception as error:
            print(traceback.format_exc())
            u_interface.output_error(
                ctx = None,
                error = error
            )



    @hourly_loop.before_loop
    async def hourly_setup(self: typing.Self):
        # Update the bot status.
        try:
            await self.refresh_status()
        except:
            print(traceback.format_exc())

        # This just waits until it's time for the first iteration.
        print("Starting hourly loop, current time is {}.".format(datetime.datetime.now()))

        minute_in_hour = 5 # 5 would be X:05, 30 would be X:30.

        wait_time = time.time() - (minute_in_hour * 60)
        wait_time = 3600 - (wait_time % 3600) + 2 # Artificially add 2 seconds to ensure it stops at the correct time.

        print("Waiting to start hourly loop for {} minutes.".format(round(wait_time / 60, 2)))
        
        await asyncio.sleep(wait_time)
        
        print("Finished waiting at {}.".format(datetime.datetime.now()))




    
    
    ######################################################################################################################################################
    ##### DAILY LOOP #####################################################################################################################################
    ######################################################################################################################################################

    @tasks.loop(
        time = bingo_time
    )
    async def daily_loop(self: typing.Self):
        print("Daily loop triggered at {}".format(datetime.datetime.now()))

        try:
            hour_offset = 5 # The number of hours to subract from the current unix timestamp.
            day_of_the_week = ((int(time.time()) - (hour_offset * 3600)) // 86400 + 4) % 7
            weekly_board = day_of_the_week == 0

            ##### Archive the old bingo boards. #####

            # Archive daily board and the weekly board if it's Monday.
            live_data = u_bingo.live(database=database)

            archive_5x5 = database.load("bingo", "previous_5x5_boards", default={})

            archive_5x5[str(live_data["daily_board_id"])] = {
                "tile_string": live_data["daily_tile_string"],
                "enabled": live_data["daily_enabled"]
            }

            database.save("bingo", "previous_5x5_boards", data=archive_5x5)

            # If it's the day of the weekly board then archive it since we'll be making a new one.
            if weekly_board:
                archive_9x9 = database.load("bingo", "previous_9x9_boards", default={})

                archive_9x9[str(live_data["weekly_board_id"])] = {
                    "tile_string": live_data["weekly_tile_string"],
                    "enabled": live_data["weekly_enabled"]
                }

                database.save("bingo", "previous_9x9_boards", data=archive_9x9)
            
            ##### Handle the day stats. #####
                
            handled_stats = False

            try:
                # Load the previous day stats.
                existing = u_files.load("data", "bread", "day_stats.json", default={}, join_file_path=True)

                # Update the previous day stats to add this last day's stats.
                existing[
                        str(live_data.get("daily_board_id", time.time() // 1))
                    ] = database.load("bread", "day_stats", default={})

                # Save the day stats file.
                u_files.save("data", "bread", "day_stats.json", data=existing, join_file_path=True)

                # Clear the day stats in the database.
                database.save("bread", "day_stats", data={})
                
                handled_stats = True
            except:
                print(traceback.format_exc())

            ##### Make new boards. #####

            new_daily = u_bingo.generate_5x5_board(database=database)

            live_data["daily_tile_string"] = new_daily
            live_data["daily_enabled"] = 0
            live_data["daily_board_id"] += 1

            if weekly_board:
                new_weekly = u_bingo.generate_9x9_board(database=database)

                live_data["weekly_tile_string"] = new_weekly
                live_data["weekly_enabled"] = 0
                live_data["weekly_board_id"] += 1
            
            u_bingo.update_live(database=database, bot=self.bot, new_data=live_data)
            self.bot.update_bingo_cache(live_data)

            ##### Send board announcement messages. #####
            # Send the daily board.
            daily_channel = await self.bot.fetch_channel(DAILY_BOARD_CHANNEL)
            u_images.render_full_5x5(
                database = database,
                tile_string = new_daily,
                enabled = 0
            )

            await daily_channel.send(
                "Bingo Board #{board_id}!\nThe wiki:\n<https://bread.miraheze.org/wiki/The_Bread_Game_Wiki>\n{stats_text}".format(
                    board_id = live_data["daily_board_id"],
                    stats_text = f"The previous day's stats have been archived! You can check the stats with `%bread day {live_data['daily_board_id'] - 1}`!" if handled_stats else "*Something went wrong with the daily stats.*"
                ),
                file=discord.File(r'images/generated/bingo_board.png')
            )
            
            # If it's the day for it, send the weekly board.
            if weekly_board:
                weekly_channel = await self.bot.fetch_channel(WEEKLY_BOARD_CHANNEL)
                u_images.render_board_9x9(
                    database = database,
                    tile_string = new_weekly,
                    enabled = 0
                )

                await weekly_channel.send("Weekly Bingo Board #{}!".format(live_data["weekly_board_id"]), file=discord.File(r'images/generated/bingo_board.png'))
            
            ##### Increment counters. #####
            
            counter_list = [
                "pk_counter"
            ]
            for counter in counter_list:
                database.increment_daily_counter(counter, amount=1)
            
            ##### Make role snapshot. #####
                
            u_interface.snapshot_roles(
                guild = self.bot.get_guild(MAIN_GUILD)
            )
        except:
            print(traceback.format_exc())

        ##### Running _daily_task in other cogs. #####
        for cog in self.bot.cogs.values():
            if cog.__cog_name__ == self.__cog_name__:
                continue

            try:
                await cog.daily_task()
            except AttributeError:
                pass




    
    
    ######################################################################################################################################################
    ##### ON EVENTS ######################################################################################################################################
    ######################################################################################################################################################
        
    async def on_stonk_tick(
            self: typing.Self,
            message: discord.Message
        ):
        if message.content[-1] in "!.?":
            return
        
        stonk_values = u_stonks.parse_stonk_tick(message)

        ### Updating stonk history. ###
        stonk_history = u_stonks.stonk_history(database)

        append = {
            stonk.internal_name: values[-1]
            for stonk, values in stonk_values.items()
        }

        stonk_history.append(append)
        
        database.save("stonks", "stonk_history", data=stonk_history)

        ### Updating current values. ###
        new = {
            "message_link": message.jump_url,
            "tick_number": len(stonk_history) - 1,
            "values": append
        }

        database.save("stonks", "current_values", data=new)
        
        ### Running the stonk algorithms. ###

        u_algorithms.run_all_algorithms(database)

        ### Attempt to generate the stonk report. ###

        send_file = None
        try:
            u_images.stonk_report(database)
            send_file = discord.File("images/generated/stonk_report.png")
        except:
            # Something went wrong :(
            print(traceback.format_exc())

        ### Send message. ###

        stonk_pinglist = database.get_ping_list("stonk_tick_pings")
        try:
            stonk_pinglist = list(filter(u_interface.Filter_Member_In_Guild(message.guild), stonk_pinglist))
        except:
            pass

        # For funzies, shuffle the pinglist order.
        random.shuffle(stonk_pinglist)

        await message.reply("{}\n\nCopy of tick {}:\n\n{}".format(
            "".join(["<@{}>".format(user_id) for user_id in stonk_pinglist]),
                new["tick_number"],
                message.content
            ),
            file = send_file
        )
        
        # Run the auto detection.
        try:
            await u_detection.on_stonk_tick_detection(
                    stonk_data = stonk_values,
                    bot = self.bot,
                    message = message,
                    database = database,
                    bingo_data = self.parsed_bingo_cache
                )
        except:
            print(traceback.format_exc())
            await message.reply("Something went wrong with the auto detection.\nPlease ping Duck Duck.")    
        
        # Save the database to file.
        database.save_database(make_backup=True)

        # Update public/stonk_history.json.
        database.save_json_file("public", "stonk_history.json", data=u_stonks.stonk_history(database), join_file_path=True)

        # Update public/stonk_current.json.
        database.save_json_file("public", "stonk_current.json", data=u_stonks.full_current_values(database), join_file_path=True)

        # Running _on_stonk_tick in other cogs.
        for cog in self.bot.cogs.values():
            if cog.__cog_name__ == self.__cog_name__:
                continue

            try:
                await cog._on_stonk_tick(message)
            except AttributeError:
                pass

        
    
    async def chains(
            self: typing.Self,
            message: discord.Message
        ):
        if u_checks.sensitive_check(message.channel):
            return
        
        if message.channel.id == 958679256156749866: # new-members
            return
        
        channel_data = self._get_channel_chain(message.channel.id).copy()

        if channel_data["message"] != message.content:
            self._update_channel_chain(
                channel_id = message.channel.id,
                data = {
                    "message": message.content,
                    "sender": message.author.id,
                    "count": 1
                }
            )

            if channel_data["count"] >= 3:
                # If the hugging emoji was in the chain, or in the message that broke the chain, react with 🫂 to give the person a hug.
                try:
                    if any(search in message.content or search in channel_data["message"] for search in [":people_hugging:", "🫂"]):
                        # Hug <3
                        emoji = "🫂"
                        await message.add_reaction(emoji)
                    elif message.channel.id == 958542943625556038:
                        # Capybara <3
                        emoji = "<:capybara:971174918840549418>"
                        await message.add_reaction(emoji)
                    else:
                        emoji = "<a:you_broke_the_chain:1064349721361133608>"
                        await message.add_reaction(emoji)
                except:
                    emoji = "❌"
                    await message.add_reaction(emoji)


                def proxy_check(m: discord.Message):
                    return m == message
                
                try:
                    # Attempt to find the deleted proxied message.
                    await self.bot.wait_for(
                        "message_delete",
                        check = proxy_check,
                        timeout = 2
                    )

                    async for history in message.channel.history(limit=10, after=message):
                        if history.content != message.content:
                            continue

                        if not history.author.bot:
                            continue

                        await history.add_reaction(emoji)
                except asyncio.TimeoutError:
                    # No proxied message was found, so it was probably not proxied by PluralKit.
                    pass
            return
        
        if channel_data["sender"] == message.author.id:
            # So someone can't go twice in a row.
            return
        
        if message.author.bot:
            # Accounts with bot tags shouldn't be able to contribute to the chains, but can still break it.
            return
        
        new = {
            "message": message.content,
            "sender": message.author.id,
            "count": channel_data["count"] + 1
        }

        self._update_channel_chain(
            channel_id = message.channel.id,
            data = new
        )

        # Run the auto detection.
        if new["count"] >= 10:
            await u_detection.chains_detection(
                bot = self.bot,
                message = message,
                database = database,
                bingo_data = self.parsed_bingo_cache,
                chain_data = new
            )

        



        
    async def on_gamble(
            self: typing.Self,
            message: discord.Message
        ):
        # Gamble messages.

        command = None
        if u_interface.is_reply(message, allow_ping=False):
            command = message.reference.message_id

        gamble_messages = database.load("bread", "gamble_messages", default={})

        gamble_messages[f"{message.channel.id}.{message.id}"] = {
            "content": message.content,
            "command": command # Used in auto-detection for d44 and w18.
        }

        if len(gamble_messages) > 500:
            gamble_messages.pop(next(iter(gamble_messages)))
        
        database.save("bread", "gamble_messages", data=gamble_messages)
    
    async def ask_ouija(
            self: typing.Self,
            message: discord.Message
        ):
        if u_checks.sensitive_check(message.channel):
            return
        
        if hasattr(message, "webhook_id") and message.webhook_id is not None:
            return
        
        # Allow custom emojis.
        if message.content.startswith("<"):
            if len(re.sub("<a?:\w+:\d+>", "", message.content)) != 0:
                return
        
        ouija_data = database.get_ouija_data(message.channel.id)

        if not ouija_data["active"]:
            return
        
        # Contributing twice in a row is disallowed when strict mode is enabled.
        if ouija_data.get("strict") and message.author.id == ouija_data.get("last_sender"):
                return
            
        # Author contributing.
        if message.author.id == ouija_data.get("author_id"):
            return
        
        if message.content.lower() == "goodbye":
            database.set_ouija_data(message.channel.id, active = False)

            reply_message = message.channel.get_partial_message(ouija_data["message_id"])

            try:
                await u_interface.smart_reply(reply_message, "Ouija says:\n{}".format(u_text.ping_filter(ouija_data["letters"])))
            except AttributeError: # If the message was deleted.
                await u_interface.safe_send(message, "<@{}>,\nOuija says:\n{}".format(ouija_data["author_id"], u_text.ping_filter(ouija_data["letters"])))
            except:
                # Reraise any other exceptions.
                raise

            return
        
        content = message.content.strip()

        if content == "** **":
            content = " "

        database.set_ouija_data(
            channel_id = message.channel.id,
            letters = "{}{}".format(ouija_data["letters"], content),
            last_sender = message.author.id
        )
    
    async def counting(
            self: typing.Self,
            message: discord.Message
        ):
        if u_checks.sensitive_check(message.channel):
            return
        
        # Prevent accounts with a bot tag from contributing to the counting.
        if message.author.bot:
            return
        
        if u_converters.is_digit(message.content):
            sent_number = u_converters.parse_int(message.content)
        else:
            try:
                sent_number = round(u_solvers.evaluate_problem(message.content), 5)
            except u_custom.BingoError:
                return

        counting_data = database.get_counting_data(message.channel.id)

        if sent_number <= counting_data["count"]:
            return

        def proxy_check(m: discord.Message):
            return m == message

        if sent_number > counting_data["count"] + 1:
            if counting_data["count"] == 0: # If 1 hasn't been sent since the last break.
                return
            
            database.set_counting_data(
                channel_id = message.channel.id,
                count = 0,
                sender = 0
            )
            embed = u_interface.gen_embed(
                title = "You broke the counting!",
                description = "The counting was broken at **{}** by {}!\nYou must restart at 1.\nGet ready for the brick <:trol:1015821884450947173>\n\nShockingly, {} is not equal to {} + 1.".format(
                    u_text.smart_number(counting_data["count"]),
                    message.author.mention,
                    u_text.smart_number(int(sent_number) if round(sent_number, 5).as_integer_ratio()[-1] == 1 else round(sent_number, 5)),
                    u_text.smart_number(counting_data["count"]),
                )
            )
            try:
                try:
                    emoji = "<:blunder:958752015188656138>"
                    await message.add_reaction(emoji) # <a:you_cant_count:1134902783095603300>
                except:
                    emoji = "💀"
                    await message.add_reaction(emoji)
                finally:
                    await u_interface.smart_reply(message, embed=embed)

                    try:
                        # Attempt to find the deleted proxied message.
                        await self.bot.wait_for(
                            "message_delete",
                            check = proxy_check,
                            timeout = 2
                        )

                        async for history in message.channel.history(limit=10, after=message):
                            if history.content != message.content:
                                continue

                            if not history.author.bot:
                                continue

                            await history.add_reaction(emoji)
                    except asyncio.TimeoutError:
                        # No proxied message was found, so it was probably not proxied by PluralKit.
                        pass

            except discord.errors.Forbidden:
                database.set_counting_data(channel_id = message.channel.id, count = counting_data["count"], sender = counting_data["sender"])
            
            return
        
        # So 1.5 doesn't get counted for 2.
        if int(sent_number) != int(counting_data["count"] + 1):
            return
        
        if message.author.id == counting_data["sender"]:
            return # So someone can't go twice in a row.
        
        database.set_counting_data(
            channel_id = message.channel.id,
            count = int(sent_number),
            sender = message.author.id
        )
        try:
            await message.add_reaction("<a:you_can_count:1133795506099867738>")

            try:
                # Attempt to find the deleted proxied message.
                await self.bot.wait_for(
                    "message_delete",
                    check = proxy_check,
                    timeout = 2
                )

                async for history in message.channel.history(limit=10, after=message):
                    if history.content != message.content:
                        continue

                    if not history.author.bot:
                        continue

                    await history.add_reaction("<a:you_can_count:1133795506099867738>")

            except asyncio.TimeoutError:
                # No proxied message was found, so it was probably not proxied by PluralKit.
                pass
        except discord.errors.Forbidden:
            database.set_counting_data(channel_id = message.channel.id, count = counting_data["count"], sender = counting_data["sender"])
                
    async def pk_reply(
            self: typing.Self,
            message: discord.Message
        ):
        if message.flags.silent:
            # If the message is a silent message.
            return
        
        # If the author of the message has a bot tag, we can safely ignore it.
        if message.author.bot:
            return
        
        # Get the message that was replied-to.
        replied_to = message.reference.resolved
        
        if not (hasattr(replied_to, "webhook_id") and replied_to.webhook_id is not None):
            # If the message doesn't have a webhook id (the first message in threads and discussion channel threads will do this),
            # or if the webhook id is None, then the message was not sent by a webhook.
            return
        
        # Replied-to message is a webhook, it's likely it's a proxied message.
        # Let's pray we're not rate limited.

        # Now we start an async aiohttp session so the API request can be made without blocking (at least, in theory)

        return_json = {}

        async with aiohttp.ClientSession() as session:
            # Make the request to the PluralKit API to try and get information about the replied-to message.
            async with session.get(f"https://api.pluralkit.me/v2/messages/{replied_to.id}") as resp:
                # If the status code is not 200, then the message wasn't proxied by PluralKit or something went wrong, either way stop execution.
                if resp.status != 200:
                    return
                
                return_json = await resp.json()

        
        # If we got here, then the replied-to message is a proxied message!
        
        if message.author.id == int(return_json['sender']):
            # Make sure it's not someone replying to themself.
            return 
            
        if f"<@{return_json['sender']}>" in message.content:
            # Make sure that the person being replied-to wasn't pinged in the message.
            return

        # Attempt to send a message.
        try: 
            await message.reply(f"Psst, <@{return_json['sender']}>, someone replied to you!", mention_author=False)
        except discord.errors.HTTPException:
            await message.channel.send(f"Psst, <@{return_json['sender']}>, someone replied to your [message]({replied_to.jump_url})!")
    
    async def pk_explanation(
            self: typing.Self,
            message: discord.Message
        ):
        if message.author.id in self.pk_trigger_blacklist or message.author.bot:
            return

        input_modify = " {} ".format(str(message.content).replace("\n", " ").lower().replace('"', "").replace("'", ""))

        if not(any([trigger in input_modify for trigger in self.pk_triggers])):
            return
        
        if time.time() - self.last_pk_trigger < 60:
            await message.author.send(self.get_pk_explanation(replace_pings=True, auto_trigger=True))
            return
        
        self.last_pk_trigger = time.time()
        await message.reply(self.get_pk_explanation(
            replace_pings=message.guild.id != 958392331671830579, 
            auto_trigger=True))
    
    async def brick_stats_correcting(
            self: typing.Self,
            message: discord.Message
        ):
        if u_checks.serious_channel_check(message.channel):
            return
        
        split = message.content.split(" ")
        if len(split) <= 2:
            return
        
        user = split[2]
        user = discord.utils.find(lambda m: user in [m.name, m.display_name, m.global_name, m.mention, m.id, str(m)], message.guild.members)
        if user is not None:
            await message.reply(f"Do you mean `$brick {user.id} stats`?")

    async def seven_twenty_seven(
            self: typing.Self,
            message: discord.Message
        ):
        if u_checks.serious_channel_check(message.channel):
            return
        
        content = message.content

        content = re.sub(r"<@&?\d+>", "", content) # Remove pings.
        content = re.sub(r"<#\d+>", "", content) # Remove channel mentions.
        content = re.sub(r"<a?:\w+:\d+>", "", content) # Remove custom emojis.
        content = re.sub(r"(http|ftp|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])?", "", content) # Remove urls. Pattern sourced from https://stackoverflow.com/questions/6038061/regular-expression-to-find-urls-within-a-string

        if "727" not in content:
            # 727 was in a ping, channel mention, emoji, or url.
            return
        
        if random.randint(1, 32) != 1:
            return
        
        # Now, fetch the users in the "727_pinglist" from the pinglist data and send a message pinging all of them.
        ping_data = database.get_ping_list("727_pinglist")
        try:
            ping_list = list(filter(u_interface.Filter_Member_In_Guild(message.guild), ping_list))
        except:
            pass

        # For funzies, shuffle the pinglist order.
        random.shuffle(ping_data)

        await message.reply("".join([f"<@{user_id}>" for user_id in ping_data]), mention_author=False)
        return
    
    async def auto_detection(
            self: typing.Self,
            message: discord.Message
        ):
        # Filter out all messages sent by the bot, unless it's an objective completion message.
        if message.author.id == self.bot.user.id:
            if not(u_interface.is_reply(message) and "completed!" in message.content):
                return
            
        await u_detection.on_message_detection(
            bot = self.bot,
            message = message,
            database = database,
            bingo_data = self.parsed_bingo_cache
        )
    
    async def daily_stats(
            self: typing.Self,
            message: discord.Message
        ):
        if message.guild is None:
            return
        
        # Ensure messages are only counted if they're sent in the AC server.
        if message.guild.id != MAIN_GUILD:
            return
        
        stats = database.load("bread", "day_stats", default={})

        def increment(key: str, *, amount: int = 1):
            nonlocal stats
            
            if key not in stats:
                stats[key] = amount
                return
            
            stats[key] += amount

        # The number of sent messages.
        increment("sent_messages")

        # The number of bread commands.
        if message.content.startswith("$bread"):
            increment("bread_commands")
        
        # The number of messages sent in #bread-rolls.
        if message.channel.id == 967544442468843560:
            increment("bread_rolls_messages")
        
        # The number of messages sent in #announcements.
        if message.channel.id == 958763826025742336:
            increment("announcements_made")
        
        # The number of messages sent in #new-members, so long as the message content is blank.
        if message.channel.id == 958679256156749866 and message.content == "":
            increment("new_members")
        
        # The number of messages sent that are just "skill issue"
        if message.content.lower() == "skill issue":
            increment("skill_issues")
        
        # The number of messages that contain "owo"
        if "owo" in message.content.lower():
            increment("owo_messages")
        
        # The number of times @gets pinged too much was pinged.
        if "<@&967443956659019786>" in message.content:
            increment("gptm_pings")
        
        # The number of messages that contain "ah yes" after commas are removed.
        if "ah yes" in message.content.lower().replace(",", ""):
            increment("ah_yes")

        # The following ones all require the message being sent by Machine-Mind.
        if u_interface.is_mm(message):
            # The number of messages sent by Machine-Mind.
            increment("mm_messages")

            replied = u_interface.is_reply(message)

            # The number of gambles done.
            if u_interface.is_gamble(message):
                increment("gambles_done")
            
            # The amount of times alchemy was completed.
            if replied and "Well done. You have created" in message.content:
                increment("alchemy_completed")
            

            # The number of normal bricks found, along with the total number of bricks done.
            if message.content in [":bricks:", "🧱"]:
                increment("normal_bricks")
                increment("total_bricks")
            
            # The number of golden bricks found, along with the total number of bricks done.
            if message.content == "<:brick_gold:971239215968944168>":
                increment("gold_bricks")
                increment("total_bricks")
            
            # There are currently 4 different chessatron completion messages.
            # This tron completion message is used if you're making 1 or 2 trons, it sends it once per tron.
            if "You have collected all the chess pieces!" in message.content:
                increment("chessatrons_made")
            
            # This tron completion message is used for if you're making 3 to 9 trons, it also sends it once per tron.
            if "Congratulations! You've collected all the chess pieces!" in message.content:
                increment("chessatrons_made")
            
            # This tron completion message is used for 10 to 4,999 chessatrons, it sends a single summary message, and then messages containing the chessatron emoji for each tron made.
            if "Congratulations! More chessatrons!" in message.content:
                increment(
                    key ="chessatrons_made",
                    amount = u_text.extract_number(r"Congratulations! More chessatrons! You've made ([\d,]+) of them\.", message.content, default=1)
                )
            
            # This tron completion message is used for if you're making 5,000 or more chessatrons at once, it sends only two messages, a summary, and a message with the chessatron emoji once and the number of trons made.
            if "Wow. You have created a **lot** of chessatrons." in message.content:
                increment(
                    key = "chessatrons_made",
                    amount = u_text.extract_number(r"Wow\. You have created a \*\*lot\*\* of chessatrons\. ([\d,]+) to be exact\.", message.content, default=1)
                )
            
            # Okay, done with the chessatrons.
                
            # The next two require the message being a roll summary.
            if replied and "Summary of results:" in message.content:

                # This is the number of MoaKs rolled. It's not going to be perfect, since it only uses the number shown in the roll summary.
                if "<:anarchy_chess:960772054746005534>" in message.content:
                    increment(
                        key = "moaks_rolled",
                        amount = u_text.extract_number(r"<:anarchy_chess:960772054746005534>: ([\d,]+)", message.content, default=0)
                    )

                # This is the number of gold gems rolled. Like MoaKs, it's not going to be perfect.
                if "<:gem_gold:1006498746718244944>" in message.content:
                    increment(
                        key = "gold_gems_rolled",
                        amount = u_text.extract_number(r"<:gem_gold:1006498746718244944>: ([\d,]+)", message.content, default=0)
                    )
        
        # Save the updated stats.
        database.save("bread", "day_stats", data=stats)
    
    async def mm_offline(
            self: typing.Self,
            message: discord.Message
        ):
        modified_content = f"{message.content} "

        if not(modified_content.startswith("$bread ") or \
               modified_content.startswith("$brick ") or \
               modified_content.startswith("$board ") or \
               modified_content.startswith("$say ") or \
               modified_content.startswith("$analysis ") or \
               modified_content.startswith("$verify ") or \
               modified_content.startswith("$move ")
            ):
            return
        
        mm_member = discord.utils.find(lambda m: m.id == 960869046323134514, message.guild.members)

        if mm_member is None:
            return
        
        if mm_member.raw_status == "offline":
            await message.reply("Machine-Mind is currently listed as offline, so doing things such as bread rolling, bricking, and playing chess is impossible.")
    
    async def pk_filter(
            self: typing.Self,
            message: discord.Message
        ):
        # If the message does not have a webhook id, then it's probably the first message of a thread.
        # If the message does have the webhook id attribute and it's None, then it's not a proxied message.
        try:
            if message.webhook_id is None:
                return
        except AttributeError:
            return
        
        async with aiohttp.ClientSession() as session:
            # Make the request to the PluralKit API to try and get information about author of this message.
            async with session.get(f"https://api.pluralkit.me/v2/messages/{message.id}") as resp:
                # If the status code is not 200, then the message wasn't proxied by PluralKit or something went wrong, either way stop execution.
                if resp.status != 200:
                    return
                
                return_json = await resp.json()

        filter_data = database.load("pk_filter", default={})
        
        filter_ids = filter_data.get("member_ids", [])

        member_id = return_json.get("member", {}).get("id", None)

        if member_id in filter_ids:
            try:
                await message.delete()
            except discord.NotFound:
                pass
            except discord.Forbidden:
                pass

            
            

    
    @commands.Cog.listener()
    async def on_message(
            self: typing.Self,
            message: discord.Message
        ):
        # Run the auto detection. It will automatically filter out messages sent by the bot if needed.
        await self.auto_detection(message)

        # Increment the daily stats.
        await self.daily_stats(message)

        # Chains.
        await self.chains(message)

        # Make sure the bot doesn't read it's own messages.
        if message.author.id == self.bot.user.id:
            return
        
        # Just a note, while there's u_custom.CustomContext for context objects, there is no CustomMessage, so u_interface.smart_reply still needs to be used.

        # Stonk ticks.
        if u_interface.is_mm(message) and message.content.startswith("Current stonk values are as follows"):
            await self.on_stonk_tick(message)

        # PluralKit replies.
        if u_interface.is_reply(message, allow_ping=False):
            await self.pk_reply(message)
        
        # PluralKit filter.
        if message.author.bot:
            await self.pk_filter(message)
        
        # PluralKit explanation.
        await self.pk_explanation(message)

        # Counting
        if u_converters.is_digit(message.content) or u_solvers.is_math_equation_bool(message.content):
            await self.counting(message)
        
        # AskOuija
        if len(message.content) == 1 or message.content.strip() == "** **" or message.content.lower() == "goodbye" or message.content.startswith("<"):
            await self.ask_ouija(message)

        # ???

        # Profit

        # On gamble.
        if u_interface.is_gamble(message):
            await self.on_gamble(message)
        
        # Gold brick reacting.
        if message.content == "<:brick_gold:971239215968944168>" and u_interface.is_mm(message) and not u_checks.sensitive_check(message.channel):
            await message.add_reaction("<:brilliant_move:958751616939474995>")
        
        # Brick stats correcting.
        if message.content.startswith("$brick stats"):
            await self.brick_stats_correcting(message)
        
        # 727 pings.
        if "727" in message.content:
            await self.seven_twenty_seven(message)
        
        # If Machine-Mind is offline.
        if not message.author.bot and message.content.startswith("$"):
            await self.mm_offline(message)
        
        # if message.channel.id == RULETTE_RULES_CHANNEL:
        #     await u_rulette.message(
        #         bot = self.bot,
        #         message = message
        #     )




    
    
    ######################################################################################################################################################
    ##### ON REACTION ADD ################################################################################################################################
    ######################################################################################################################################################
            
    async def pk_explanation_deletion(
            self: typing.Self,
            payload: discord.RawReactionActionEvent
        ):
        """If someone reacts to a PluralKit explanation message with ❌, then we need to edit the message to something saying it was removed."""

        try:
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)

            if message.author.id != self.bot.user.id:
                return
            
            if not u_interface.is_reply(message):
                return
            
            if not("https://morethanone.info/" in message.content and "This was triggered automatically by something you said." in message.content):
                return
            
            # If it's here, it's probably the pk explanation message.

            await message.edit(content="*[PluralKit explanation text removed due to a removal reaction. It can be resummoned with `%pk`]*")
            await message.clear_reaction(payload.emoji)
        
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            print(traceback.format_exc())
            pass    
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(
            self: typing.Self,
            payload: discord.RawReactionActionEvent
        ):
        if payload.event_type != "REACTION_ADD":
            return
        
        # PluralKit explanation deleting.
        if payload.emoji.name == "❌":
            await self.pk_explanation_deletion(payload)




    
    
    ######################################################################################################################################################
    ##### ON COMMAND ERROR ###############################################################################################################################
    ######################################################################################################################################################

    @commands.Cog.listener()
    async def on_command_error(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            error: Exception
        ):
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

        if OUTPUT_ERRORS:
            try:
                await u_interface.output_error(
                    ctx = ctx,
                    error = error
                )
            except:
                print(traceback.format_exc())

        


async def setup(bot: commands.Bot):
    global database
    database = bot.database

    cog = Triggers_cog()
    cog.bot = bot
    
    # Add attributes for sys.modules and globals() so the _reload_module() function in utility.custom can read it and get the module objects.
    cog.modules = sys.modules
    cog.globals = globals()
    
    await bot.add_cog(cog)
