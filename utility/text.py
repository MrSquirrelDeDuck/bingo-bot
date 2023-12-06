"""Functions for working with/formatting text."""

def smart_number(number: int) -> str:
    """Inserts a comma in the correct spots so numbers are easy to read."""
    return f'{number:,d}'

def word_plural(text: str, number: int) -> str:
    """Returns the provided text, with an "s" added at the end if the number is not 1."""
    return f"{text}{'s' if number != 1 else ''}"

def smart_text(number: int, text: str) -> str:
    """Combines smart_number() and word_plural() into one function. Will add a space between the number and text."""
    return f"{smart_number(number)} {word_plural(text, number)}"