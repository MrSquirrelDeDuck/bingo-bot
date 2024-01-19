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

class Triggers_cog(u_custom.CustomCog, name="Triggers", description="Hey there! owo\n\nyou just lost the game >:3"):
    bot = None

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
    
    ###########################
    ###########################
    ###########################

    #######################
    ##### HOURLY LOOP #####
    #######################

    @tasks.loop(
        minutes = 60
    )
    async def hourly_loop(self):
        print("Hourly loop triggered at {}.".format(datetime.datetime.now()))

        ### REMINDERS ###

        bst_time = u_bread.bread_time().total_seconds() // 3600

        reminder_data = u_files.load("data/reminders.json")
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
        
        ping_list_data = u_files.load("data/ping_lists.json")

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
            u_files.save("data/ping_lists.json", ping_list_data)

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


    @hourly_loop.before_loop
    async def hourly_setup(self):
        # This just waits until it's time for the first iteration.
        print("Starting hourly loop, current time is {}.".format(datetime.datetime.now()))

        # Get current time.
        time = datetime.datetime.now()

        wait_time = 0

        if time.minute < 5:
            wait_time = max(5 - time.minute, 0)

        elif time.minute > 5:
            wait_time = max(65 - time.minute, 0)

        print("Waiting to start hourly loop for {} minutes.".format(wait_time))
        await asyncio.sleep(60*wait_time)
        print("Finished waiting at {}.".format(datetime.datetime.now()))
    
    ######################
    ##### DAILY LOOP #####
    ######################

    @tasks.loop(
        time = bingo_time
    )
    async def daily_loop(self):
        print("Daily loop triggered at {}".format(datetime.datetime.now()))
    
    ###########################
    ###########################
    ###########################
    
    #####################
    ##### ON EVENTS #####
    #####################
        
    async def on_stonk_tick(self, message: discord.Message):
        if message.content[-1] in "!.?":
            return
        
        stonk_values = u_stonks.parse_stonk_tick(message)

        ### Updating stonk history. ###
        stonk_history = u_stonks.stonk_history()

        append = {
            stonk.internal_name: values[-1]
            for stonk, values in stonk_values.items()
        }

        stonk_history.append(append)
        
        u_files.save("data/stonks/stonk_history.json", stonk_history)

        ### Updating current values. ###
        new = {
            "message_link": message.jump_url,
            "tick_number": len(stonk_history) - 1,
            "values": append
        }

        u_files.save("data/stonks/current_values.json", new)
        
        ### Running the stonk algorithms. ###

        u_algorithms.run_all_algorithms()

        ### Attempt to generate the stonk report. ###

        send_file = None
        try:
            u_images.stonk_report()
            send_file = discord.File("images/generated/stonk_report.png")
        except:
            # Something went wrong :(
            print(traceback.format_exc())

        ### Send message. ###

        stonk_pinglist = u_files.get_ping_list("stonk_tick_pings")

        await message.reply("{}\n\nCopy of tick {}:\n\n{}".format(
            "".join(["<@{}>".format(user_id) for user_id in stonk_pinglist]),
                new["tick_number"],
                message.content
            ),
            file = send_file
        )

        


        
    async def on_gamble(self, message: discord.Message):
        # Gamble messages.
        gamble_messages = u_files.load("data/bread/gamble_messages.json")

        gamble_messages[f"{message.channel.id}.{message.id}"] = message.content

        if len(gamble_messages) > 500:
            gamble_messages.pop(next(iter(gamble_messages)))
        
        u_files.save("data/bread/gamble_messages.json", gamble_messages)
    
    async def ask_ouija(self, message: discord.Message):
        if u_checks.sensitive_check(message.channel):
            return
        
        ouija_data = u_files.get_ouija_data(message.channel.id)

        if not ouija_data["active"]:
            return
        
        if message.content.lower() == "goodbye":
            u_files.set_ouija_data(message.channel.id, active = False)

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

        u_files.set_ouija_data(message.channel.id, letters = "{}{}".format(ouija_data["letters"], content))
    
    async def counting(self, message: discord.Message):
        if u_checks.sensitive_check(message.channel):
            return
        
        sent_number = u_converters.parse_int(message.content)

        counting_data = u_files.get_counting_data(message.channel.id)

        if sent_number > counting_data["count"]:
            if sent_number > counting_data["count"] + 1:
                if counting_data["count"] == 0: # If 1 hasn't been sent since the last break.
                    return
                
                u_files.set_counting_data(
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
                    u_files.set_counting_data(channel_id = message.channel.id, count = counting_data["count"], sender = counting_data["sender"])
                
                return
            
            if message.author.id == counting_data["sender"]:
                return # So someone can't go twice in a row.
            
            u_files.set_counting_data(
                channel_id = message.channel.id,
                count = sent_number,
                sender = message.author.id
            )
            try:
                await message.add_reaction("<a:you_can_count:1133795506099867738>")
            except discord.errors.Forbidden:
                u_files.set_counting_data(channel_id = message.channel.id, count = counting_data["count"], sender = counting_data["sender"])
                
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

        input_modify = " {} ".format(str(message.content).lower().replace('"', "").replace("'", ""))

        if not(any([trigger in input_modify for trigger in self.pk_triggers])):
            return
        
        text = "On the server, you might see some users that appear to be talking with a bot tag. However, unless they have a color role (e.g. <@&960885443153522691>, <@&1032864473700122687>, <@&966569150468210723>, <@&973840335841140769>), they are not bots. They are using <@466378653216014359>, an integration that allows them to talk under different profiles, each with a custom name and profile picture, while using the same account. This is useful for multiple people sharing one body, aka systems, who want to be differentiated from one another when using their discord account. Even though they show up with a bot tag, again, **they are not bots**. Please refrain from referring to them as bots, or joking about it.\n\nMore information on plurality can be found here:\n<https://morethanone.info/>\n\n*This was triggered automatically by something you said. If I misinterpreted the context and this relates to the bot Latent-Dreamer, run `%ld` for an explanation. If I misinterpreted the context, it was not relating to Latent-Dreamer and this makes no sense, feel free to ignore this, or ping my creator to let them know.*"
        
        if time.time() - self.last_pk_trigger < 60:
            text = text.replace(
                "<@&960885443153522691>", "<@960869046323134514>"
            ).replace(
                "<@&1032864473700122687>", "<@1029793702136254584>"
            ).replace(
                "<@&966569150468210723>", "<@966474721619238972>"
            ).replace(
                "<@&973840335841140769>", "<@973811353036927047>"
            )
            await message.author.send(text)
            return
        
        self.last_pk_trigger = time.time()
        await message.reply(text)
    
    async def brick_stats_correcting(self, message: discord.Message):
        if u_checks.sensitive_check(message.channel):
            return
        
        split = message.content.split(" ")
        if len(split) <= 2:
            return
        
        user = split[2]
        user = discord.utils.find(lambda m: user in [m.name, m.display_name, m.global_name, m.mention, m.id, str(m)], message.guild.members)
        if user is not None:
            await message.reply(f"Do you mean `$brick {user.id} stats`?")

    async def seven_twenty_seven(self, message: discord.Message):
        if u_checks.sensitive_check(message.channel):
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
        ping_data = u_files.get_ping_list("727_pinglist")

        await message.reply("".join([f"<@{user_id}>" for user_id in ping_data]), mention_author=False)
        return

            
            

    
    @commands.Cog.listener()
    async def on_message(self, message):
        # Make sure the bot doesn't read it's own messages.
        if message.author.id == self.bot.user.id:
            return
        
        # Just a note, while there's u_custom.CustomContext for context objects, there is no CustomMessage, so u_interface.smart_reply still needs to be used.

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
    

async def setup(bot: commands.Bot):
    cog = Triggers_cog()
    cog.bot = bot
    
    # Add attributes for sys.modules and globals() so the _reload_module() function in utility.custom can read it and get the module objects.
    cog.modules = sys.modules
    cog.globals = globals()
    
    await bot.add_cog(cog)