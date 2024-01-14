"""This is a bunch of general converters that can be used in places to check for stuff. There are other, more specific converters in other utility files.
The primary use is in command parameters via typing.Optional, however it can also be used to parse integers that contain commas."""

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

def parse_float(argument) -> float:
    """Converts an argument to an float, will remove commas along the way."""
    return float(str(argument).replace(",", ""))

def parse_int(argument) -> int:
    """Converts an argument to an integer, will remove commas along the way."""
    return int(str(argument).replace(",", ""))

def is_digit(string) -> bool:
    """Same as str.isdigit(), but will remove commas first."""
    return str(string).replace(",", "").isdigit()

def is_numeric(string) -> bool:
    """Same as str.isnumeric(), but will remove commas first."""
    return str(string).replace(",", "").isnumeric()

def is_decimal(string) -> bool:
    """Same as str.isdecimal(), but will remove commas first."""
    return str(string).replace(",", "").isdecimal()