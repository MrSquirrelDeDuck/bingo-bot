from discord.ext import commands
from discord.ext import tasks
import datetime
import asyncio
import zoneinfo 

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