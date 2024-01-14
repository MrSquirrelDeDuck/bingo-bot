"""Functions for working with/formatting text."""

from discord.ext import commands
import typing
import re

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
    """Inserts a comma in the correct spots so numbers are easy to read."""
    return f'{number:,}'

def word_plural(text: str, number: int) -> str:
    """Returns the provided text, with an "s" added at the end if the number is not 1."""
    return f"{text}{'s' if number != 1 else ''}"

def smart_text(number: int, text: str) -> str:
    """Combines smart_number() and word_plural() into one function. Will add a space between the number and text."""
    return f"{smart_number(number)} {word_plural(text, number)}"

def split_chunks(text: str, chunk_length: int) -> list[str]:
    """Splits a string into chunks."""
    return [text[i:i + chunk_length] for i in range(0, len(text), chunk_length)]

def ping_filter(text: str) -> str:
    """Puts an invisible character (U+200B) after every @ symbol."""
    return text.replace("@", "@​")

def has_ping(text: str) -> bool:
    """Returns a boolean for whether a piece of text contains a ping."""
    return re.match("<@&?\d+>|@(everyone|here)", text) is not None

def after_parameter(ctx: commands.Context, parameter_text: str) -> str:
    """Gets all the text after a parameter."""
    return u_interface.msg_content(ctx).split(str(parameter_text), 1)[-1].lstrip('"\'').strip()

def return_numeric(text: str) -> int:
    """Returns just all the numbers in a string as an integer, ignoring all other characters."""
    return int("".join([i for i in str(text) if i.isdigit()]))

def parse_wikitext(wikitext: str, wiki_link: str, page_title: str = None, return_sections: bool = False) -> typing.Union[str, dict[str, str]]:
    """Parses wikitext into something that can be sent in Discord.

    Args:
        wikitext (str): The raw wikitext.
        wiki_link (str): A link to the wiki without a specific page. Example: "https://minecraft.wiki/w/"
        page_title (str, optional): The title of the page, will be used when making the section list. If return_sections is True then this must be provided. Defaults to None.
        return_sections (bool, optional): Whether to return it in a dict where the keys are the section names and the value is the section text. If this is True then page_title must be passed. Defaults to False.

    Returns:
        typing.Union[str, dict[str, str]]: The parsed wikitext as a string, or a dict with section titles as keys and the section text as values.
    """    
    parsed = wikitext

    parsed = re.sub("<math>.*?<\/math>", "", parsed)
    parsed = re.sub("{{[\w\W]*?}}", "", parsed)
    parsed = re.sub("\[\[File:[\w\W]+?\]\]", "", parsed)
    parsed = re.sub("\[\[Category:[\w\W]+?\]\]", "", parsed)
    parsed = re.sub('{\| class="wikitable[\w\W]+?}', "", parsed)
    parsed = parsed.replace("'''", "**")
    parsed = parsed.replace("''", "*")
    
    link_found = re.findall("\[\[([\w _]+)(\|[\w\W _]+?)?\]\]", parsed)

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