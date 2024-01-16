from discord.ext import commands
from discord.ext import tasks
import discord
import datetime
import asyncio

import sys

import utility.files as u_files
import utility.interface as u_interface
import utility.custom as u_custom
import utility.text as u_text
import utility.converters as u_converters

bingo_time = datetime.time(
    hour = 23,
    minute = 0,
    tzinfo = datetime.timezone.utc
)

class Triggers_cog(u_custom.CustomCog, name="Triggers", description="Hey there! owo\n\nyou just lost the game >:3"):
    bot = None

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

    @hourly_loop.before_loop
    async def hourly_setup(self):
        # This just waits until it's time for the first iteration.
        print("Starting hourly loop, current time is {}.".format(datetime.datetime.now()))

        # Get current time.
        time = datetime.datetime.now()

        wait_time = 0

        if time.minute < 5:
            # wait until 5 minutes after the hour
            wait_time = max(5 - time.minute, 0)

        elif time.minute > 5:
            # wait into next hour
            wait_time = max(65 - time.minute, 0)
            # print(f"waiting before bread loop for {wait_time} minutes")
            # await asyncio.sleep(60*wait_time)
            # print(time.strftime("Finished waiting at %H:%M:%S"))

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
        
    async def on_gamble(self, message: discord.Message):
        # Gamble messages.
        gamble_messages = u_files.load("data/bread/gamble_messages.json")

        gamble_messages[f"{message.channel.id}.{message.id}"] = message.content

        if len(gamble_messages) > 500:
            gamble_messages.pop(next(iter(gamble_messages)))
        
        u_files.save("data/bread/gamble_messages.json", gamble_messages)
    
    async def ask_ouija(self, message: discord.Message):
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
        sent_number = u_converters.parse_int(message.content)

        counting_data = u_files.get_counting_data(message.channel.id)

        if sent_number > counting_data["count"]:
            if sent_number > counting_data["count"] + 1:
                if counting_data["sender"] == 0: # If 1 hasn't been sent since the last break.
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
                


            
            

    
    @commands.Cog.listener()
    async def on_message(self, message):
        # Just a note, while there's u_custom.CustomContext for context objects, there is no CustomMessage, so u_interface.smart_reply still needs to be used.

        # Autodetection.

        # PluralKit replies.

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
    

async def setup(bot: commands.Bot):
    cog = Triggers_cog()
    cog.bot = bot
    
    # Add attributes for sys.modules and globals() so the _reload_module() function in utility.custom can read it and get the module objects.
    cog.modules = sys.modules
    cog.globals = globals()
    
    await bot.add_cog(cog)