"""Functions for Discord related things."""

import discord
from discord.ext import commands
import typing
import datetime
import asyncio

import utility.values as u_values
import utility.text as u_text
import utility.bread as u_bread
import utility.custom as u_custom
import utility.files as u_files

everyone_prevention = discord.AllowedMentions(everyone=False)

import importlib

importlib.reload(u_values)
importlib.reload(u_text)
importlib.reload(u_bread)
importlib.reload(u_custom)

def embed(
        title: str, title_link: str = None,
        color: typing.Union[str, tuple[int, int, int]] = "#e91e63",
        description: str = None,
        author_name: str = None, author_link: str = None, author_icon: str = None,
        footer_text: str = None, footer_icon: str = None,
        image_link: str = None,
        thumbnail_link: str = None,
        fields: list[tuple[str, str, bool]] = None,
        timestamp: datetime.datetime = None
    ) -> discord.Embed:
    """Function for easy creation of embeds. The color can be provided as a hex code (with or without the hash symbol) or as RGB values.
    # Fields:
    Each field is a 3 item tuple as follows:
    1. Field name (256 characters)
    2. Field text (1024 characters)
    3. Whether the field should be inline (bool)
    The fields should be provided in the order you want to display them.
    # For adding images:
    https://discordpy.readthedocs.io/en/stable/faq.html#local-image"""

    if isinstance(color, str):
        color = int(color.replace("#", ""), 16)
    elif isinstance(color, tuple):
        color = int(f"{color[0]:02x}{color[1]:02x}{color[2]:02x}", 16)
    else:
        raise TypeError("Provided color must be a hex code or set of RBG values in a tuple.")
    
    embed = discord.Embed(
        color = color,
        title = title,
        url = title_link,
        description = description,
        timestamp = timestamp
    )

    if author_name is not None:
        embed.set_author(
            name = author_name,
            url = author_link,
            icon_url = author_icon
        )
    
    if footer_text is not None:
        embed.set_footer(
            text = footer_text,
            icon_url = footer_icon
        )
    
    if image_link is not None:
        embed.set_image(
            url = image_link
        )
    
    if thumbnail_link is not None:
        embed.set_thumbnail(
            url = thumbnail_link
        )
    
    if fields is not None:
        for field_title, field_text, field_inline in fields:
            embed.add_field(
                name = field_title,
                value = field_text,
                inline = field_inline
            )
    
    return embed

def msg_content(ctx: commands.Context) -> str:
    """Returns the message content from a context object, while removing commands.
    For example, a context object of the message `%objective search Hello, world!` would return `Hello, world!`"""
    return ((ctx.message.content).replace(str(ctx.command), "", 1).replace(ctx.bot.command_prefix, "", 1).lstrip(" "))

def combine_args(ctx: (commands.Context | str), args: (tuple | list), keep: int, ctx_is_content: bool = False) -> list[str]:
    """Combines args into a single arg using msg_content(), it will, however, keep the first x arguments as normal, and will not incorporate those into the joined arg. x is set with the keep parameter. 
    If ctx_is_content is set to true then the ctx argument will be treated as the content."""
    args = list(args)
    if ctx_is_content:
        content = ctx
    else:
        content = msg_content(ctx)

    if keep == 0: return content

    indexstart = content.find(args[keep - 1]) + len(args[keep - 1]) + 1
    while content[indexstart] in ['"', "'", " "] and not indexstart >= len(content):
        indexstart += 1
    if indexstart >= len(content):
        content == ""
    else:
        content = content[indexstart:]
    
    return [args[i] for i in range(keep)] + [content]

def get_display_name(member: discord.Member) -> str:
    return (member.global_name if (member.global_name is not None and member.name == member.display_name) else member.display_name)

def is_reply(message: discord.Message) -> bool:
    return message.reference is not None

async def smart_reply(ctx, content: str = "", **kwargs) -> discord.Message:
    """Attempts to reply, if there's an error it then tries to send it normally."""

    try:
        return await safe_reply(ctx, content, **kwargs)
    except discord.HTTPException:
        # If something went wrong replying.
        if kwargs.get("mention_author", True):
            return await safe_send(ctx, f"{ctx.author.mention},\n\n{content}", **kwargs)
        else:
            return await safe_send(ctx, f"{u_text.ping_filter(get_display_name(ctx.author))},\n\n{content}", **kwargs)
    except:
        # For other errors, this will fire and reraise the exception.
        raise

async def safe_reply(ctx, content: str = "", **kwargs) -> discord.Message:
    """Replies in a safe manner."""
    
    kwargs["allowed_mentions"] = everyone_prevention

    return await ctx.reply(content, **kwargs)

async def safe_send(ctx, content: str = "", **kwargs) -> discord.Message:
    """Sends a message in a safe manner."""

    kwargs["allowed_mentions"] = everyone_prevention
    
    try:
        return await ctx.send(content, **kwargs)
    except AttributeError: # If the context passed was a discord.Message object.
        return await ctx.channel.send(content, **kwargs)
    except:
        # Reraise any other exceptions.
        raise


def is_reply(message: discord.Message) -> bool:
    """Returns a boolean for whether the message provided is a reply.

    Args:
        message (discord.Message): The message to check.

    Returns:
        bool: Whether the given message is a reply.
    """
    return message.reference is not None

def is_mm(message: discord.Message) -> bool:
    """Returns a boolean for whether the given message was sent by Machine-Mind, or a known Machine-Mind clone used for testing.

    Args:
        message (discord.Message): The message to check.

    Returns:
        bool: Whether the message was sent by Machine-Mind or a known Machine-Mind clone.
    """
    mm_ids = [960869046323134514, 1144833820940578847, 658290426435862619]

    return message.author.id in mm_ids

def mm_checks(message: discord.Message, check_reply: bool = False) -> bool:
    """Checks whether a message was sent by Machine-Mind (or a known clone) and, if specified, will check whether the message is a reply.

    Args:
        message (discord.Message): The message to check.
        check_reply (bool, optional): Whether to require the given message to be a reply. Defaults to False.

    Returns:
        bool: Whether the checks passed.
    """
    if not is_mm(message):
        return False
    
    if check_reply and not is_reply(message):
        return False
    
    return True

def replying_mm_checks(message: discord.Message, require_reply: bool = False, return_replied_to: bool = False) -> typing.Union[bool, discord.Message]:
    """Takes a message and checks whether it's replying to Machine-Mind (or a known clone.)
    If specified, it can also check whether Machine-Mind's message is also a reply.

    Args:
        message (discord.Message): The user message that will be checked.
        require_reply (bool, optional): Whether to check if Machine-Mind's messsage is also a reply. Defaults to False.
        return_replied_to (bool, optional): Whether to return the replied to message. Defaults to False.

    Returns:
        bool: Whether the checks passed.
    """
    
    # If the user message is not a reply, it's not what we're looking for.
    if not is_reply(message):
        return False
    
    replied_to = message.reference.resolved

    # If the replied to message is not MM, we know it failed the checks.
    if not is_mm(replied_to):
        return False
    
    # If require_reply is True and the replied-to message is not a reply, then it fails the checks.
    if require_reply and not is_reply(replied_to):
        return False
    
    # If return_replied_to is True, then return the message that was replied to.
    if return_replied_to:
        return replied_to
    
    # If it gets here, all the checks have passed.
    return True
    
def is_gamble(message: discord.Message) -> bool:
    """Returns a boolean for whether a message is a Bread Game gamble.

    Args:
        message (discord.Message): The message to check.

    Returns:
        bool: Whether the message is a gamble.
    """

    if not mm_checks(message, check_reply = True):
        return False
    
    if any([message.content.endswith(_) for _ in ["?", "!", "."]]):
        return False
    
    if message.content.count(" ") + message.content.count("\n") != 18:
        return False
    
    return True

def resolve_conflict(message: discord.Message, stats_type: str, user_provided: list[typing.Any], stat_keys: list[u_values.Item | u_values.ChessItem | u_values.StonkItem | str]) -> typing.Union[list[typing.Any], bool]:
    """
    Resolves conflicts between user-provided input and the stats parser.
    The method behind this is very simple, if it's provided by the user, use it, otherwise use the output from the stats parser.

    Args:
        message (discord.Message): The user's message.
        stats_type (str): The type of stats to look for. A list of acceptable ones are in the parse_stats() in utility.bread.
        user_provided (list[typing.Any]): A list of the user-provided values, where None is unprovided.
        stat_keys (list[u_values.Item  |  u_values.ChessItem  |  u_values.StonkItem  |  str]): A list of keys to look for in the parsed stats, in the same order as user_provided.

    Returns:
        typing.Union[list[typing.Any], bool]: The list of resolved values, or False if it failed.
    """

    if None not in user_provided:
        return user_provided
    
    replied_to = replying_mm_checks(message, require_reply=True, return_replied_to=True)

    if not replied_to:
        return False
    
    parsed = u_bread.parse_stats(replied_to)

    if parsed.get("stats_type") != stats_type: # If the parse was unsuccessful, then the .get will be None.
        return False
    
    parsed = parsed["stats"]

    for index, item in enumerate(user_provided):
        if item is not None:
            continue

        user_provided[index] = parsed.get(stat_keys[index], 0)
    
    if None in user_provided:
        return False
    
    return user_provided

def get_role_list(guild: discord.Guild) -> dict[str, list[int]]:
    """Generates a list of member ids, each with a list of the roles they have.

    Args:
        guild (discord.Guild): The guild to get the role list for.

    Returns:
        dict[str, list[int]]: The determined data.
    """
    out = {}
    for member in guild.members:
        data = [role.id for role in member.roles]
        out[member.id] = data
    
    return out

async def refresh_status(bot: u_custom.CustomBot | commands.Bot, database: u_files.DatabaseInterface):
    """Refreshes the status from the database.

    Args:
        database (u_files.DatabaseInterface): The database.
    """
    status_data = database.load("bot_status")
        
    status_type = status_data["status_type"]
    status_text = status_data["status_text"]
    status_url = status_data["status_url"]

    await change_status(
        database = database,
        bot = bot,
        status_type = status_type,
        status_text = status_text,
        status_url = status_url
    )

async def change_status(
        bot: u_custom.CustomBot | commands.Bot,
        status_type: str,
        status_text: str,
        status_url: str = None,
        *, database: u_files.DatabaseInterface = None,
    ) -> None:
    """Changes the bot's status based on the provided strings.

    Args:
        bot (u_custom.CustomBot | commands.Bot): The bot.
        status_type (str): The type of status to change to: "playing", "watching", "streaming", "listening", "custom", "competing"
        status_text (str): The text of the status.
        status_url (str, optional): The url to use if the status type is "streaming". Defaults to None.
        database (u_files.DatabaseInterface, optional): The database to use. If nothing is provided it won't store the status to the database. Defaults to None.
    """
    activity_type = None

    if status_type == "playing":
        activity = discord.Game(name=status_text)
    elif status_type == "streaming":
        if "youtu.be" in status_url:
            status_url = "https://www.youtube.com/watch?v=" + status_url.split("youtu.be/")[1]

        activity = discord.Streaming(name=status_text, url=status_url)
    elif status_type == "listening":
        activity_type = discord.ActivityType.listening
    elif status_type == "competing":
        activity_type = discord.ActivityType.competing
    elif status_type == "watching":
        activity_type = discord.ActivityType.watching
    elif status_type == "custom":
        activity = discord.CustomActivity(name=status_text)
    
    if activity_type is not None:
        activity = discord.Activity(type=activity_type, name=status_text)
    
    if database is not None:
        database.save("bot_status", data={"status_type": status_type, "status_text": status_text, "status_url": status_url})
    
    await bot.change_presence(activity=activity)

async def await_confirmation(bot: u_custom.CustomBot | commands.Bot, ctx: typing.Union[commands.Context, u_custom.CustomContext],
        message = "Are you sure you would like to proceed? y/n.",
        confirm: list[str] = ["y", "yes"], 
        cancel: list[str] = ["n", "no"],
        lower_response: bool = True
    ) -> bool:
    """Prompts a confirmation.

    Args:
        ctx (typing.Union[commands.Context, u_custom.CustomContext]): The context object.
        message (str, optional): The message to prompt with. Defaults to "Are you sure you would like to proceed? y/n.".
        confirm (list[str], optional): A list of strings that will be accepted. Defaults to ["y", "yes"].
        cancel (list[str], optional): A list of strings that will cancel. Defaults to ["n", "no"].
        lower_response (bool, optional): Whether to make the response lower case before checking it against the `confirm` and `cancel` lists. Defaults to True.

    Returns:
        bool: Whether the prompt was accepted.
    """

    def check(m: discord.Message):
        return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id 
    
    await ctx.reply(message)
    try:
        msg = await bot.wait_for('message', check = check, timeout = 60.0)
    except asyncio.TimeoutError: 
        # No message was sent by the person running the command in a minute, so just cancel it.
        await ctx.reply(f"Timed out.")
        return False
    
    response = msg.content

    if lower_response:
        response = response.lower()

    if response in confirm:
        await ctx.reply("Proceeding.")
        return True
    elif response in cancel:
        await ctx.reply("Cancelled.")
        return False
    else:
        await ctx.reply("Unknown response, cancelled.")
        return False