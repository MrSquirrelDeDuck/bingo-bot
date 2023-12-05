"""This is a bunch of converters that can be used in places to check for stuff.
The primary use is in command parameters via typing.Optional, however it can also be used to parse integers that contain commas."""

##################
##### COMMAS #####
##################

def parse_int(argument) -> int:
    """Converts an argument to an integer, will remove commas along the way."""
    return int(float(str(argument).replace(",", "")))

def is_digit(string) -> bool:
    """Same as str.isdigit(), but will remove commas first."""
    return str(string).replace(",", "").isdigit()

def is_numeric(string) -> bool:
    """Same as str.isnumeric(), but will remove commas first."""
    return str(string).replace(",", "").isnumeric()

def is_decimal(string) -> bool:
    """Same as str.isdecimal(), but will remove commas first."""
    return str(string).replace(",", "").isdecimal()