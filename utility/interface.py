"""Functions for interfacing with Discord and other web services, like wikis."""

import discord
from discord.ext import commands
import typing
import datetime
import asyncio
import time
import re
import aiohttp
import traceback

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

def gen_embed(
        title: str, title_link: str = None,
        color: str | tuple[int, int, int] = "#e91e63", # 15277667
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

def msg_content(ctx: commands.Context | u_custom.CustomContext) -> str:
    """Returns the message content from a context object, while removing commands.
    For example, a context object of the message `%objective search Hello, world!` would return `Hello, world!`"""
    return ((ctx.message.content).replace(str(ctx.command), "", 1).replace(ctx.bot.command_prefix, "", 1).lstrip(" "))

def get_display_name(member: discord.Member) -> str:
    """Returns the display name of a member.

    Args:
        member (discord.Member): The member.

    Returns:
        str: The member's display name.
    """
    return (member.global_name if (member.global_name is not None and member.name == member.display_name) else member.display_name)

async def smart_reply(
        ctx: commands.Context | u_custom.CustomContext,
        content: str = "",
        **kwargs
    ) -> discord.Message:
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

async def safe_reply(
        ctx: commands.Context | u_custom.CustomContext,
        content: str = "",
        **kwargs
    ) -> discord.Message:
    """Replies in a safe manner."""
    
    kwargs["allowed_mentions"] = everyone_prevention

    return await ctx.reply(content, **kwargs)

async def safe_send(
        ctx: commands.Context | u_custom.CustomContext,
        content: str = "",
        **kwargs
    ) -> discord.Message:
    """Sends a message in a safe manner."""

    kwargs["allowed_mentions"] = everyone_prevention
    
    try:
        return await ctx.send(content, **kwargs)
    except AttributeError: # If the context passed was a discord.Message object.
        return await ctx.channel.send(content, **kwargs)
    except:
        # Reraise any other exceptions.
        raise


def is_reply(
        message: discord.Message,
        *,
        allow_ping: bool = True
    ) -> bool:
    """Returns a boolean for whether the message provided is a reply.

    Args:
        message (discord.Message): The message to check.
        allow_ping (bool, optional): Whether to allow a ping at the start of an MM message to count. Defaults to True.

    Returns:
        bool: Whether the given message is a reply.
    """
    if is_mm(message) and "<@" in message.content and allow_ping:
        if re.match("<@\d+> ?\n\n", message.content):
            return True
        
    return message.reference is not None

def is_mm(message: discord.Message) -> bool:
    """Returns a boolean for whether the given message was sent by Machine-Mind, or a known Machine-Mind clone used for testing.

    Args:
        message (discord.Message): The message to check.

    Returns:
        bool: Whether the message was sent by Machine-Mind or a known Machine-Mind clone.
    """
    mm_ids = [960869046323134514, 1144833820940578847]

    return message.author.id in mm_ids

def mm_checks(
        message: discord.Message,
        check_reply: bool = False
    ) -> bool:
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

def replying_mm_checks(
        message: discord.Message,
        require_reply: bool = False,
        return_replied_to: bool = False
    ) -> bool | discord.Message:
    """Takes a message and checks whether it's replying to Machine-Mind (or a known clone.)
    If specified, it can also check whether Machine-Mind's message is also a reply.

    Args:
        message (discord.Message): The user message that will be checked.
        require_reply (bool, optional): Whether to check if Machine-Mind's messsage is also a reply. Defaults to False.
        return_replied_to (bool, optional): Whether to return the replied to message. Defaults to False.

    Returns:
        bool | discord.Message: Whether the checks passed, or the message if return_replied_to is True.
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

def is_bread_roll(message: discord.Message) -> bool:
    """Returns a boolean for whether the given message is a bread roll.
    
    Args:
        message (discord.Message): The message to check.
    
    Returns:
        bool: Whether the message is a bread roll.
    """
    if not mm_checks(message, check_reply = True):
        return False
    
    if is_gamble(message):
        return False
    
    content = remove_starting_ping(message.content)
    
    first_line = content.split("---")[0].split("\n")[0]
    per_line_count = len(re.findall("(<a?)?:[\d\w_]+:(\d+>)?", first_line))
    if per_line_count not in [5, 10]:
        return False



    content = content.replace(" ", "").replace("\n", "").replace("-", "")
    for item in u_values.rollable_items:
        content = content.replace(item.internal_emoji, "")
        content = content.replace(item.emoji, "")

    return len(content) == 0
    
def is_gamble(message: discord.Message | str) -> bool:
    """Returns a boolean for whether a message is a Bread Game gamble.

    Args:
        message (discord.Message): The message to check.

    Returns:
        bool: Whether the message is a gamble.
    """
    try:
        if not mm_checks(message, check_reply = True):
            return False
        
        content = message.content
    except AttributeError:
        content = message
    
    if any([content.endswith(_) for _ in ["?", "!", "."]]):
        return False
    
    content = remove_starting_ping(content)

    split = content.split("\n")

    if len(split) != 4:
        return False
    
    for item in split:
        if item.strip().count(" ") != 3:
            return False
    
    if content.count(" ") != 15:
        return False
    
    return True

def remove_starting_ping(content: str) -> str:
    """Removes a ping from the start of a message.

    Args:
        content (str): The message content.

    Returns:
        str: The message content with the ping removed.
    """
    if "<@" in content:
        content = re.sub(r"^<@\d+> ?\n\n", "", content)
    return content

def resolve_conflict(
        database: u_files.DatabaseInterface,
        ctx: commands.Context | u_custom.CustomContext,
        resolve_keys: list[str | typing.Type[u_values.Item]],
        command_provided: list[int | None]
    ) -> tuple[bool, ...]:
    """Resolves the conflict of user-provided parameters, the stats parser, or stored data.

    Args:
        database (u_files.DatabaseInterface): The database.
        ctx (commands.Context | u_custom.CustomContext): The context this is needed in.
        resolve_keys (list[str  |  typing.Type[u_values.Item]]): A list of keys to look for in the stats parser and stored data.
        command_provided (list[int | None]): The user-provided parameters. It's fine if this is just a list of None.

    Returns:
        tuple[bool, ...]: A tuple containing a boolean for whether stored data was used, following by the resolved data, in the order it is provided.
    """
    using_stored_data = False

    parsed_data = None
    stored_data = None

    def get_parsed():
        nonlocal parsed_data
        if parsed_data is None:
            replied = replying_mm_checks(
                message = ctx.message,
                require_reply = True,
                return_replied_to = True
            )

            if not replied:
                parsed_data = {}
                return parsed_data

            parsed_data = u_bread.parse_stats(replied)

            if parsed_data.get("parse_successful"):
                parsed_data = parsed_data.get("stats")
            else:
                parsed_data = {}

        return parsed_data

    def get_stored(database: u_files.DatabaseInterface) -> u_bread.BreadDataAccount:
        nonlocal stored_data, using_stored_data
        if stored_data is None:
            stored_data = u_bread.get_stored_data(
                database = database,
                user_id = ctx.author.id
            )
            using_stored_data = True
        return stored_data
    
    resolve = dict(zip(resolve_keys, command_provided))
    
    for stat in resolve:
        if resolve[stat] is None:
            if parsed_data is None:
                get_parsed()
            
            if stat in parsed_data:
                resolve[stat] = parsed_data[stat]
            else:
                resolve[stat] = get_stored(database).get(stat, 0)
    
    return (using_stored_data,) + tuple(resolve.values())

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

def snapshot_roles(guild: discord.Guild) -> None:
    """Loops through all the members in the given guild and writes dough the role ids for each member. It then saves all of this to a json file with the name of the current unix timestamp in 'data/role_snapshots/snapshots/'

    Args:
        guild (discord.Guild): Discord guild to get the role information for.
    """
    # Get the snapshot.
    out = get_role_list(guild)
    
    # Save the snapshot to file.
    snapshot_id = time.time()
    u_files.save("data", "role_snapshots", "snapshots", f"{snapshot_id}.json", data=out, join_file_path=True)

    # Updating the list of snapshots people were previously in.
    base = u_files.load("data", "role_snapshots", "last_snapshot.json", default={}, join_file_path=True)

    for member_id in out:
        base[str(member_id)] = str(snapshot_id)
    
    u_files.save("data", "role_snapshots", "last_snapshot.json", data=base, join_file_path=True)

async def refresh_status(
        bot: u_custom.CustomBot | commands.Bot,
        database: u_files.DatabaseInterface
    ):
    """Refreshes the status from the database.

    Args:
        bot (u_custom.CustomBot | commands.Bot): The bot object.
        database (u_files.DatabaseInterface): The database.
    """
    status_data = database.load("bot_status", default = None)

    if status_data is None:
        return
        
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

async def await_confirmation(
        bot: u_custom.CustomBot | commands.Bot,
        ctx: commands.Context | u_custom.CustomContext,
        message = "Are you sure you would like to proceed? y/n.",
        confirm: list[str] = ["y", "yes"], 
        cancel: list[str] = ["n", "no"],
        lower_response: bool = True
    ) -> bool:
    """Prompts a confirmation.

    Args:
        ctx (commands.Context | u_custom.CustomContext): The context object.
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

def wiki_correct_length(
        text: str,
        limit: int = 300
    ) -> str:
    """Corrects the length of a wikitext string, while, hopefully, keeping links intact."""

    period_location = text[:limit].rfind(".")
    addition = "".join([text, " "])

    if addition[period_location + 1] in [" ", "\\"]:
        return text[:period_location + 1]
    
    for char_id in range(len(text) - limit):
        if period_location + char_id >= 1000:
            break
        
        if addition[period_location + char_id] != ".":
            continue

        if addition[period_location + char_id + 1] not in [" ", "\\"]:
            continue
        
        return text[:period_location + char_id + 1]
    
    for char_id in range(limit):
        if period_location - char_id >= 1000:
            break

        if addition[period_location - char_id] != ".":
            continue

        if addition[period_location - char_id + 1] not in [" ", "\\"]:
            continue

        return text[:period_location - char_id + 1]
    
    text = text[:300]
    return text[:text.rfind(".") + 1]

async def handle_wiki_search(
        ctx: commands.Context | u_custom.CustomContext,
        *,
        wiki_name: str,
        wiki_link: str,
        wiki_main_page: str,
        wiki_api_url: str,
        search_term: str = None,
        manual_replacements: typing.Callable[[str], str] = None
    ) -> None:
    """Handles all the logic required for searching a wiki and sending results.

    Args:
        ctx (commands.Context | u_custom.CustomContext): The context object.
        wiki_name (str): The name of the wiki, like "The Bread Game Wiki"
        wiki_link (str): A link to the wiki without a specific page. Example: "https://bread.miraheze.org/wiki/"
        wiki_main_page (str): The main page of the wiki, like "https://bread.miraheze.org/wiki/Main_Page"
        wiki_api_url (str): The URL of the API for the wiki without any parameters, like "https://bread.miraheze.org/api.php"
        search_term (str, optional): The search term to search the wiki with. Defaults to None.
        manual_replacements (typing.Callable[[str], str], optional): A callable that will be called on the wikitext before it is parsed. It will be passed the wikitext and should return a modified copy of that text. Defaults to None.
    """
    if search_term is None:
        await ctx.reply("Here's a link to {wiki_name}:\n<{main_page}>\nIf you want to search {wiki_name}, use `%{command} <search term>`.".format(
            wiki_name=wiki_name,
            main_page=wiki_main_page,
            command=ctx.command.qualified_name
        ))
        return
    
    async def error_message(embed: discord.Embed, sent_message: discord.Message) -> None:
        """Changes all 'Waiting to be loaded' messages to 'Something went wrong'"""
        modified = 0

        for field_id, field in enumerate(embed.fields):
            if "Waiting to be loaded" not in field.value:
                continue
            
            embed.set_field_at(field_id, name=field.name, value=field.value.replace("Waiting to be loaded", "Something went wrong"), inline=field.inline)
            modified += 1
        
        if modified >= 1:
            await sent_message.edit(content=sent_message.content, embed=embed)
    
    embed = None
    sent_message = None

    try:

        async with aiohttp.ClientSession() as session:
            json_args = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": search_term,
                "srlimit": 3
            }
            async with session.get(wiki_api_url, params=json_args) as resp:
                if resp.status != 200:
                    await ctx.reply("Something went wrong.")
                    return
                
                ret_json = await resp.json()

            description_prefix = f"Search results after searching for '{search_term}' on [{wiki_name}]({wiki_main_page}):"
            
            if ret_json["query"]["searchinfo"]["totalhits"] == 0:
                embed = gen_embed(
                    title = wiki_name,
                    title_link = wiki_main_page,
                    description = f"{description_prefix}\n\nThe search did not find any results, try different search terms."
                )
                await ctx.reply(embed=embed)
                return
            
            search_results = []

            for page_info in ret_json["query"]["search"]:                    
                search_results.append(page_info["title"])

            fields = [
                (page_name, "[Link to wiki page.]({}{})\n\n*Waiting to be loaded.*".format(wiki_link, page_name.replace(" ", "_")), True)
                for page_name in search_results
            ]

            embed = gen_embed(
                title = wiki_name,
                title_link = wiki_main_page,
                description = f"{description_prefix}",
                fields = fields + [("", "Not what you're looking for? Try different search terms.", False)]
            )

            sent_message = await ctx.reply(embed=embed)


            json_args = {
                "action": "query",
                "prop": "revisions",
                "titles": "|".join(search_results),
                "rvslots": "*",
                "rvprop": "content",
                "formatversion": "2",
                "format": "json",
                "redirects": "true"
            }
            async with session.get(wiki_api_url, params=json_args) as resp:
                if resp.status != 200:
                    await ctx.reply("Something went wrong.")
                    return
                
                ret_json = await resp.json()

            wiki_data = {}
            for data in ret_json["query"]["pages"]:
                try:
                    wiki_data[data["title"]] = data["revisions"][0]["slots"]["main"]["content"]
                except KeyError:
                    wiki_data[data["title"]] = data["revisions"][0]["content"]

            redirect_data = {}
            if "redirects" in ret_json["query"]:
                for data in ret_json["query"]["redirects"]:
                    redirect_data[data["from"]] = {"to": data["to"], "fragment": data.get("tofragment", None)}

            for field_id, page in enumerate(search_results):
                page_get = page
                page_fragment = None

                redirect_text = ""
                
                for redirect_count in range(50):
                    if page_get in redirect_data:
                        page_fragment = redirect_data[page_get]["fragment"]
                        page_get = redirect_data[page_get]["to"]
                        redirect_text = f"*Redirected to {page_get}*\n"
                        continue
                    break

                if page_fragment is None:
                    page_fragment = page_get
                
                sections = u_text.parse_wikitext(
                    wikitext = wiki_data[page_get],
                    wiki_link = wiki_link,
                    page_title = page_get,
                    return_sections = True,
                    manual_replacements = manual_replacements
                )
                
                summary = "[Link to wiki page.]({}{})\n{}\n{}".format(wiki_link, page.replace(" ", "_"), redirect_text, sections[page_fragment])

                if len(summary) > 900:
                    summary = wiki_correct_length(summary, 900)

                embed.set_field_at(field_id, name=page, value=summary, inline=True)

            await sent_message.edit(content=sent_message.content, embed=embed)

    except:
        print(traceback.format_exc())

        if embed is not None and sent_message is not None:
            await error_message(embed, sent_message)

def remove_emojis(
        input_text: str,
        filler: str | None = None
    ) -> str:
    """Removes non-ascii emojis from a piece of text. This can have false positives.

    Args:
        input_text (str): The input text to remove emojis from.
        filler (str | None, optional): What to replace emojis with, None will use an empty string. Defaults to None.

    Returns:
        str: The input text, but with emojis removed.
    """
    if filler is None:
        filler = ""
    return re.sub("(<a?)?:[\d\w_]+:(\d+>)?", filler, input_text)