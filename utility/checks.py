"""Along with functions for permission checking, this has some checks that can be used with `@commands.check(checks.<function>)` if this file is loaded as checks via `import utility.checks as checks`."""

import discord

import utility.files as files

def get_permission(user_id: int, permission_name: str) -> bool:
    """Checks a permission via permissions.json."""

    # Load permission data.
    permission_data = files.load("data/permissions.json")

    # Return a bool for if the user id is in the permissions.
    return user_id in permission_data[permission_name]

async def bingo_tick_check(message: discord.Message) -> bool:
    """Checks if the user has the permission required to tick and untick tiles on the bingo boards."""
    
    if get_permission(message.author.id, "bingo_tick"):
        return True
    
    await message.reply("I am sorry, but you can't use this command.")
    return False