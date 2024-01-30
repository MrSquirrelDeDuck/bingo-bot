"""Functions for working with/formatting text."""

from discord.ext import commands
import typing
import re
import os

import utility.interface as u_interface

def rreplace(string: str, old: str, new: str, amount: int = -1) -> str:
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

def word_plural(text: str, number: int) -> str:
    """Returns the provided text, with an "s" added at the end if the number is not 1.

    Args:
        text (str): The text to potentially add the "s" to.
        number (int): The number to check against.

    Returns:
        str: The text with an "s" added at the end if the number is not 1.
    """
    return f"{text}{'s' if number != 1 else ''}"

def smart_text(number: int, text: str) -> str:
    """Combines smart_number() and word_plural() into one function. Will add a space between the number and text.

    Args:
        number (int): The number to use.
        text (str): The text to put at the end.

    Returns:
        str: The formatted number with commas, and then the text with an "s" at the end if the number isn't 1.
    """
    return f"{smart_number(number)} {word_plural(text, number)}"

def split_chunks(text: str, chunk_length: int) -> list[str]:
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

def has_ping(text: str) -> bool:
    """Uses RegEx to check if a piece of text contains a ping.

    Args:
        text (str): The text to check.

    Returns:
        bool: Whether the text contains a ping.
    """
    return re.match("<@&?\d+>|@(everyone|here)", text) is not None

def after_parameter(ctx: commands.Context, parameter_text: str) -> str:
    """Returns all the text after a parameter.

    If possible, using `arg1, *, arg2` for command parameters is better.

    Args:
        ctx (commands.Context): The context object.
        parameter_text (str): The parameter text to get the text after.

    Returns:
        str: The text after the parameter.
    """
    return u_interface.msg_content(ctx).split(str(parameter_text), 1)[-1].lstrip('"\'').strip()

def return_numeric(text: str) -> int:
    """Returns just all the nubmer in a string as an integer, ignoring all other characters.

    Args:
        text (str): The string to get the numbers from.

    Returns:
        int: An integer of all the numbers in the string.
    """
    return int("".join([i for i in str(text) if i.isdigit()]))

def return_alphanumeric(text: str) -> str:
    """Returns just all the letters, numbers, spaces, dashes, and underscores in a string, ignoring all other characters.

    Args:
        text (str): The text to filter.

    Returns:
        str: The filtered text.
    """
    character_filter = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLNOPQRSTUVWXYZ0123456789-_ "
    return "".join([i for i in str(text) if i in character_filter])

def parse_wikitext(
        *,
        wikitext: str,
        wiki_link: str,
        page_title: str = None,
        return_sections: bool = False,
        manual_replacements: typing.Callable[[str], str] = None
    ) -> typing.Union[str, dict[str, str]]:
    """Parses wikitext into something that can be sent in Discord.

    Args:
        wikitext (str): The raw wikitext.
        wiki_link (str): A link to the wiki without a specific page. Example: "https://minecraft.wiki/w/"
        page_title (str, optional): The title of the page, will be used when making the section list. If return_sections is True then this must be provided. Defaults to None.
        return_sections (bool, optional): Whether to return it in a dict where the keys are the section names and the value is the section text. If this is True then page_title must be passed. Defaults to False.
        manual_replacements (typing.Callable[[str], str], optional): A callable that will be called on the wikitext before it is parsed. It will be passed the wikitext and should return a modified copy of that text. Defaults to None.

    Returns:
        typing.Union[str, dict[str, str]]: The parsed wikitext as a string, or a dict with section titles as keys and the section text as values.
    """    
    parsed = wikitext

    if manual_replacements is not None:
        parsed = manual_replacements(parsed)

    parsed = re.sub("<math>.*?<\/math>", "", parsed)
    parsed = re.sub("{{[\w\W]*?}}", "", parsed)
    parsed = re.sub("\[\[File:[\w\W]+?\]\]", "", parsed)
    parsed = re.sub("\[\[Category:[\w\W]+?\]\]", "", parsed)
    parsed = re.sub('{\| class="wikitable[\w\W]+?}', "", parsed)
    parsed = parsed.replace("'''", "**")
    parsed = parsed.replace("''", "*")
    parsed = parsed.replace("<code>", "`")
    parsed = parsed.replace("</code>", "`")
    
    link_found = re.findall("\[\[([\w'\" _]+)(\|[\w\W _]+?)?\]\]", parsed)

    for link_page, link_text in link_found:
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