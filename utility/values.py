"""Objects that can be used to get the relationships between text and items in the bread game.

This is essentially a modified copy of values.py from Machine-Mind"""

import typing
from discord.ext import commands


class Item:
    def __init__(self: typing.Self,
                name: str,
                internal_name: str,
                internal_emoji: str,
                emoji: str = None,
                attributes: list[str] = [],
                gambit_bonus: int = None,
                aliases: list[str] = [],
                gamble_multiplier: int = None
            ) -> None:
        """Generic Bread Game item object.

        Args:
            self (typing.Self)
            name (str): Name of the emoji, something like "Stuffed Flatbread" or "Black Pawn"
            internal_emoji (str): Internal emoji for this, like ":stuffed_flatbread:" or "<:Bpawn:961815364436635718>"
            internal_name (str): Internal name for this emoji, like "stuffed_flatbread" or "bpawn"
            emoji (str, optional): Emoji symbol for this, something like "🥙". Defaults to None.
            attributes (list[str], optional): A list of attributes this has, like "['special_bread']" or "['chess_piece', 'black_chess_piece']". Defaults to [].
            gambit_bonus (int, optional): The amount of a dough bonus this item gets with the gambit shop. If this item isn't in the gambit shop, don't provide it or just provide None.. Defaults to None.
            aliases (list[str], optional): A list of aliases that can be used to refer to this item. Like "['stuffed']" or "['black_pawn']". Defaults to [].
            gamble_multiplier (int, optional): The amount to multiply the gamble wager by if this item is won. If this item is not in gambling, don't provide it or just provide None. Defaults to None.
        """

        self.name = name
        self.internal_name = internal_name
        self.internal_emoji = internal_emoji

        if emoji is None:
            self.emoji = internal_emoji
        else:
            self.emoji = emoji

        self.attributes = attributes
        self.gambit_bonus = gambit_bonus,
        self.aliases = aliases
        self.gamble_multiplier = gamble_multiplier
    
    def __str__(self: typing.Self) -> str:
        return self.internal_emoji
    
    def __repr__(self: typing.Self) -> str:
        return self.__str__()
    
    def __eq__(self: typing.Self, other: typing.Any) -> bool:
        try:
            return self.internal_name == other.internal_name
        except:
            return False
    
    def __key__(self):
        return (self.name, self.internal_name, self.internal_emoji)

    def __hash__(self):
        return hash(self.__key__())

class StonkItem(Item):
    def __init__(self: typing.Self,
                name: str,
                internal_name: str,
                internal_emoji: str,
                base_value: int,
                emoji: str = None,
                attributes: list[str] = [],
                gambit_bonus: int = None,
                aliases: list[str] = [],
                graph_color: str = None,
                gamble_multiplier: int = None
            ) -> None:
        """Object specifcially for stonks.

        Args:
            self (typing.Self)
            name (str): Name of the emoji, something like "Stuffed Flatbread" or "Black Pawn"
            internal_emoji (str): Internal emoji for this, like ":stuffed_flatbread:" or "<:Bpawn:961815364436635718>"
            internal_name (str): Internal name for this emoji, like "stuffed_flatbread" or "bpawn"
            base_value (int): The starting value of this stonk.
            emoji (str, optional): Emoji symbol for this, something like "🥙". Defaults to None.
            attributes (list[str], optional): A list of attributes this has, like "['special_bread']" or "['chess_piece', 'black_chess_piece']". Defaults to [].
            gambit_bonus (int, optional): The amount of a dough bonus this item gets with the gambit shop. If this item isn't in the gambit shop, don't provide it or just provide None. Defaults to None.
            aliases (list[str], optional): A list of aliases that can be used to refer to this item. Like "['stuffed']" or "['black_pawn']". Defaults to []..
            gamble_multiplier (int, optional): The amount to multiply the gamble wager by if this item is won. If this item is not in gambling, don't provide it or just provide None. Defaults to None.
            graph_color (str, optional): The color to use for this stonk on stonk graphs. Defaults to None.
        """
        super().__init__(name, internal_name, internal_emoji, emoji, attributes, gambit_bonus, aliases, gamble_multiplier)

        self.base_value = base_value
        self.graph_color = graph_color


    def value(self) -> int:
        """Returns this stonk's current value."""
        current_values = u_stonks.current_values()
        return current_values.get(self.internal_name)

class ChessItem(Item):
    def __init__(self: typing.Self,
                name: str,
                internal_name: str,
                internal_emoji: str,
                is_white: bool,
                emoji: str = None,
                attributes: list[str] = [],
                gambit_bonus: int = None,
                aliases: list[str] = [],
                gamble_multiplier: int = None
            ) -> None:
        """Object specifically for chess pieces.

        Args:
            self (typing.Self)
            name (str): Name of the emoji, something like "Stuffed Flatbread" or "Black Pawn"
            internal_emoji (str): Internal emoji for this, like ":stuffed_flatbread:" or "<:Bpawn:961815364436635718>"
            internal_name (str): Internal name for this emoji, like "stuffed_flatbread" or "bpawn"
            is_white (bool): A boolean for whether this piece is a white chess piece.
            emoji (str, optional): Emoji symbol for this, something like "🥙". Defaults to None.
            attributes (list[str], optional): A list of attributes this has, like "['special_bread']" or "['chess_piece', 'black_chess_piece']". Defaults to [].
            gambit_bonus (int, optional): The amount of a dough bonus this item gets with the gambit shop. If this item isn't in the gambit shop, don't provide it or just provide None.. Defaults to None.
            aliases (list[str], optional): A list of aliases that can be used to refer to this item. Like "['stuffed']" or "['black_pawn']". Defaults to []..
            gamble_multiplier (int, optional): The amount to multiply the gamble wager by if this item is won. If this item is not in gambling, don't provide it or just provide None. Defaults to None.
        """
        super().__init__(name, internal_name, internal_emoji, emoji, attributes, gambit_bonus, aliases, gamble_multiplier)

        self.is_white = is_white

#####################
##### ITEM LIST #####
#####################

bread = Item(
    name = "Bread",
    internal_name = "bread",
    internal_emoji = ":bread:",
    emoji = "🍞",
    attributes = ["rollable", "gamble_item", "gamble_bread"],
    gamble_multiplier = 0.5
)

##### Special bread. #####

flatbread = Item(
    name = "Flatbread",
    internal_name = "flatbread",
    internal_emoji = ":flatbread:",
    emoji = "🫓",
    gambit_bonus = 2,
    attributes = ["special_bread", "rollable", "gamble_item", "gamble_special"],
    gamble_multiplier = 2
)

stuffed_flatbread = Item(
    name = "Stuffed Flatbread",
    internal_name = "stuffed_flatbread",
    internal_emoji = ":stuffed_flatbread:",
    emoji = "🥙",
    gambit_bonus = 2,
    attributes = ["special_bread", "rollable", "gamble_item", "gamble_special"],
    aliases = ["stuffed"],
    gamble_multiplier = 2
)

sandwich = Item(
    name = "sandwich",
    internal_name = "sandwich",
    internal_emoji = ":sandwich:",
    emoji = "🥪",
    gambit_bonus = 2,
    attributes = ["special_bread", "rollable", "gamble_item", "gamble_special"],
    gamble_multiplier = 2
)

french_bread = Item(
    name = "french_bread",
    internal_name = "french_bread",
    internal_emoji = ":french_bread:",
    emoji = "🥖",
    gambit_bonus = 2,
    attributes = ["special_bread", "rollable", "gamble_item", "gamble_special"],
    gamble_multiplier = 2
)

croissant = Item(
    name = "Croissant",
    internal_name = "croissant",
    internal_emoji = ":croissant:",
    emoji = "🥐",
    gambit_bonus = 2,
    attributes = ["special_bread", "rollable", "gamble_item", "gamble_special"],
    gamble_multiplier = 2
)

##### Rare bread. #####

bagel = Item(
    name = "Bagel",
    internal_name = "bagel",
    internal_emoji = ":bagel:",
    emoji = "🥯",
    gambit_bonus = 4,
    attributes = ["rare_bread", "rollable"]
)

doughnut = Item(
    name = "Doughnut",
    internal_name = "doughnut",
    internal_emoji = ":doughnut:",
    emoji = "🍩",
    gambit_bonus = 4,
    attributes = ["rare_bread", "rollable"]
)

waffle = Item(
    name = "Waffle",
    internal_name = "waffle",
    internal_emoji = ":waffle:",
    emoji = "🧇",
    gambit_bonus = 4,
    attributes = ["rare_bread", "rollable"]
)

##### Black chess pieces. #####

bpawn = ChessItem(
    name = "Black Pawn",
    internal_name = "bpawn",
    internal_emoji = "<:Bpawn:961815364436635718>",
    is_white = False,
    gambit_bonus = 20,
    attributes = ["chess_piece", "black_chess_piece", "rollable", "gamble_item", "gamble_chess_piece"],
    aliases = ["black_pawn"],
    gamble_multiplier = 4
)

bknight = ChessItem(
    name = "Black Knight",
    internal_name = "bknight",
    internal_emoji = "<:Bknight:961815364424048650>",
    is_white = False,
    gambit_bonus = 20,
    attributes = ["chess_piece", "black_chess_piece", "rollable", "gamble_item", "gamble_chess_piece"],
    aliases = ["black_knight"],
    gamble_multiplier = 4
)

bbishop = ChessItem(
    name = "Black Bishop",
    internal_name = "bbishop",
    internal_emoji = "<:Bbishop:961815364306608228>",
    is_white = False,
    gambit_bonus = 20,
    attributes = ["chess_piece", "black_chess_piece", "rollable", "gamble_item", "gamble_chess_piece"],
    aliases = ["black_bishop"],
    gamble_multiplier = 4
)

brook = ChessItem(
    name = "Black Rook",
    internal_name = "brook",
    internal_emoji = "<:Brook:961815364377919518>",
    is_white = False,
    gambit_bonus = 20,
    attributes = ["chess_piece", "black_chess_piece", "rollable", "gamble_item", "gamble_chess_piece"],
    aliases = ["black_rook"],
    gamble_multiplier = 4
)

bqueen = ChessItem(
    name = "Black Queen",
    internal_name = "bqueen",
    internal_emoji = "<:Bqueen:961815364470202428>",
    is_white = False,
    gambit_bonus = 20,
    attributes = ["chess_piece", "black_chess_piece", "rollable", "gamble_item", "gamble_chess_piece"],
    aliases = ["black_queen"],
    gamble_multiplier = 4
)

bking = ChessItem(
    name = "Black King",
    internal_name = "bking",
    internal_emoji = "<:Bking:961815364327600178>",
    is_white = False,
    gambit_bonus = 20,
    attributes = ["chess_piece", "black_chess_piece", "rollable", "gamble_item", "gamble_chess_piece"],
    aliases = ["black_king"],
    gamble_multiplier = 4
)

##### White chess pieces. #####

wpawn = ChessItem(
    name = "White Pawn",
    internal_name = "wpawn",
    internal_emoji = "<:Wpawn:961815364319207516>",
    is_white = True,
    gambit_bonus = 40,
    attributes = ["chess_piece", "white_chess_piece", "rollable"],
    aliases = ["white_pawn"]
)

wknight = ChessItem(
    name = "White Knight",
    internal_name = "wknight",
    internal_emoji = "<:Wknight:958746544436310057>",
    is_white = True,
    gambit_bonus = 40,
    attributes = ["chess_piece", "white_chess_piece", "rollable"],
    aliases = ["white_knight"]
)

wbishop = ChessItem(
    name = "White Bishop",
    internal_name = "wbishop",
    internal_emoji = "<:Wbishop:961815364428263435>",
    is_white = True,
    gambit_bonus = 40,
    attributes = ["chess_piece", "white_chess_piece", "rollable"],
    aliases = ["white_bishop"]
)

wrook = ChessItem(
    name = "White Rook",
    internal_name = "wrook",
    internal_emoji = "<:Wrook:961815364482793492>",
    is_white = True,
    gambit_bonus = 40,
    attributes = ["chess_piece", "white_chess_piece", "rollable"],
    aliases = ["white_rook"]
)

wqueen = ChessItem(
    name = "White Queen",
    internal_name = "wqueen",
    internal_emoji = "<:Wqueen:961815364461809774>",
    is_white = True,
    gambit_bonus = 40,
    attributes = ["chess_piece", "white_chess_piece", "rollable"],
    aliases = ["white_queen"]
)

wking = ChessItem(
    name = "White King",
    internal_name = "wking",
    internal_emoji = "<:Wking:961815364411478016>",
    is_white = True,
    gambit_bonus = 40,
    attributes = ["chess_piece", "white_chess_piece", "rollable"],
    aliases = ["white_king"]
)

##### Gems. #####

gem_red = Item(
    name = "Red Gem",
    internal_name = "gem_red",
    internal_emoji = "<:gem_red:1006498544892526612>",
    gambit_bonus = 150,
    attributes = ["shiny", "rollable"],
    aliases = "red_gem"
)

gem_blue = Item(
    name = "Blue Gem",
    internal_name = "gem_blue",
    internal_emoji = "<:gem_blue:1006498655508889671>",
    gambit_bonus = 250,
    attributes = ["shiny", "rollable"],
    aliases = "blue_gem"
)

gem_purple = Item(
    name = "Purple Gem",
    internal_name = "gem_purple",
    internal_emoji = "<:gem_purple:1006498607861604392>",
    gambit_bonus = 500,
    attributes = ["shiny", "rollable"],
    aliases = "purple_gem"
)

gem_green = Item(
    name = "Green Gem",
    internal_name = "gem_green",
    internal_emoji = "<:gem_green:1006498803295211520>",
    gambit_bonus = 750,
    attributes = ["shiny", "rollable"],
    aliases = "green_gem"
)

gem_gold = Item(
    name = "Gold Gem",
    internal_name = "gem_gold",
    internal_emoji = "<:gem_gold:1006498746718244944>",
    gambit_bonus = 5000,
    attributes = ["shiny", "rollable"],
    aliases = "gold_gem"
)

##### Miscellaneous items. #####

anarchy_chess = Item(
    name = "MoaK",
    internal_name = "anarchy_chess",
    internal_emoji = "<:anarchy_chess:960772054746005534>",
    attributes = ["rollable", "gamble_item", "gamble_anarchy"],
    aliases = ["moak"],
    gamble_multiplier = 10
)

chessatron = Item(
    name = "Chessatron",
    internal_name = "chessatron",
    internal_emoji = "<:chessatron:996668260210708491>"
)

omega_chessatron = Item(
    name = "Omega Chessatron",
    internal_name = "omega_chessatron",
    internal_emoji = "<:omega_chessatron:1010359685339160637>",
    aliases = "omega"
)

ascension_token = Item(
    name = "Ascension Token",
    internal_name = "ascension_token",
    internal_emoji = "<:ascension_token:1023695148380602430>"
)

##### Shadow items. #####

shadow_moak = Item(
    name = "Shadow MoaK",
    internal_name = "shadow_moak",
    internal_emoji = "<:shadow_moak:1025974976093884537>",
    attributes = ["shadow"]
)

shadow_gem_gold = Item(
    name = "Shadow Gold Gem",
    internal_name = "shadow_gem_gold",
    internal_emoji = "<:shadow_gem_gold:1025975043907399711>",
    attributes = ["shadow"],
    aliases = ["shadow_gold_gem"]
)

shadowmega_chessatron = Item(
    name = "Shadowmega Chessatron",
    internal_name = "shadowmega_chessatron",
    internal_emoji = "<:shadowmega_chessatron:1025974897639432262>",
    attributes = ["shadow"],
    aliases = ["shadowmega"]
)

##### One of a Kinds. #####

anarchy = Item(
    name = "Anarchy",
    internal_name = "anarchy",
    internal_emoji = "<:anarchy:960771114819264533>",
    attributes = ["one_of_a_kind", "gamble_item", "gamble_anarchy"],
    gamble_multiplier = 10
)

holy_hell = Item(
    name = "Holy Hell",
    internal_name = "holy_hell",
    internal_emoji = "<:holy_hell:961184782253948938>",
    attributes = ["one_of_a_kind", "gamble_item", "gamble_anarchy"],
    gamble_multiplier = 10
)

horsey = Item(
    name = "Horsey",
    internal_name = "horsey",
    internal_emoji = "<:horsey:960727531592511578>",
    attributes = ["one_of_a_kind", "gamble_item", "gamble_horsey"],
    gamble_multiplier = 0
)

##### Stonks. #####

pretzel = StonkItem(
    name = "Pretzel",
    internal_name = "pretzel",
    internal_emoji = ":pretzel:",
    emoji = "🥨",
    base_value = 100,
    attributes = ["stonk"],
    graph_color = "#ff7f0e"
)

cookie = StonkItem(
    name = "Cookie",
    internal_name = "cookie",
    internal_emoji = ":cookie:",
    emoji = "🍪",
    base_value = 25,
    attributes = ["stonk"],
    graph_color = "#1f77b4"
)

fortune_cookie = StonkItem(
    name = "Fortune Cookie",
    internal_name = "fortune_cookie",
    internal_emoji = ":fortune_cookie:",
    emoji = "🥠",
    base_value = 500,
    attributes = ["stonk"],
    aliases = ["fortune"],
    graph_color = "#2ca02c"
)

pancakes = StonkItem(
    name = "Pancake",
    internal_name = "pancakes",
    internal_emoji = ":pancakes:",
    emoji = "🥞",
    base_value = 2500,
    attributes = ["stonk"],
    graph_color = "#d62728"
)

### Shadow stonks.

cake = StonkItem(
    name = "Cake",
    internal_name = "cake",
    internal_emoji = ":cake:",
    emoji = "🍰",
    base_value = 21000,
    attributes = ["shadow_stonk"],
    graph_color = "#9467bd"
)

pizza = StonkItem(
    name = "Pizza",
    internal_name = "pizza",
    internal_emoji = ":pizza:",
    emoji = "🍕",
    base_value = 168000,
    attributes = ["shadow_stonk"],
    graph_color = "#e377c2"
)

pie = StonkItem(
    name = "Pie",
    internal_name = "pie",
    internal_emoji = ":pie:",
    emoji = "🥧",
    base_value = 1512000,
    attributes = ["shadow_stonk"],
    aliases = ["fortune"],
    graph_color = "#bcbd22"
)

cupcake = StonkItem(
    name = "Cupcake",
    internal_name = "cupcake",
    internal_emoji = ":cupcake:",
    emoji = "🧁",
    base_value = 15120000,
    attributes = ["shadow_stonk"],
    graph_color = "#17becf"
)

##### Exclusively gamble items. #####

bricks = Item(
    name = "Brick",
    internal_name = "brick",
    internal_emoji = ":brick:",
    emoji = "🧱",
    attributes = ["gamble_item", "gamble_brick"],
    gamble_multiplier = 0
)

brick_fide = Item(
    name = "Pixel Fide Brick",
    internal_name = "brick_fide",
    internal_emoji = "<:brick_fide:961517570396135494>",
    attributes = ["gamble_item", "gamble_brick"],
    gamble_multiplier = 0
)

fide_brick = Item(
    name = "Fide Brick",
    internal_name = "fide_brick",
    internal_emoji = "<:fide_brick:961811237296037957>",
    attributes = ["gamble_item", "gamble_brick"],
    gamble_multiplier = 0
)

brick_gold = Item(
    name = "Gold Brick",
    internal_name = "brick_gold",
    internal_emoji = "<:brick_gold:971239215968944168>",
    attributes = ["gamble_item", "gamble_brick"],
    gamble_multiplier = 10
)

cherries = Item(
    name = "Cherries",
    internal_name = "cherries",
    internal_emoji = ":cherries:",
    emoji = "🍒",
    attributes = ["gamble_item", "gamble_fruit"],
    gamble_multiplier = 0.25
)

grapes = Item(
    name = "Grapes",
    internal_name = "grapes",
    internal_emoji = ":grapes:",
    emoji = "🍇",
    attributes = ["gamble_item", "gamble_fruit"],
    gamble_multiplier = 0.25
)

lemon = Item(
    name = "Lemon",
    internal_name = "lemon",
    internal_emoji = ":lemon:",
    emoji = "🍋",
    attributes = ["gamble_item", "gamble_fruit"],
    gamble_multiplier = 0.25
)

bcapy = ChessItem(
    name = "Black Capybara",
    internal_name = "bcapy",
    internal_emoji = "<:Bcapy:1003061938684711092>",
    is_white = False,
    attributes = ["gamble_item", "gamble_chess_piece"],
    gamble_multiplier = 4
)

### BASE LISTS ###
    
all_items = [bread, flatbread, stuffed_flatbread, sandwich, french_bread, croissant, bagel, doughnut, waffle, bpawn, bknight, bbishop, brook, bqueen, bking, wpawn, wknight, wbishop, wrook, wqueen, wking, gem_red, gem_blue, gem_purple, gem_green, gem_gold, anarchy_chess, chessatron, omega_chessatron, ascension_token, shadow_moak, shadow_gem_gold, shadowmega_chessatron, anarchy, holy_hell, horsey, pretzel, cookie, fortune_cookie, pancakes, cake, pizza, pie, cupcake, bricks, brick_fide, fide_brick, brick_gold, cherries, grapes, lemon, bcapy]
bling_items = [gem_red, gem_blue, gem_purple, gem_green, gem_gold, anarchy_chess]

#############################
##### UTILITY FUNCTIONS #####
#############################

def attribute_item_list(attributes: typing.Union[str, list[str]]) -> list[type[Item]]:
    """Returns a list of BaseItem and/or StonkItem objects that have any attribute that matches with `attribute`.
    
    If a string is passed to `attribute` the item must have that attribute to be included. If a list is passed the item must have any attribute in common in order to be included."""

    if attributes is None or len(attributes) == 0:
        return all_items

    if isinstance(attributes, str):
        attributes = [attributes]

    found_items = []

    for item in all_items:
        if any([attr in attributes for attr in item.attributes]):
            found_items.append(item)
    
    return found_items

def get_item(item_identifier: str, attributes: typing.Union[str, list[str]] = None) -> typing.Union[None, type[Item]]:
    """Attempts to get an item from a string. Returns None if no item is found.
    
    If an attribute (or multiples attributes) is provided the item must fall into one or more of the provided attributes."""

    if isinstance(item_identifier, Item):
        return item_identifier

    item_identifier = item_identifier.lower()
    
    if item_identifier[-1] == "s":
        plural_identifier = item_identifier[:-1]
    else:
        plural_identifier = f"{item_identifier}s"

    for identifier in [item_identifier, plural_identifier]:
        for item in attribute_item_list(attributes):
            if identifier == item.internal_name.lower() \
                or identifier == item.internal_emoji.lower()\
                or identifier == item.name.lower() \
                or identifier == item.emoji.lower() \
                or identifier in [i.lower() for i in item.aliases]:

                return item
    
    return None

def convert_dict(item_dict: dict[str, int]) -> dict[type[Item] | str, int]:
    """Converts the keys in a dict to Item objects (or subclasses) while ignoring the values that aren't items.

    Args:
        item_dict (dict[str, int]): The dict to convert.

    Returns:
        dict[type[Item] | str, int]: The converted dict with Item or string keys.
    """

    for key in item_dict:
        item = get_item(key)

        if not item:
            continue

        item_dict[item] = item_dict.pop(key)
    
    return item_dict


class ItemConverter(commands.Converter):
    """Converter that can be used in a command to automatically convert an argument to an item."""

    attributes = None

    def __init__(self, attributes: typing.Union[str, list[str]] = None) -> None:
        super().__init__()
        self.attributes = attributes

    async def convert(self, ctx, arg: str) -> type[Item]:
        converted = get_item(arg, self.attributes)

        if not converted:
            raise commands.errors.BadArgument
        
        return converted

RollableItemConverter = ItemConverter("rollable")
SpecialBreadConverter = ItemConverter("special_bread")
RareBreadConverter = ItemConverter("rare_bread")
GemConverter = ItemConverter("shiny")
StonkConverter = ItemConverter("stonk")
ChessPieceConverter = ItemConverter("chess_piece")
OneOfAKindConverter = ItemConverter("one_of_a_kind")
ShadowItemConverter = ItemConverter("shadow")

BlackChessPieceConverter = ItemConverter("black_chess_piece")
WhiteChessPieceConverter = ItemConverter("white_chess_piece")

InGambitShopConverter = ItemConverter(["special_bread", "rare_bread", "chess_piece", "shiny"])

###########################
##### ATTRIBUTE LISTS #####
###########################

rollable_items = attribute_item_list("rollable")

all_specials = attribute_item_list("special_bread")
all_rares = attribute_item_list("rare_bread")
special_and_rare = all_specials + all_rares

white_chess_pieces = attribute_item_list("white_chess_piece")
white_chess_biased = [wpawn] * 8 + [wknight] * 2 + [wbishop] * 2 + [wrook] * 2 + [wqueen, wking]

black_chess_pieces = attribute_item_list("black_chess_piece")
black_chess_biased = [bpawn] * 8 + [bknight] * 2 + [bbishop] * 2 + [brook] * 2 + [bqueen, bking]

all_chess_pieces = white_chess_pieces + black_chess_pieces

all_shiny = attribute_item_list("shiny")

all_gambit = special_and_rare + all_chess_pieces + all_shiny

one_of_a_kinds = attribute_item_list("one_of_a_kind")
stonks = attribute_item_list("stonk")
shadows = attribute_item_list("shadow")

gamble_items = attribute_item_list("gamble_item")

gamble_bricks = attribute_item_list("gamble_brick")
gamble_horsey = attribute_item_list("gamble_horsey")
gamble_fruit = attribute_item_list("gamble_fruit")
gamble_bread = attribute_item_list("gamble_bread")
gamble_special = attribute_item_list("gamble_special")
gamble_chess_piece = attribute_item_list("gamble_chess_piece")
gamble_anarchy = attribute_item_list("gamble_anarchy")

gamble_positives = gamble_special + gamble_chess_piece + gamble_anarchy + [brick_gold]
gamble_negatives = gamble_horsey + gamble_fruit + gamble_bread + [bricks, brick_fide, fide_brick]

###############################################################
#  █████  ██       ██████ ██   ██ ███████ ███    ███ ██    ██ #
# ██   ██ ██      ██      ██   ██ ██      ████  ████  ██  ██  #
# ███████ ██      ██      ███████ █████   ██ ████ ██   ████   #
# ██   ██ ██      ██      ██   ██ ██      ██  ██  ██    ██    #
# ██   ██ ███████  ██████ ██   ██ ███████ ██      ██    ██    #
###############################################################                                       

alchemy_recipes = {
    "wpawn": [
        {
            "cost": [(bpawn, 2), (doughnut, 10), (bagel, 10), (waffle, 10)]
        },
        {
            "cost": [(bpawn, 2), (croissant, 10), (flatbread, 10), (stuffed_flatbread, 10), (sandwich, 10), (french_bread, 10)]
        },
        {
            "cost": [(bpawn, 3)]
        },
        {
            "cost": [(gem_red, 1)]
        }
    ],
    "wrook": [
        {
            "cost": [(brook, 1), (sandwich, 50), (waffle, 25)]
        },
        {
            "cost": [(brook, 2), (sandwich, 50)]
        },
        {
            "cost": [(brook, 3)]
        },
        {
            "cost": [(brook, 2), (waffle, 75)]
        },
        {
            "cost": [(gem_red, 1)]
        }
    ],
        "wknight" : [
        {
			"cost": [(bknight, 1), (croissant, 50), (bagel, 25)]
		},
        {
			"cost": [(bknight, 2), (croissant, 50)]
		},
        {
			"cost": [(bknight, 3)]
		},
        {
			"cost": [(bknight, 2), (bagel, 75)]
		},
        {
			"cost": [(gem_red, 1)]
		}
    ],

    "wbishop" : [
        {
			"cost": [(bbishop, 1), (french_bread, 50), (doughnut, 25)]
		},
        {
			"cost": [(bbishop, 2), (french_bread, 50)]
		},
        {
			"cost": [(bbishop, 3)]
		},
        {
			"cost": [(bbishop, 2), (doughnut, 75)]
		},
        {
			"cost": [(gem_red, 1)]
		}
    ],

    "wqueen" : [
        {
			"cost": [(bqueen, 1), (stuffed_flatbread, 50), (doughnut, 25)]
		},
        {
			"cost": [(bqueen, 2), (stuffed_flatbread, 50)]
		},
        {
			"cost": [(bqueen, 3)]
		},
        {
			"cost": [(bqueen, 2), (doughnut, 75)]
		},
        {
			"cost": [(gem_red, 1)]
		}
    ],

    "wking" : [
        {
			"cost": [(bking, 1), (flatbread, 50), (bagel, 25)]
		},
        {
			"cost": [(bking, 2), (flatbread, 50)]
		},
        {
			"cost": [(bking, 3)]
		},
        {
			"cost": [(bking, 2), (bagel, 75)]
		},
        {
			"cost": [(gem_red, 1)]
		}
    ],

    "bpawn" : [
        {
			"cost": [(wpawn, 1)]
		},
        {
			"cost": [(gem_red, 1)]
		}
    ],

    "brook" : [
        {
			"cost": [(wrook, 1)]
		},
        {
			"cost": [(gem_red, 1)]
		}
    ],

    "bknight" : [
        {
			"cost": [(wknight, 1)]
		},
        {
			"cost": [(gem_red, 1)]
		}
    ],

    "bbishop" : [
        {
			"cost": [(wbishop, 1)]
		},
        {
			"cost": [(gem_red, 1)]
		}
    ],

    "bqueen" : [
        {
			"cost": [(wqueen, 1)]
		},
        {
			"cost": [(gem_red, 1)]
		}
    ],

    "bking" : [
        {
			"cost": [(wking, 1)]
		},
        {
			"cost": [(gem_red, 1)]
		}
    ],


    "gem_gold" : [
        {
			"cost": [(gem_green, 2), (gem_purple, 4), (gem_blue, 8), (gem_red, 16)]
		},
        {
			"cost": [(bread, 10000), 
            (croissant, 1000), (flatbread, 1000), (stuffed_flatbread, 1000), (sandwich, 1000), (french_bread, 1000),
            (doughnut, 500), (bagel, 500), (waffle, 500)]
		},
        {
            "cost": [(anarchy_chess, 1)],
            "requirement": [("loaf_converter", 128)],
            "provide_no_dough": True
        }
    ],

    "gem_green" : [
        {
			"cost": [(gem_purple, 2)]
		},
        {
			"cost": [(gem_gold, 1)],
            "result": 4
		}
    ],

    "gem_purple" : [
        {
			"cost": [(gem_blue, 2)]
		},
        {
			"cost": [(gem_green, 1)]
		}
    ],

    "gem_blue" : [
        {
			"cost": [(gem_red, 2)]
		},
        {
			"cost": [(gem_purple, 1)]
		}
    ],

    "gem_red" : [
        {
			"cost": [(gem_blue, 1)]
		}
    ],

    "omega_chessatron" : [
        {
			"cost": [(chessatron, 5), (anarchy_chess, 1), 
            (gem_gold, 1), (gem_green, 1), (gem_purple, 1), (gem_blue, 1), (gem_red, 1),
			]
		}
    ],

    "holy_hell" : [
        {
			"cost": [ (anarchy_chess, 5) ]
		}
    ],

    "anarchy" : [
        {
			"cost": [(anarchy_chess, 5)]
		}
    ],

    "horsey" : [
        {
			"cost": [(anarchy_chess, 5)]
		}
    ],

    "doughnut" : [
        {
			"cost": [(bread, 25)]
		}
    ],

    "bagel" : [
        {
			"cost": [(bread, 25)]
		}
    ],

    "waffle" : [
        {
			"cost": [(bread, 25)]
		}
    ],

    "flatbread" : [
        {
			"cost": [(bread, 10)]
		}
    ],

    "stuffed_flatbread" : [
        {
			"cost": [(bread, 10)]
		}
    ],

    "sandwich" : [
        {
			"cost": [(bread, 10)]
		}
    ],

    "french_bread" : [
        {
			"cost": [(bread, 10)]
		}
    ],

    "croissant" : [
        {
			"cost": [(bread, 10)]
		}
    ]
}

###############################################################################################################################
# ███    ███ ██ ███████  ██████      ██████  ██████  ███    ██ ██    ██ ███████ ██████  ███████ ██  ██████  ███    ██ ███████ #
# ████  ████ ██ ██      ██          ██      ██    ██ ████   ██ ██    ██ ██      ██   ██ ██      ██ ██    ██ ████   ██ ██      #
# ██ ████ ██ ██ ███████ ██          ██      ██    ██ ██ ██  ██ ██    ██ █████   ██████  ███████ ██ ██    ██ ██ ██  ██ ███████ #
# ██  ██  ██ ██      ██ ██          ██      ██    ██ ██  ██ ██  ██  ██  ██      ██   ██      ██ ██ ██    ██ ██  ██ ██      ██ #
# ██      ██ ██ ███████  ██████      ██████  ██████  ██   ████   ████   ███████ ██   ██ ███████ ██  ██████  ██   ████ ███████ #
###############################################################################################################################

misc_conversions = {
    "chessatron": [
        {
            "cost": [(bpawn, 8), (bbishop, 2), (brook, 2), (bknight, 2), (bqueen, 1), (bking, 1), (wpawn, 8), (wbishop, 2), (wknight, 2), (wrook, 2), (wqueen, 1), (wking, 1)]
        },
        {
            "cost": [(gem_red, 32)]
        }
    ]
}


########################################################################################
#  ██████   █████  ███    ███ ██████  ██ ████████     ███████ ██   ██  ██████  ██████  #
# ██       ██   ██ ████  ████ ██   ██ ██    ██        ██      ██   ██ ██    ██ ██   ██ #
# ██   ███ ███████ ██ ████ ██ ██████  ██    ██        ███████ ███████ ██    ██ ██████  #
# ██    ██ ██   ██ ██  ██  ██ ██   ██ ██    ██             ██ ██   ██ ██    ██ ██      #
#  ██████  ██   ██ ██      ██ ██████  ██    ██        ███████ ██   ██  ██████  ██      #
########################################################################################

gambit_shop_items = {
    ##### TIER 1 #####
    "gambit_shop_tier_1": {
        "cost": [(doughnut, 10), (bagel, 10), (waffle, 10)],
        "level_required": 0,
        "official_name": "Gambit Shop Level"
    },
    "flatbread": {
        "cost": [(flatbread, 20), (stuffed_flatbread, 20), (sandwich, 20), (french_bread, 20), (croissant, 20)],
        "level_required": 1,
        "official_name": "Rolling Pin"
    },
    "stuffed_flatbread": {
        "cost": [(flatbread, 40), (stuffed_flatbread, 40), (sandwich, 40), (french_bread, 40), (croissant, 40)],
        "level_required": 1,
        "official_name": "Fresh Falafel"
    },
    "sandwich": {
        "cost": [(flatbread, 80), (stuffed_flatbread, 80), (sandwich, 80), (french_bread, 80), (croissant, 80)],
        "level_required": 1,
        "official_name": "BLT"
    },
    "french_bread": {
        "cost": [(flatbread, 160), (stuffed_flatbread, 160), (sandwich, 160), (french_bread, 160), (croissant, 160)],
        "level_required": 1,
        "official_name": "Brie"
    },
    "croissant": {
        "cost": [(flatbread, 320), (stuffed_flatbread, 320), (sandwich, 320), (french_bread, 320), (croissant, 320)],
        "level_required": 1,
        "official_name": "More Butter"
    },

    "bagel": {
        "cost": [(doughnut, 200), (bagel, 200), (waffle, 200)],
        "level_required": 1,
        "official_name": "Cream Cheese"
    },
    "doughnut": {
        "cost": [(doughnut, 400), (bagel, 400), (waffle, 400)],
        "level_required": 1,
        "official_name": "Jelly Filling"
    },
    "waffle": {
        "cost": [(doughnut, 800), (bagel, 800), (waffle, 800)],
        "level_required": 1,
        "official_name": "Maple Syrup"
    },

    ##### TIER 2 #####

    "gambit_shop_tier_2": {
        "cost": [(gem_red, 3)],
        "level_required": 1,
        "official_name": "Gambit Shop Level"
    },
    "bpawn": {
        "cost": [(bpawn, 25), (gem_red, 1)],
        "level_required": 2,
        "official_name": "e5"
    },
    "bknight": {
        "cost": [(bpawn, 25), (bknight, 10), (gem_red, 1)],
        "level_required": 2,
        "official_name": "King's Indian Defense"
    },
    "bbishop": {
        "cost": [(bpawn, 25), (bbishop, 10), (gem_red, 1)],
        "level_required": 2,
        "official_name": "Classical Defense"
    },
    "brook": {
        "cost": [(bpawn, 25), (brook, 10), (gem_red, 1)],
        "level_required": 2,
        "official_name": "0-0"
    },
    "bqueen": {
        "cost": [(bpawn, 25), (bqueen, 10), (gem_red, 1)],
        "level_required": 2,
        "official_name": "Botez Gambit"
    },
    "bking": {
        "cost": [(bpawn, 25), (bking, 10), (gem_red, 1)],
        "level_required": 2,
        "official_name": "Bongcloud"
    },

    ##### TIER 3 #####
    
    "gambit_shop_tier_3": {
        "cost": [(gem_blue, 3)],
        "level_required": 2,
        "official_name": "Gambit Shop Level"
    },
    "wpawn": {
        "cost": [(wpawn, 25), (gem_blue, 1)],
        "level_required": 3,
        "official_name": "e4"
    },
    "wknight": {
        "cost": [(wpawn, 25), (wknight, 10), (gem_blue, 1)],
        "level_required": 3,
        "official_name": "Vienna Game"
    },
    "wbishop": {
        "cost": [(wpawn, 25), (wbishop, 10), (gem_blue, 1)],
        "level_required": 3,
        "official_name": "King's Fianchetto Opening"
    },
    "wrook": {
        "cost": [(wpawn, 25), (wrook, 10), (gem_blue, 1)],
        "level_required": 3,
        "official_name": "Ra4"
    },
    "wqueen": {
        "cost": [(wpawn, 25), (wqueen, 10), (gem_blue, 1)],
        "level_required": 3,
        "official_name": "Botez Gambit Accepted"
    },
    "wking": {
        "cost": [(wpawn, 25), (wking, 10), (gem_blue, 1)],
        "level_required": 3,
        "official_name": "Double Bongcloud"
    },

    ##### TIER 4 #####

    "gambit_shop_tier_4": {
        "cost": [(gem_purple, 3)],
        "level_required": 3,
        "official_name": "Gambit Shop Level"
    },
    "gem_red": {
        "cost": [(gem_red, 10), (gem_blue, 5)],
        "level_required": 4,
        "official_name": "Refined Ruby"
    },
    "gem_blue": {
        "cost": [(gem_red, 20), (gem_blue, 10), (gem_purple, 5)],
        "level_required": 4,
        "official_name": "Sapphire Ring"
    },
    "gem_purple": {
        "cost": [(gem_red, 40), (gem_blue, 20), (gem_purple, 10), (gem_green, 5)],
        "level_required": 4,
        "official_name": "Amethyst Amulet"
    },
    "gem_green": {
        "cost": [(gem_red, 80), (gem_blue, 40), (gem_purple, 20), (gem_green, 10), (gem_gold, 5)],
        "level_required": 4,
        "official_name": "Emerald Necklace"
    },
    "gem_gold": {
        "cost": [(gem_red, 160), (gem_blue, 80), (gem_purple, 40), (gem_green, 20), (gem_gold, 10)],
        "level_required": 4,
        "official_name": "Gold Ring"
    }
}

# Imports down here to avoid circular imports.
import utility.stonks as u_stonks

import importlib

importlib.reload(u_stonks)