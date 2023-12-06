from discord.ext import commands
from discord.ext import tasks
import datetime
import asyncio

import sys
import importlib

bingo_time = datetime.time(
    hour = 23,
    minute = 0,
    tzinfo = datetime.timezone.utc
)

class Loop_cog(commands.Cog, name="Loop"):
    bot = None

    def __init__(self) -> None:
        super().__init__()
        self.hourly_loop.start()
        self.daily_loop.start()
    
    def cog_unload(self):
        self.hourly_loop.cancel()
        self.daily_loop.cancel()

    ###########################
    ##### ADMIN FUNCTIONS #####
    ###########################
    
    def _reload_module(self, module_name: str) -> bool:
        """Reloads a module by name.
        For imports that are in a folder, the folder name must be included. For instance: `utility.files` would reload the utility.files code.
        Returns a bool for whether anything was reloaded, so the number of reloads can be counted."""

        # Get a list of the names of every module in globals(). This can be done with a list comprehension but this is easier to read.
        globals_modules = []

        for module in globals().values():
            if hasattr(module, "__name__"):
                globals_modules.append(module.__name__)
        
        # Get a list of every imported module via cross-checking globals_modules and sys.modules.
        all_modules = set(sys.modules) & set(globals_modules)

        # If the provided module name 
        if module_name not in all_modules:
            return False
        
        # Get the module object.
        module = sys.modules[module_name]

        # Reload the module via importlib.reload.
        importlib.reload(module)
        print("- {} has reloaded {}.".format(self.qualified_name, module_name))

        # Return True, since it has been reloaded in theory.
        return True
    
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
    
    #######################
    ###### DAILY LOOP #####
    #######################

    @tasks.loop(
        time = bingo_time
    )
    async def daily_loop(self):
        print("Daily loop triggered at {}".format(datetime.datetime.now()))
    
    

async def setup(bot: commands.Bot):
    cog = Loop_cog()
    cog.bot = bot
    
    await bot.add_cog(cog)