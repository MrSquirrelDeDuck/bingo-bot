import discord
from discord.ext import commands

# pip install python-dotenv
import dotenv
import os

import utility.custom as u_custom
import utility.files as u_files

dotenv.load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
COMMAND_PREFIX = os.getenv('COMMAND_PREFIX')
OWNER_ID = int(os.getenv('OWNER_ID'))

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
intents.reactions = True


bot = u_custom.CustomBot(
    command_prefix = COMMAND_PREFIX,
    intents = intents, 
    owner_id = OWNER_ID,
    help_command = u_custom.CustomHelpCommand()
)

@bot.event
async def on_ready():
    print("on_ready() called.")

    # Save the database, this is assuming on_ready() was called twice.
    try:
        bot.database.save_database(make_backup=True)
        print("Database saved.")
    except AttributeError:
        print("Setting up database.")
        bot.database = u_files.DatabaseInterface()
        print("Database setup complete.")


    print("Loading admin_cog.")

    try:
        await bot.load_extension("admin_cog")

        admin_cog = bot.get_cog("Admin")

        await admin_cog._load_all_extensions()
        admin_cog.add_checks()
    except commands.ExtensionAlreadyLoaded:
        pass
    except:
        raise

    print("admin_cog loaded.")

    print("Fully logged in as {}!".format(bot.user))
    print("\n##################################\n")


bot.run(TOKEN)