"""This is a bunch of general converters that can be used in places to check for stuff. There are other, more specific converters in other utility files.
The primary use is in command parameters via typing.Optional, however it can also be used to parse integers that contain commas."""

from discord.ext import commands
import re

import utility.text as u_text

def parse_percent(argument: str) -> float:
    """Attempts to parse an argument as a percentage and return that percentage, will remove commas along the way.
    Examples:
    - input: 20%, output: 0.2
    - input: 0.45, output: 0.45
    - input: 0.45%, output: 0.0045"""
    if argument.endswith("%"):
        return float(u_text.rreplace(argument, "%", "", 1).replace(",", "")) / 100
    else:
        return float(str(argument).replace(",", ""))

def parse_float(argument: str) -> float:
    """Converts an argument to an float, will remove commas along the way."""
    return float(str(argument).replace(",", ""))

def parse_int(argument: str) -> int:
    """Converts an argument to an integer, will remove commas along the way."""
    return int(str(argument).replace(",", ""))

def extended_bool(argument: str) -> bool:
    """Extended boolean converter that allows for more things to be specified."""
    if argument.lower() in ["true", "t", "1", "on", "yes"]:
        return True
    elif argument.lower() in ["false", "f", "0", "off", "no"]:
        return False
    
    raise commands.BadArgument

def parse_message_link(argument: str) -> dict[str, int]:
    """Attempts to convert an argument that's a Discord message link into a dict. Returned dict has the guild id, the channel id, and the message id."""
    matched = re.match("https:\/\/discord\.com\/channels\/(\d+)\/(\d+)\/(\d+)", argument)

    if matched is None:
        raise commands.BadArgument
    
    return {
        "guild": int(matched.group(1)),
        "channel": int(matched.group(2)),
        "message": int(matched.group(3)),
    }

def is_float(string: str) -> bool:
    """Returns a boolean for whether a string represents a float."""
    if string is None: 
        return False
    try:
        float(string)
        return True
    except ValueError:
        return False

def is_digit(string) -> bool:
    """Same as str.isdigit(), but will remove commas first."""
    return str(string).replace(",", "").isdigit()

def is_numeric(string) -> bool:
    """Same as str.isnumeric(), but will remove commas first."""
    return str(string).replace(",", "").isnumeric()

def is_decimal(string) -> bool:
    """Same as str.isdecimal(), but will remove commas first."""
    return str(string).replace(",", "").isdecimal()