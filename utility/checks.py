"""Along with functions for permission checking, this has some checks that can be used with `@commands.check(checks.<function>)` if this file is loaded as checks via `import utility.checks as checks`."""

from os.path import sep as SLASH

import discord
from discord.ext import commands
import typing
import math

import utility.files as u_files
import utility.custom as u_custom

def get_permission(user_id: int, permission_name: str) -> bool:
    """Checks a permission via permissions.json."""

    # Load permission data.
    permission_data = u_files.load("data/misc/permissions.json", replace_slash=True)

    # Return a bool for if the user id is in the permissions.
    return user_id in permission_data.get(permission_name, [])

def has_role(member: discord.Member, role_list: typing.Union[list[str], list[int]]):
    """Checks if the member provided has any role with an id in the role_list list.
    Note that `role_list` should be a list of role ids, in either strings or integers."""

    role_list = [int(role) for role in role_list]

    for role in member.roles:
        if role.id in role_list:
            return True
    
    return False

def is_prime(number: int) -> bool:
    if number <= 1:
        return False
    
    for i in range(2, int(math.sqrt(number)) + 1):
        if number % i == 0:
            return False
    
    return True
    
def sensitive_check(channel: typing.Union[discord.TextChannel, discord.Thread]) -> bool:
    """Returns a boolean for whether a channel is a sensitive channel.
    
    Currently this includes:
    - #mental-health."""
    if isinstance(channel, discord.Thread):
        channel = channel.parent
        
    return channel.id in [969881291740811264]
    
def serious_channel_check(channel: typing.Union[discord.TextChannel, discord.Thread]) -> bool:
    """Returns a boolean for whether a channel is a serious channel.
    
    Currently this includes:
    - #mental-health.
    - #all-queer.
    - #100.
    - #conways-game-of-life-fan-club.
    - #wii-play-tanks."""
    if isinstance(channel, discord.Thread):
        channel = channel.parent
        
    return channel.id in [958562231921025054, 969881291740811264, 958487694676205628, 980267115821035550, 994460122875174942]

##### COMMAND CHECKS #####

async def in_authority(ctx: typing.Union[commands.Context, u_custom.CustomContext, discord.Member]) -> bool:
    """Returns a boolean for whether the author of the message (or a member provided) has Trusted or higher.
    This can be used as a check in a command with `@commands.check(checks.in_authority)` or as a standalone check in an if with `if await checks.in_authority(ctx):`"""

    try:
        member = ctx.author
    except:
        member = ctx

    return has_role(member, [970549665055522850, 1119445209923723396, 958512048306815056, 958755031820161025, 1179943096402837535])

def bingo_tick_check(ctx: typing.Union[commands.Context, u_custom.CustomContext]) -> bool:
    """Checks if the user has the permission required to tick and untick tiles on the bingo boards."""
    return get_permission(ctx.author.id, "bingo_tick")

def shutdown_check(ctx: typing.Union[commands.Context, u_custom.CustomContext]) -> bool:
    """Checks if the user has the 'shutdown' permission."""
    return get_permission(ctx.author.id, "shutdown")

def remote_say_check(ctx: typing.Union[commands.Context, u_custom.CustomContext]) -> bool:
    """Checks if the user has the 'remote_say' permission."""
    return get_permission(ctx.author.id, "remote_say")

async def hide_from_help(ctx: typing.Union[commands.Context, u_custom.CustomContext]) -> bool:
    """This returns False if the command being run is just `%help`, but returns True for command usage and if a subsection of the help command is used."""
    if ctx.invoked_with != "help":
        return True
    
    split = ctx.message.content.split(" ", 1)

    if len(split) == 1:
        return False
    
    if split[1] == "":
        return False
    
    return True