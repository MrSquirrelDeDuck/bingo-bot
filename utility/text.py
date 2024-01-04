"""Functions for working with/formatting text."""

from discord.ext import commands

import utility.interface as u_interface

def smart_number(number: int) -> str:
    """Inserts a comma in the correct spots so numbers are easy to read."""
    return f'{number:,d}'

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

def after_parameter(ctx: commands.Context, parameter_text: str) -> str:
    """Gets all the text after a parameter."""
    return u_interface.msg_content(ctx).split(str(parameter_text), 1)[-1].lstrip('"\'').strip()

def return_numeric(text: str) -> int:
    """Returns just all the numbers in a string as an integer, ignoring all other characters."""
    return int("".join([i for i in str(text) if i.isdigit()]))