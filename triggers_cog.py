from discord.ext import commands
from discord.ext import tasks
import discord
import datetime
import asyncio

import sys
import importlib

import utility.files as u_files
import utility.interface as u_interface
import utility.custom as u_custom

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
    
    @commands.Cog.listener()
    async def on_message(self, message):
        # Autodetection.

        # PluralKit replies.

        # Counting
        
        # AskOuija

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