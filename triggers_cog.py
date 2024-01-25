"""This cog is for events like on_message along with the hourly and daily loops.
The PluralKit and Latent-Dreamer explanation commands are also here."""

from discord.ext import commands
from discord.ext import tasks
import discord
import datetime
import asyncio
import aiohttp
import time
import traceback
import re
import random
import time
import typing

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

bingo_time = datetime.time(
    hour = 23,
    minute = 0,
    tzinfo = datetime.timezone.utc
)

REMINDERS_CHANNEL = 1196865764511191090
PING_LISTS_CHANNEL = 1196865786489344120
DAILY_BOARD_CHANNEL = 1196865970355052644
WEEKLY_BOARD_CHANNEL = 1196865991632748614
# lol they get longer by 1 letter each time

database = None # type: u_files.DatabaseInterface

class Triggers_cog(u_custom.CustomCog, name="Triggers", description="Hey there! owo\n\nyou just lost the game >:3"):
    bot = None

    # bingo_cache = u_bingo.live(database=database)
    # parsed_bingo_cache = {}

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

    def __init__(self) -> None:
        super().__init__()
        self.hourly_loop.start()
        self.daily_loop.start()
    
    def cog_unload(self):
        self.hourly_loop.cancel()
        self.daily_loop.cancel()

        # self._save_chains_data()
    
    # def bingo_cache_updated(self: typing.Self) -> None:
    #     """Runs whenever the bingo cache is updated."""
    #     self.parsed_bingo_cache = {
    #         "daily_tile_string": u_text.split_chunks(self.bingo_cache["daily_tile_string"], 3),
    #         "daily_enabled": u_bingo.decompile_enabled(self.bingo_cache["daily_enabled"], 5),
    #         "daily_board_id": self.bingo_cache["daily_board_id"],
    #         "weekly_tile_string": u_text.split_chunks(self.bingo_cache["weekly_tile_string"], 3),
    #         "weekly_enabled": u_bingo.decompile_enabled(self.bingo_cache["weekly_enabled"], 9),
    #         "weekly_board_id": self.bingo_cache["weekly_board_id"]
    #     }

    # def _save_chains_data(self) -> None:
    #     """Saves self.chains_data to the data file."""
    #     u_files.save("data/chains_data.json", self.chains_data)

    # def _refresh_chains_data(self) -> None:
    #     """Refreshes self.chains_data from the data file."""
    #     self.chains_data = u_files.load("data/chains_data.json")
    
    def _get_channel_chain(self, channel_id: int) -> dict:
        """Returns the chains data for a specific channel."""
        return database.load("chains_data", str(channel_id), default = {"message": None, "sender": 0, "count": 0})

    def _update_channel_chain(self, channel_id: int, data: dict) -> None:
        """Updates the chains data for a specific channel."""
        database.save("chains_data", str(channel_id), data=data)
    
    # def save_all_data(self) -> None:
    #     """Saves all stored data to files."""
    #     self._save_chains_data()



    
    
    ######################################################################################################################################################
    ##### UTILITY FUNCTIONS ##############################################################################################################################
    ######################################################################################################################################################
    
    def get_pk_explanation(self: typing.Self,
            replace_pings: bool = False,
            auto_trigger: bool = True
        ) -> str:
        """Returns the PluralKit explanation with replacements made as told.
        
        Arguments:
            replace_pings (bool, optional): Whether or not to replace the role pings with user pings. Defaults to False.
        
        Returns:
            str: The PluralKit explanation with replacements made as told."""
        text = "On the server, you might see some users that appear to be talking with a bot tag. However, unless they have a color role (e.g. <@&960885443153522691>, <@&1032864473700122687>, <@&966569150468210723>, <@&973840335841140769>), they are not bots. They are using <@466378653216014359>, an integration that allows them to talk under different profiles, each with a custom name and profile picture, while using the same account. This is useful for multiple people sharing one body, aka systems, who want to be differentiated from one another when using their discord account. Even though they show up with a bot tag, again, **they are not bots**. Please refrain from referring to them as bots, or joking about it.\n\nMore information on plurality can be found here:\n<https://morethanone.info/>"
        
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
    
    async def refresh_status(self):
        status_data = database.load("bot_status")
            
        status_type = status_data["status_type"]
        status_text = status_data["status_text"]
        status_url = status_data["status_url"]

        await u_interface.change_status(
            database = database,
            bot = self.bot,
            status_type = status_type,
            status_text = status_text,
            status_url = status_url
        )




    
            
    ######################################################################################################################################################
    ##### VERY FEW COMMANDS ##############################################################################################################################
    ######################################################################################################################################################
        
    @commands.group(
        name = "pk",
        description = "Provides a more tailored PluralKit description.",
        brief = "Provides a more tailored PluralKit description.",
        invoke_without_command = True,
        pass_context = True
    )
    @commands.check(u_checks.hide_from_help)
    async def pk_explanation_command(self, ctx):
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
    async def pk_explanation_counter(self, ctx):
        if ctx.invoked_subcommand is not None:
            return
        
        counter_data = database.get_daily_counter("pk_counter")
        record = database.get_daily_counter("pk_counter_record")

        embed = u_interface.embed(
            title = "PluralKit Counter",
            description = "Days since the last PluralKit confusion:\n# {}\nThe current record is **{}**.".format(u_text.smart_number(counter_data), u_text.smart_text(record, 'day'))
        )
        await ctx.reply(embed=embed)
    
    @pk_explanation_counter.command(
        name = "reset",
        description = "Resets the PluralKit counter.",
        brief = "Resets the PluralKit counter."
    )
    async def pk_explanation_counter_reset(self, ctx):
        if ctx.invoked_subcommand is not None:
            return
        
        counter_data = database.get_daily_counter("pk_counter")
        record = database.get_daily_counter("pk_counter_record")

        is_record = counter_data > record

        database.set_daily_counter("pk_counter", 0)
        if is_record:
            database.set_daily_counter("pk_counter_record", counter_data)

        embed = u_interface.embed(
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
    async def latent_explanation_command(self, ctx):
        await ctx.reply("Latent-Dreamer is a bot that creates new responses via ChatGPT when triggered by specific phrases.\nWhen triggered she will send a message based on what the trigger was.\nThings like 'google en passant' and 'chess 2' always use the same prompt. Triggers such as 'what is ...' and 'google ...' will have ChatGPT provide an answer to the question or generate a list of search terms, depending on which was triggered.\n\nLatent-Dreamer also has a credits system to limit the amount of times people can trigger her per day.\nMore information about the credits system can be found [here](<https://discord.com/channels/958392331671830579/958392332590387262/1110078862286671962>) or by pinging Latent-Dreamer with the word 'credits'.")

    
    
    ######################################################################################################################################################
    ##### HOURLY LOOP ####################################################################################################################################
    ######################################################################################################################################################

    @tasks.loop(
        minutes = 60
    )
    async def hourly_loop(self):
        print("Hourly loop triggered at {}.".format(datetime.datetime.now()))

        ### REMINDERS ###

        bst_time = u_bread.bread_time().total_seconds() // 3600

        reminder_data = database.load("reminders")
        reminder_channel = None

        for reminder in reminder_data["reminder_list"]:
            if reminder["hour"] != bst_time:
                continue
            
            if reminder_channel is None:
                reminder_channel = await self.bot.fetch_channel(REMINDERS_CHANNEL)

            embed = u_interface.embed(
                title = "You had a reminder set for now!",
                description = reminder["text"]
            )
            await reminder_channel.send(content="<@{}>".format(reminder["user"]), embed=embed)
        
        ### XKCD PINGLIST ###
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://xkcd.com/info.0.json") as resp:
                if resp.status != 200:
                    return
                
                return_json = await resp.json()
        
        ping_list_data = database.load("ping_lists")

        if return_json["num"] > ping_list_data["xkcd_previous"]:
            ping_list_channel = await self.bot.fetch_channel(PING_LISTS_CHANNEL)

            embed = u_interface.embed(
                title = "{}: {}".format(return_json["num"], return_json["safe_title"]),
                title_link = "https://xkcd.com/{}/".format(return_json["num"]),
                image_link = return_json["img"],
                footer_text = return_json["alt"]
            )
            content = "New xkcd strip!!\n\nPinglist:\n{}\nUse `%xkcd ping` to add or remove yourself from the pinglist.".format("".join([f"<@{str(item)}>" for item in ping_list_data["xkcd_strips"]]))

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

        # Running _hourly_task in other cogs.
        for cog in self.bot.cogs.values():
            if cog.__cog_name__ == self.__cog_name__:
                continue

            try:
                await cog._hourly_task()
            except AttributeError:
                pass


    @hourly_loop.before_loop
    async def hourly_setup(self):
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
    async def daily_loop(self):
        print("Daily loop triggered at {}".format(datetime.datetime.now()))

        hour_offset = 5 # The number of hours to subract from the current unix timestamp.
        day_of_the_week = ((int(time.time()) - (hour_offset * 3600)) // 86400 + 4) % 7
        weekly_board = day_of_the_week == 0

        # Archive daily board and the weekly board if it's Monday.
        live_data = u_bingo.live(database=database)

        archive_5x5 = database.load("bingo", "previous_5x5_boards")

        archive_5x5[str(live_data["daily_board_id"])] = {
            "tile_string": live_data["daily_tile_string"],
            "enabled": live_data["daily_enabled"]
        }

        database.save("bingo", "previous_5x5_boards", data=archive_5x5)

        # If it's the day of the weekly board then archive it since we'll be making a new one.
        if weekly_board:
            archive_9x9 = database.load("bingo", "previous_9x9_boards")

            archive_9x9[str(live_data["weekly_board_id"])] = {
                "tile_string": live_data["weekly_tile_string"],
                "enabled": live_data["weekly_enabled"]
            }

            database.save("bingo", "previous_9x9_boards", data=archive_9x9)

        # Now, make new boards.

        new_daily = u_bingo.generate_5x5_board(database=database)

        live_data["daily_tile_string"] = new_daily
        live_data["daily_enabled"] = 0
        live_data["daily_board_id"] += 1

        if weekly_board:
            new_weekly = u_bingo.generate_9x9_board(database=database)

            live_data["weekly_tile_string"] = new_weekly
            live_data["weekly_enabled"] = 0
            live_data["weekly_board_id"] += 1
        
        u_bingo.update_live(database=database, new_data=live_data)
        self.bot.update_bingo_cache(live_data)

        # Send the daily board to the daily board channel.
        daily_channel = await self.bot.fetch_channel(DAILY_BOARD_CHANNEL)
        u_images.render_full_5x5(
            database = database,
            tile_string = new_daily,
            enabled = 0
        )

        await daily_channel.send("Bingo Board #{}!\nThe wiki:\n<https://bread.miraheze.org/wiki/The_Bread_Game_Wiki>".format(live_data["daily_board_id"]), file=discord.File(r'images/generated/bingo_board.png'))
        
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

        # Running _daily_task in other cogs.
        for cog in self.bot.cogs.values():
            if cog.__cog_name__ == self.__cog_name__:
                continue

            try:
                await cog._daily_task()
            except AttributeError:
                pass




    
    
    ######################################################################################################################################################
    ##### ON EVENTS ######################################################################################################################################
    ######################################################################################################################################################
        
    async def on_stonk_tick(self, message: discord.Message):
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

        await message.reply("{}\n\nCopy of tick {}:\n\n{}".format(
            "".join(["<@{}>".format(user_id) for user_id in stonk_pinglist]),
                new["tick_number"],
                message.content
            ),
            file = send_file
        )
        
        # Save the database to file.
        database.save_database(make_backup=True)

        # Running _on_stonk_tick in other cogs.
        for cog in self.bot.cogs.values():
            if cog.__cog_name__ == self.__cog_name__:
                continue

            try:
                await cog._on_stonk_tick(message)
            except AttributeError:
                pass

        
    
    async def chains(self, message: discord.Message):
        if u_checks.sensitive_check(message.channel):
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
                await message.add_reaction("<a:you_broke_the_chain:1064256620617535538>")
            return
        
        if channel_data["sender"] == message.author.id:
            # So someone can't go twice in a row.
            return
        
        if message.author.bot:
            # Accounts with bot tags shouldn't be able to contribute to the chains, but can still break it.
            return

        self._update_channel_chain(
            channel_id = message.channel.id,
            data = {
                "message": message.content,
                "sender": message.author.id,
                "count": channel_data["count"] + 1
            }
        )
        



        
    async def on_gamble(self, message: discord.Message):
        # Gamble messages.
        gamble_messages = database.load("bread", "gamble_messages")

        gamble_messages[f"{message.channel.id}.{message.id}"] = message.content

        if len(gamble_messages) > 500:
            gamble_messages.pop(next(iter(gamble_messages)))
        
        database.save("bread", "gamble_messages", data=gamble_messages)
    
    async def ask_ouija(self, message: discord.Message):
        if u_checks.sensitive_check(message.channel):
            return
        
        ouija_data = database.get_ouija_data(message.channel.id)

        if not ouija_data["active"]:
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

        database.set_ouija_data(message.channel.id, letters = "{}{}".format(ouija_data["letters"], content))
    
    async def counting(self, message: discord.Message):
        if u_checks.sensitive_check(message.channel):
            return
        
        sent_number = u_converters.parse_int(message.content)

        counting_data = database.get_counting_data(message.channel.id)

        if sent_number <= counting_data["count"]:
            return

        if sent_number > counting_data["count"] + 1:
            if counting_data["count"] == 0: # If 1 hasn't been sent since the last break.
                return
            
            counting_data.set_counting_data(
                channel_id = message.channel.id,
                count = 0,
                sender = 0
            )
            embed = u_interface.embed(
                title = "You broke the counting!",
                description = "The counting was broken at **{}** by {}!\nYou must restart at 1.\nGet ready for the brick <:trol:1015821884450947173>".format(
                    u_text.smart_number(counting_data["count"]),
                    message.author.mention
                )
            )
            try:
                await message.add_reaction("<a:you_cant_count:1134902783095603300>")
                await u_interface.smart_reply(message, embed=embed)
            except discord.errors.Forbidden:
                database.set_counting_data(channel_id = message.channel.id, count = counting_data["count"], sender = counting_data["sender"])
            
            return
        
        if message.author.id == counting_data["sender"]:
            return # So someone can't go twice in a row.
        
        database.set_counting_data(
            channel_id = message.channel.id,
            count = sent_number,
            sender = message.author.id
        )
        try:
            await message.add_reaction("<a:you_can_count:1133795506099867738>")
        except discord.errors.Forbidden:
            database.set_counting_data(channel_id = message.channel.id, count = counting_data["count"], sender = counting_data["sender"])
                
    async def pk_reply(self, message: discord.Message):
        if message.flags.silent:
            # If the message is a silent message.
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
    
    async def pk_explanation(self, message: discord.Message):
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
    
    async def brick_stats_correcting(self, message: discord.Message):
        if u_checks.serious_channel_check(message.channel):
            return
        
        split = message.content.split(" ")
        if len(split) <= 2:
            return
        
        user = split[2]
        user = discord.utils.find(lambda m: user in [m.name, m.display_name, m.global_name, m.mention, m.id, str(m)], message.guild.members)
        if user is not None:
            await message.reply(f"Do you mean `$brick {user.id} stats`?")

    async def seven_twenty_seven(self, message: discord.Message):
        if u_checks.serious_channel_check(message.channel):
            return
        
        content = message.content

        content = re.sub(r"<@&?\d+>", "", content)
        content = re.sub(r"<#\d+>", "", content)
        content = re.sub(r"<a?:\w+:\d+>", "", content)

        if "727" not in content:
            # 727 was in a ping, channel mention, or emoji.
            return
        
        if random.randint(1, 32) != 1:
            return
        
        # Now, fetch the users in the "727_pinglist" from the pinglist data and send a message pinging all of them.
        ping_data = database.get_ping_list("727_pinglist")

        await message.reply("".join([f"<@{user_id}>" for user_id in ping_data]), mention_author=False)
        return

            
            

    
    @commands.Cog.listener()
    async def on_message(self, message):
        # Make sure the bot doesn't read it's own messages.
        if message.author.id == self.bot.user.id:
            return
        
        # Just a note, while there's u_custom.CustomContext for context objects, there is no CustomMessage, so u_interface.smart_reply still needs to be used.

        # Chains.
        await self.chains(message)

        # Autodetection.

        # Stonk ticks.
        if u_interface.is_mm(message) and message.content.startswith("Current stonk values are as follows"):
            await self.on_stonk_tick(message)

        # PluralKit replies.
        if u_interface.is_reply(message):
            await self.pk_reply(message)
        
        # PluralKit explanation.
        await self.pk_explanation(message)

        # Counting
        if u_converters.is_digit(message.content):
            await self.counting(message)
        
        # AskOuija
        if len(message.content) == 1 or message.content.strip() == "** **" or message.content.lower() == "goodbye":
            await self.ask_ouija(message)

        # ???

        # Profit

        # On gamble.
        if u_interface.is_gamble(message):
            await self.on_gamble(message)
        
        # Gold brick reacting.
        if message.content == "<:brick_gold:971239215968944168>" and u_interface.is_mm(message) and not u_checks.sensitive_check(message.channel):
            await message.add_reaction("<:Pog:1029515439971258398>")
        
        # Brick stats correcting.
        if message.content.startswith("$brick stats"):
            await self.brick_stats_correcting(message)
        
        # 727 pings.
        if "727" in message.content:
            await self.seven_twenty_seven(message)




    
    
    ######################################################################################################################################################
    ##### ON REACTION ADD ################################################################################################################################
    ######################################################################################################################################################
            
    async def pk_explanation_deletion(self, payload: discord.RawReactionActionEvent):
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
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.event_type != "REACTION_ADD":
            return
        
        # PluralKit explanation deleting.
        if payload.emoji.name == "❌":
            await self.pk_explanation_deletion(payload)




    
    
    ######################################################################################################################################################
    ##### ON COMMAND ERROR ###############################################################################################################################
    ######################################################################################################################################################

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

        


async def setup(bot: commands.Bot):
    cog = Triggers_cog()
    cog.bot = bot

    global database
    database = bot.database
    
    # Add attributes for sys.modules and globals() so the _reload_module() function in utility.custom can read it and get the module objects.
    cog.modules = sys.modules
    cog.globals = globals()
    
    await bot.add_cog(cog)