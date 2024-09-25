"""Functions for working with/formatting text."""

from __future__ import annotations

from discord.ext import commands
import typing
import re
import datetime
import decimal

import utility.interface as u_interface
import utility.converters as u_converters
import utility.custom as u_custom

T = typing.TypeVar('T')

def rreplace(
        string: str,
        old: str,
        new: str,
        amount: int = -1
    ) -> str:
    """Replaces in a string, from right to left.

    Args:
        string (str): The string to run the code on.
        old (str): The old text.
        new (str): The text to replace the old text with.
        amount (int, optional): The max number of replacements, -1 is infinite. Defaults to -1.

    Returns:
        str: _description_
    """
    return new.join(string.rsplit(old, amount))

def smart_number(number: int) -> str:
    """Inserts commas into a number in order to make it easier to read.

    Args:
        number (int): The number to use.

    Returns:
        str: The number with commas.
    """
    return f'{number:,}'

def word_plural(
        text: str,
        number: int
    ) -> str:
    """Returns the provided text, with an "s" added at the end if the number is not 1.

    Args:
        text (str): The text to potentially add the "s" to.
        number (int): The number to check against.

    Returns:
        str: The text with an "s" added at the end if the number is not 1.
    """
    return f"{text}{'s' if number != 1 else ''}"

def smart_text(
        number: int,
        text: str
    ) -> str:
    """Combines smart_number() and word_plural() into one function. Will add a space between the number and text.

    Args:
        number (int): The number to use.
        text (str): The text to put at the end.

    Returns:
        str: The formatted number with commas, and then the text with an "s" at the end if the number isn't 1.
    """
    return f"{smart_number(number)} {word_plural(text, number)}"

def split_chunks(
        text: str,
        chunk_length: int
    ) -> list[str]:
    """Splits a string into chunks of equal length.

    Args:
        text (str): The string to split.
        chunk_length (int): The length of each chunk.

    Returns:
        list[str]: The input string, split into chunks.
    """
    return [text[i:i + chunk_length] for i in range(0, len(text), chunk_length)]

def ping_filter(text: str) -> str:
    """Uses re.sub to put an invisible character after the @ symbol in pings.
    
    Args:
        text (str): The text to filter.

    Returns:
        str: The filtered text.
    """
    text = re.sub("<@(&?\d+>)", "<@\u200b\\1", text)
    text = re.sub("@(everyone|here)", "@\u200b\\1", text)
    return text

def backtick_filter(text: str) -> str:
    """Puts invisible characters after backticks.

    Args:
        text (str): The text to filter.

    Returns:
        str: The filtered text.
    """
    return text.replace("`", "`\u200b")

def has_ping(text: str) -> bool:
    """Uses RegEx to check if a piece of text contains a ping.

    Args:
        text (str): The text to check.

    Returns:
        bool: Whether the text contains a ping.
    """
    return re.search("<@&?\d+>|@(everyone|here)", text) is not None

def after_parameter(
        ctx: commands.Context | u_custom.CustomContext,
        parameter_text: str
    ) -> str:
    """Returns all the text after a parameter.

    If possible, using `arg1, *, arg2` for command parameters is better.

    Args:
        ctx (commands.Context): The context object.
        parameter_text (str): The parameter text to get the text after.

    Returns:
        str: The text after the parameter.
    """
    return u_interface.msg_content(ctx).split(str(parameter_text), 1)[-1].lstrip('"\'').strip()

def return_numeric(
        text: str,
        return_type: typing.Any = None
    ) -> typing.Union[T, int]:
    """Returns just all the nubmer in a string as an integer, ignoring all other characters.

    Args:
        text (str): The string to get the numbers from.
        return_type (typing.Any, optional): The type to return. If nothing or None is passed it will convert to an integer before returning. Defaults to None.

    Returns:
        Any, int: An integer of all the numbers in the string. However, if return_type is passed, it will be converted to the type passed to return_type.
    """
    out = "".join([i for i in str(text) if i.isdigit()])
    
    if return_type is None:
        return int(out)
    
    return return_type(out)

def return_alphanumeric(text: str) -> str:
    """Returns just all the letters, numbers, spaces, dashes, and underscores in a string, ignoring all other characters.

    Args:
        text (str): The text to filter.

    Returns:
        str: The filtered text.
    """
    character_filter = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLNOPQRSTUVWXYZ0123456789-_ "
    return "".join([i for i in str(text) if i in character_filter])

def extract_chess_moves(text: str) -> list[tuple[str, ...]]:
    """Uses RegEx to extract chess moves from a string.

    Args:
        text (str): The string to find chess moves in.

    Returns:
        list[tuple[str]]: The list of chess moves, this will be empty if there are none.
    """
    return re.findall("([BNRQK]?([a-h]|[1-8])?x?[a-h][1-8](=[BNRQ])?(\+\+?|#)?)|(O-O(-O)?(\+\+?|#)?)", text)

def extract_number(
        regex_pattern: str,
        text: str,
        group_id: int = 1,
        default: typing.Any = None
    ) -> typing.Any | int:
    """Extracts a number from a string via RegEx and returns an integer.

    Args:
        regex_pattern (str): The regex pattern to match. Make sure to put parentheses around where the number should be.
        text (str): The text to search in.
        group_id (int, optional): The group id that will be returned. Defaults to 1.

    Returns:
        typing.Any | int: The extracted number, or the default if no number was found.
    """
    match = re.search(regex_pattern, text)
    
    if match is None:
        return default
    
    return u_converters.parse_int(match.group(group_id))


def parse_wikitext(
        *,
        wikitext: str,
        wiki_link: str,
        page_title: str = None,
        return_sections: bool = False,
        manual_replacements: typing.Callable[[str], str] = None
    ) -> str | dict[str, str]:
    """Parses wikitext into something that can be sent in Discord.

    Args:
        wikitext (str): The raw wikitext.
        wiki_link (str): A link to the wiki without a specific page. Example: "https://minecraft.wiki/w/"
        page_title (str, optional): The title of the page, will be used when making the section list. If return_sections is True then this must be provided. Defaults to None.
        return_sections (bool, optional): Whether to return it in a dict where the keys are the section names and the value is the section text. If this is True then page_title must be passed. Defaults to False.
        manual_replacements (typing.Callable[[str], str], optional): A callable that will be called on the wikitext before it is parsed. It will be passed the wikitext and should return a modified copy of that text. Defaults to None.

    Returns:
        str | dict[str, str]: The parsed wikitext as a string, or a dict with section titles as keys and the section text as values.
    """    
    parsed = wikitext

    if manual_replacements is not None:
        parsed = manual_replacements(parsed)

    parsed = re.sub(r"{{PAGENAME}}", page_title, parsed)

    ## Format math equations ##

    for match in re.finditer("<math>(.*?)<\/math>", parsed):
        match_text = match.group(1)
        match_text = re.sub(r"\\left *?\(", "(", match_text)
        match_text = re.sub(r"\\right *?\)", ")", match_text)
        match_text = re.sub(r"\\cdot", "*", match_text)
        match_text = re.sub(r"\\frac\{(.*?)\}\{(.*?)\}", r"(\1)/(\2)", match_text)
        match_text = re.sub(r"\{(.*?)\}", r"(\1)", match_text)
        match_text = re.sub(r"\\", "", match_text)
        parsed = parsed.replace(match.group(0), f"`{match_text}`")

    ###########################
    
    parsed = re.sub("{{[\w\W]*?}}", "", parsed)
    parsed = re.sub("\[\[File:[\w\W]+?\]\]", "", parsed)
    parsed = re.sub("\[\[Category:[\w\W]+?\]\]", "", parsed)
    parsed = re.sub('{\| class="wikitable[\w\W]+?}', "", parsed)
    parsed = parsed.replace("'''", "**")
    parsed = parsed.replace("''", "*")
    parsed = parsed.replace("<code>", "`")
    parsed = parsed.replace("</code>", "`")
    
    link_found = re.findall("\[\[((([\w'\" _]+)?#?)[\w'\" _]+)(\|[\w\W _]+?)?\]\]", parsed)

    for link_page, _, _, link_text in link_found:
        if link_page.startswith("#"):
            link_page = f"{page_title}#{link_text[1:]}"

        link_formatted = "{}{}".format(wiki_link, link_page.replace(" ", "_"))

        if len(link_text) == 0:
            text_show = link_page
        else:
            text_show = link_text.replace("|", "", 1)

        parsed = parsed.replace(f"[[{link_page}{link_text}]]", "[{}](<{}>)".format(text_show, link_formatted))
    
    if not return_sections:
        return parsed

    section_list = parsed.split("==")
    section_list.insert(0, page_title)
    
    section_list = [section.strip().strip("\n") for section in section_list]

    sections = dict(zip(section_list[::2], map(str, section_list[1::2])))

    return sections

def format_timedelta(duration: datetime.timedelta) -> tuple[int, int, int, int]:
    """Formats a timedelta into more readable numbers.

    Args:
        duration (datetime.timedelta): The timedelta to format.

    Returns:
        tuple[int, int, int, int]: The number of days, then hours, then minutes, then seconds.
    """
    days, seconds = duration.days, duration.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = (seconds % 60)
    return days, hours, minutes, seconds

def format_decimal(value: decimal.Decimal) -> str:
    """Formats a decimal.Decimal number.

    Args:
        value (decimal.Decimal): The decimal number to format.

    Returns:
        str: The formatted number as a string.
    """
    value = value.normalize()
    sign, digits, exponent = value.as_tuple()

    try:
        if exponent < 0:
            precision = -exponent
        else:
            precision = 0
    except TypeError:
        # The only place this seems to occur is if the result is some form of infinity.
        precision = len(exponent)

    formatted_value = f"{value:,.{precision}f}"
    return formatted_value