"""Utility functions for working with the Bread Game."""

import discord
import re
import typing
import math
import datetime

# pip install pytz
import pytz

import utility.text as u_text
import utility.values as u_values
import utility.interface as u_interface
import utility.files as u_files
import utility.solvers as u_solvers

import importlib

importlib.reload(u_values)

class BreadDataAccount:
    def __init__(
            self: typing.Self,
            user_id: int,
            database: u_files.DatabaseInterface
        ) -> None:
        self.loaded = False
        self.data = {}
        
        self.user_id = user_id
        
        stored_data = database.load("bread", "data_storage", default={})

        if str(user_id) not in stored_data:
            return None
        
        stored_data = stored_data.get(str(user_id))

        self.update_from_dict(
            data = stored_data
        )

        self.loaded = True

        return None
        
    

    ###############################################################
    ## Utility methods.
    
    def has(
            self: typing.Self,
            key: typing.Type[u_values.Item] | str,
            minimum: int = 1
        ) -> bool:
        return self.data.get(key, 0) >= minimum

    
    def get(
            self: typing.Self,
            item: typing.Type[u_values.Item],
            default: typing.Any = 0
        ) -> int | typing.Any:
        if item in self.data:
            return self.data.get(item, default)

        if isinstance(item, u_values.Item):
            item = item.internal_name

        return self.data.get(item, default)
    
    def set(
            self: typing.Self,
            item: typing.Type[u_values.Item],
            value: int | typing.Any
        ) -> None:

        self.data[item] = value
    
    def solver(
            self: typing.Self,
            goal_item: typing.Type[u_values.Item],
            given_items: dict[typing.Type[u_values.Item], int] = None
        ) -> tuple[list[str], dict[u_values.Item, int], dict[str, int]]:
        """Runs the item solver to maximize the amount of an item.

        Args:
            goal_item (typing.Type[u_values.Item]): The item to maximize.
            given_items (dict[typing.Type[u_values.Item], int], optional): A list of items to give to the solver to use. If nothing is provided it will use all items stored in the account. Defaults to None.

        Returns:
            tuple[list[str], dict[u_values.Item, int], dict[str, int]]: The command list, post-alchemy version of the items, and the dict version of the solver.
        """
        if given_items is None:
            given_items = {}

            for item in u_values.all_items:
                given_items[item] = self.get(item, 0)
        
        solver = u_solvers.solver_wrapper(
            items = given_items,
            maximize = goal_item
        )

        return solver
    
    def update_from_dict(
            self: typing.Self,
            data: dict
        ) -> None:
        for key in data.copy():
            item = u_values.get_item(key)

            if item is None:
                continue

            data[item] = data.pop(key)

        self.data.update(data)
    
    def convert_to_dict(
            self: typing.Self
        ) -> dict:
        return self.data


        
    

    ###############################################################
    ## Methods for dealing with the database.

    def refresh_data(
            self: typing.Self,
            database: u_files.DatabaseInterface
        ) -> None:
        self.__init__(
            user_id = self.user_id,
            database = database
        )
    
    def update_stored_data(
            self: typing.Self,
            database: u_files.DatabaseInterface
        ) -> None:
        stored_data = database.load("bread", "data_storage", default={})

        string_user_id = str(self.user_id)

        if string_user_id not in stored_data:
            stored_data[string_user_id] = {}
        
        def sanitize_list(list_data: list) -> list:
            for index, value in enumerate(list_data.copy()):
                try:
                    list_data[index] = value.internal_name
                except AttributeError:
                    pass # If the value is not an item, do nothing.
            return list_data
        
        def sanitize_dict(dict_data: dict) -> dict:
            for key in dict_data.copy():
                if isinstance(dict_data[key], list):
                    dict_data[key] = sanitize_list(dict_data[key])
                    continue
                if isinstance(dict_data[key], dict):
                    dict_data[key] = sanitize_dict(dict_data[key]) # recursion go brrrrrrrrr
                    continue

                try:
                    modify_key = key.internal_name
                    dict_data[modify_key] = dict_data.pop(key)
                except AttributeError:
                    pass # If the key is not an item, do nothing.

            return dict_data

        data = sanitize_dict(self.data.copy())
        
        stored_data[string_user_id].update(data)

        database.save("bread", "data_storage", data=stored_data)
    
    def clear_stored_data(
            self: typing.Self,
            database: u_files.DatabaseInterface
        ) -> None:
        self.data = {}

        stored_data = database.load("bread", "data_storage", default={})

        try:       
            stored_data.pop(str(self.user_id))
        except KeyError: # This will be raised if the key isn't in the data already.
            return

        database.save("bread", "data_storage", data=stored_data)
        
    

    ###############################################################
    ## Properties.
        
    @property
    def ascension_boost(self: typing.Self) -> float:
        return self.get("prestige_level") * 0.1 + 1
        
    @property
    def ascension(self: typing.Self) -> float:
        return self.get("prestige_level")
    
    @property
    def active_shadowmegas(self: typing.Self) -> int:
        return min(self.get(u_values.shadowmega_chessatron), self.get("chessatron_shadow_boost") * 5)

    @property
    def active_shadow_gold_gems(self: typing.Self) -> int:
        return min(self.get(u_values.shadow_gold_gems), self.get("shadow_gold_gem_luck_boost") * 10)
    
    @property
    def tron_value(self: typing.Self) -> int:
        omegas = self.get(u_values.omega_chessatron)
        ascension = self.ascension
        shadowmegas = self.active_shadowmegas

        return calculate_tron_value(
            ascension = ascension,
            omega_count = omegas,
            active_shadowmegas = shadowmegas,
        )

    @property
    def all_items(self: typing.Self) -> list[typing.Type[u_values.Item]]:
        out = []

        for item in self.data.keys:
            if isinstance(item, u_values.Item):
                out.append(item)
        
        return out

    @property
    def item_generator(self: typing.Self):
        for item in self.data.keys:
            if isinstance(item, u_values.Item):
                yield item
        
    

    ###############################################################
    ## Getters that can't be properties for varius reasons.
                
    def portfolio_value(
            self: typing.Self,
            current_data: dict
        ) -> int:
        value = 0
        current_data = current_data["values"]

        for stonk in u_values.stonks:
            if self.has(stonk):
                value += self.get(stonk) * current_data.get(stonk.internal_name)
        
        return value
    

        








######################################################################################################################################################
##### UTILITY FUNCTONS ###############################################################################################################################
######################################################################################################################################################

def bread_time() -> datetime.timedelta:
    """Returns a datetime.timedelta representing the time since the last Bread o' Clock.

    You can use `bst_time()` to get the current hour.

    Returns:
        datetime.timedelta: Timedelta for the time since the last Bread o' Clock.
    """

    def is_dst(dt=None, timezone="UTC"):
        if dt is None:
            dt = datetime.datetime.now(tz=datetime.UTC)
        timezone = pytz.timezone(timezone)
        timezone_aware_date = timezone.localize(dt, is_dst=None)
        return timezone_aware_date.tzinfo._dst.seconds != 0

    apply_dst = is_dst(datetime.datetime.now(), timezone="US/Pacific")

    timestamp = datetime.datetime.now(tz=datetime.UTC).replace(microsecond=0, tzinfo=None)

    if apply_dst:
        timestamp = timestamp + datetime.timedelta(hours=1)
    
    breadoclock = datetime.datetime(timestamp.year, timestamp.month, timestamp.day, 23, 5, 0).replace(tzinfo=None)
    
    if not (timestamp.hour >= 23 and timestamp.minute >= 5):
        breadoclock = breadoclock - datetime.timedelta(days=1)

    return timestamp - breadoclock

def bst_time() -> int:
    """Returns the current hour in Bread Standard Time.

    Returns:
        int: The current hour.
    """
    return bread_time().total_seconds() // 3600

def calculate_tron_value(
        ascension: int = 0,
        omega_count: int = 0,
        active_shadowmegas: int = 0,
        shadowmegas: int = 0,
        chessatron_contraption: int = 0
    ) -> int:
    """Calculates the value of a chessatron.

    Args:
        ascension (int, optional): The ascension the player is on. Defaults to 0.
        omega_count (int, optional): The number of omegas the player has. Defaults to 0.
        active_shadowmegas (int, optional): The number of active shadowmegas the player has, does not need to be provided if `shadowmegas` and `chessatron_contraption` is provided. Defaults to 0.
        shadowmegas (int, optional): The total number of shadowmegas the player has, not the number of active shadowmegas. This and `chessatron_contraption` can be provided or `active_shadowmegas` can be provided. Defaults to 0.
        chessatron_contraption (int, optional): The level of Chessatron Contraption the player has. This and `shadowmegas` can be provided or `active_shadowmegas` can be provided. Defaults to 0.

    Returns:
        int: The amount of dough the player gets for each chessatron they make.
    """
    active_shadowmegas = max(active_shadowmegas, min(shadowmegas, chessatron_contraption * 5))

    return round((2000 + (250 * omega_count) + (100 * active_shadowmegas)) * (1 + (0.1 * ascension)))

def get_ascension(
        tokens: int = 0,
        ddc: int = 0,
        scy: int = 0,
        mb: int = 0,
        cpe: int = 0,
        hrt: int = 0,
        cc: int = 0,
        es: int = 0,
        fcotd: int = 0
    ) -> int:
    """Determines the ascension of a player based on their current ascension tokens and hidden bakery purchases.

    Args:
        tokens (int, optional): The amount of ascension tokens the player has on them. Defaults to 0.
        ddc (int, optional): Level of Daily Discount Card. Defaults to 0.
        scy (int, optional): Level of Self Converting Yeast. Defaults to 0.
        mb (int, optional): Level of MoaK Booster. Defaults to 0.
        cpe (int, optional): Level of Chess Piece Equalizer. Defaults to 0.
        hrt (int, optional): Level of High Roller Table. Defaults to 0.
        cc (int, optional): Level of Chessatron Contraption. Defaults to 0.
        es (int, optional): Level of Ethereal Shine. Defaults to 0.
        fcotd (int, optional): Level of First Catch of the Day. Defaults to 0.

    Returns:
        int: The ascension the player is on.
    """

    token_list = [
        int((ddc + 3) / 3) * ddc - 3 * (int(ddc / 3) * (int(ddc / 3) + 1) / 2), # DDC
        int((scy + 3) / 3) * scy - 3 * (int(scy / 3) * (int(scy / 3) + 1) / 2), # SCY
        int((mb + 4) / 2 ) * mb - 2 * (int(mb / 2) * (int(mb / 2) + 1) / 2), # MB
        cpe * (1 + (cpe - 1) * 0.5), # CPE
        hrt, # Dunno if you'll be able to figure this one out.
        int((cc + 2) / 2) * cc - 2 * (int(cc / 2) * (int(cc / 2) + 1) / 2), # CC
        int((es + 2) / 2) * es - 2 * (int(es / 2) * (int(es / 2) + 1) / 2), # ES
        int((fcotd + 2) / 2) * fcotd - 2 * (int(fcotd / 2) * (int(fcotd / 2) + 1) / 2), # FCotD
        tokens
    ]

    token_sum = sum(token_list)

    return int(((token_sum - 31) / 6 + 6 if token_sum-1 > 30 else (token_sum - 1) / 5) + 1)

def parse_attempt(
        message: discord.Message,
        require_reply: bool = False,
        custom_check: typing.Callable[[discord.Message], bool] = None
    ) -> bool | dict[str, int | typing.Type[u_values.Item] | dict[str, bool], bool]:
    """Attempts to parse a Discord message. Returns the parser output, or False if any check failed.

    Args:
        message (discord.Message): The user message. This will check if it's replying to Machine-Mind (or a known clone.)
        require_reply (bool, optional): Whether it should require the replied-to message to be replying. Defaults to False.
        custom_check (typing.Callable[[discord.Message], bool], optional): A custom check that can be provided. The replied-to message will be passed to this. Defaults to None.

    Returns:
        bool | dict[str, int | typing.Type[u_values.Item] | dict[str, bool], bool]: The parser output, or False if any check failed.
    """
    replied_to = u_interface.replying_mm_checks(message, require_reply=require_reply, return_replied_to=True)
    
    if not replied_to:
        return False

    if not replied_to.content.startswith("Stats for:"):
        return False
    
    if custom_check is not None:
        if custom_check(replied_to):
            return False
                    
    return parse_stats(message.reference.resolved)
    








###############################################################
##### STATS PARSER ############################################
###############################################################

def parse_stats(message: discord.Message) -> dict[str | typing.Type[u_values.Item], int | dict[str, bool] | bool]:
    """Parses a Machine-Mind message and returns a dict of as many stats as it can figure out, both user stats and internal stats, like stonks, will be returned in the `stats` dict.
    
    The following messages can be parsed:
    - $bread stats (Main, individual items if it's split, and continued.)
    - $bread stats chess
    - $bread stats gambit
    - $bread portfolio
    - $bread invest
    - $bread divest
    - $bread shop
    - $bread hidden
    - $bread dough
    - $bread stonks
    - $brick stats

    Args:
        message (discord.Message): The discord message that will be parsed.

    Returns:
        dict[str | typing.Type[u_values.Item], int | dict[str, bool] | bool]: A dictionary containing the found stats and the key "parse_successful". If parse_successful is True, then there will be a "stats_type" key with the stats type and a "stats" dict. If parse_successful is False, then no stats will be returned, and something went wrong with the parsing of the stats.
    
    stats_type key:
    - "main": `$bread stats`.
    - "main_continued": The continued message sometimes sent from `$bread stats`.
    - "hidden_bakery": `$bread hidden_bakery`.
    - "bread_shop": `$bread shop`.
    - "dough": `$bread dough`.
    - "chess": `$bread stats chess`.
    - "gambit": `$bread stats gambit`.
    - "stonks": `$bread stonks`.
    - "portfolio": `$bread portfolio`.
    - "invest": `$bread invest`.
    - "divest_specific": `$bread divest [all|amount] [stonk]`.
    - "divest_all": `$bread divest all`.
    - "brick_stats": `$brick stats`.
    """

    content = message.content
    
    def extract(
            surrounding: str,
            *,
            text: str = None,
            emoji_discord: str = "",
            emoji_ascii: str = "",
            group_id: int = 1,
            default: int = None,
            escape: bool = True
        ) -> int | None:
        """Extracts a number from a string via regex.
        If an emoji is important to the regex string, it should be replaced with "&&" in `surrounding` and the parameters `emoji_discord` and `emoji_ascii` must be provided.

        Args:
            surrounding (str): The regex pattern. It should be a normal string, with the location of the number signified by `##`. Things like asterisks and periods will be escaped automatically unless `escape` is set to False.
            text (str, optional): The text that will be checked via regex. By default this is the content of the message. Defaults to None.
            emoji_discord (str, optional): The discord version of the emoji, something like ":flatbread:". Defaults to "".
            emoji_ascii (str, optional): The ascii version of the same emoji. Defaults to "".
            group_id (int, optional): The group id that will be returned, only use this if there are multiple numbers being found with regex. Defaults to 1.
            default (int, optional): The value that will be returned if nothing is found. Defaults to None.
            escape (bool, optional): Whether to automatically escape regex markdown found in `surrounding`. Defaults to True.

        Returns:
            int | None: If it's an int, the number that's found (or the default), if it's None, then nothing was found.
        """

        if text is None:
            text = content

        pattern = surrounding
        if escape:
            pattern = re.escape(pattern)
        
        pattern = pattern.replace("\#\#", "([\d,]+)").replace("\&\&", emoji_discord)

        search_result = re.search(pattern, text)

        if search_result is None:
            if emoji_ascii == "":
                return default
            
            pattern = surrounding
            if escape:
                pattern = re.escape(pattern)
            
            pattern = pattern.replace("\#\#", "([\d,]+)").replace("\&\&", emoji_ascii)

            search_result = re.search(pattern, text)
        
        if search_result is None:
            # This is only the case if neither the normal emoji nor the ascii one worked.
            return default

        return u_text.return_numeric(search_result.group(group_id))
    
    ####################
    ### $bread stats ###
    ####################

    if content.startswith("Stats for") or content.startswith("Stats continued:"):
        stats = {}

        content = content.replace("zero time", "0 time")
        content = content.replace("once", "1 time")
        content = content.replace("twice", "2 times")

        def direct(key: str, surrounding: str, **kwargs) -> None:
            """Uses `extract()` to get a number, and then sets the value in `stats` for the key `key` to it only if the result is not None. 

            Args:
                key (str): The key in `stats` that will be used.
                surrounding (str): The regex pattern. It should be a normal string, with the location of the number signified by `##`. Things like asterisks and periods will be escaped automatically unless `escape` is set to False.
            """
            nonlocal stats

            result = extract(surrounding, **kwargs)

            if result is not None:
                stats[key] = result

        if "You've found a single solitary loaf" in content:
            # If the if is true, then the extended part is here.
            # Let's go ahead and get the stats for it, because if this is the continued section we can return it when we're done and we won't be processing a bunch of stuff we don't need.
            
            direct("highest_roll", "Your highest roll was ##.")

            search_list = {
                "eleven_breads": "11 - ## time",
                "thirteen_breads": "12 - ## time",
                "twelve_breads": "13 - ## time",
                "fourteen_or_higher": "14+ - ## time",
                "natural_1": "You've found a single solitary loaf ## time",
                "ten_breads": "and the full ten loaves ## time",
                "lottery_win": "You've won the lottery ## time",
                "chess_pieces": "You have ## Chess Piece",
                "special_bread": "You have ## Special Bread"
            }

            for key, value in search_list.items():
                direct(key, value, default=0)
            
            if content.startswith("Stats continued:"):
                return {
                    "parse_successful": True,
                    "stats_type": "main_continued",
                    "stats": stats
                }
        
        if "Individual stats" in message.content:
            # If the item stats are in this message.
        
            alternate_style = [u_values.bread]

            for item in alternate_style:
                if item in u_values.all_chess_pieces:
                    continue

                direct(
                    item,
                    "&& - ##",
                    emoji_discord = item.internal_emoji,
                    emoji_ascii = item.emoji,
                    default = 0
                )

            for item in u_values.all_items:
                if item in u_values.all_chess_pieces:
                    continue
                if item in alternate_style:
                    continue

                direct(
                    item,
                    "## &&",
                    emoji_discord = item.internal_emoji,
                    emoji_ascii = item.emoji,
                    default = 0
                )
            
            if content.startswith("Stats continued:"):
                return {
                    "parse_successful": True,
                    "stats_type": "main_items",
                    "stats": stats
                }
        
        parse_list = {
            "total_dough": "You have **## dough.**",
            "earned_dough": "You've found ## dough through all your rolls",
            "stonk_profit": "and ## dough through stonks.",
            "total_rolls": "You've bread rolled ## times overall.",
            "lifetime_gambles": "You've gambled your dough ## times.",
            "loaf_converter": "You have ## Loaf Converter",
            "LC_booster": "with Recipe Refinement level ##",
            "multiroller": "With your ## Multiroller",
            "compound_roller": "message with your ## Compound Roller"
        }

        for key, value in parse_list.items():
            direct(key, value, default=0)
        
        if "You've rolled " in content:
            direct("daily_rolls", "You've rolled ##", default=0)
            direct("max_daily_rolls", "of ## times today.", default=0)
        elif "stored rolls, plus a" in content:
            direct("max_daily_rolls", "plus a maximum of ## daily rolls.", default=10)
        
        daily_discount_card = extract("You have ## Daily Discount Card", default = 0)
        self_converting_yeast = extract("You have ## Self Converting Yeast level", default = 0)
        moak_booster = extract("With level ## of the Moak Booster", default = 0)
        chess_piece_equalizer = extract("With level ## of the Chess Piece Equalizer", default = 0)
        high_roller_table = extract("You have level ## of the High Roller Table", default = 0)
        chessatron_contraption = extract("With level ## of the Chessatron Contraption", default = 0)
        ethereal_shine = extract("With level ## of Ethereal Shine", default = 0)
        first_catch_of_the_day = extract("With First Catch of the Day, your first ## special item", default = 0)

        ascension_number = extract("**##**\u2b50:", default=0) # \u2b50 is the star emoji.

        append = {
            "prestige_level": ascension_number,

            "gamble_level": high_roller_table,
            "max_daily_rolls_discount": daily_discount_card,
            "loaf_converter_discount": self_converting_yeast,
            "chess_piece_equalizer": chess_piece_equalizer,
            "moak_booster": moak_booster,
            "chessatron_shadow_boost": chessatron_contraption,
            "shadow_gold_gem_luck_boost": ethereal_shine,
            "first_catch_level": first_catch_of_the_day,
        }

        stats.update(append)

        bling = re.search("Stats for: (<:\w+:\d+>)", content)

        if bling is not None:
            bling = bling.group(1)

            bling = u_values.bling_items.index(u_values.get_item(bling)) + 1
            
            stats["bling"] = bling
        else:
            stats["bling"] = 0
        
        return {
            "parse_successful": True,
            "stats_type": "main",
            "stats": stats
        }




    ############################
    ### $bread hidden_bakery ###
    ############################

    if content.startswith("Welcome to the hidden bakery!"):

        moak_booster_levels = [100, 130, 170, 210, 280, 370]
        chess_piece_equalizer_levels = [25, 33, 42, 50]
        high_roller_table_levels = [50, 500, 1500, 5000, 10000, 100000, 10000000, 1000000000, 1000000000000]

        ascension_token_count = extract(f"You have **## {u_values.ascension_token.internal_emoji}**.")

        daily_discount_card = (124 - extract("Reduces the cost of a daily roll by ##, to ##.", group_id=2, default = 4)) // 4
        self_converting_yeast = (244 - extract("Reduces the cost of each loaf converter level by ##, to ##.", group_id=2, default = 16)) // 12
        moak_booster = extract("Increases the chances of finding a MoaK by ##%, to ##% of base.", group_id=2)
        chess_piece_equalizer = extract("Every Chess piece will have an increased chance of being white, to ##%.")
        high_roller_table = extract("Join the high roller table. Increases your maximum bid while gambling to ##.")
        chessatron_contraption = extract("for each shadowmega chessatron you own. Works for up to ## shadowmega chessatrons.", default = 250) // 5 - 1
        ethereal_shine = extract("Allows your shadow gold gems to help you find new gems. Up to ## shadow gold gems will", default = 500) // 10 - 1
        first_catch_of_the_day = extract("The first ## special items you find each day will be", default = -1) - 1

        if first_catch_of_the_day == -1:
            first_catch_of_the_day = 50
        
        if moak_booster is None:
            moak_booster = len(moak_booster_levels) - 1
        else:
            moak_booster = moak_booster_levels.index(moak_booster) - 1
        
        if chess_piece_equalizer is None:
            chess_piece_equalizer = len(chess_piece_equalizer_levels) - 1
        else:
            chess_piece_equalizer = chess_piece_equalizer_levels.index(chess_piece_equalizer) - 1
        
        if high_roller_table is None:
            high_roller_table = len(high_roller_table_levels) - 1
        else:
            high_roller_table = high_roller_table_levels.index(high_roller_table) - 1
        
        ### Figuring out what ascension you're on. ###
        
        ascension_number = get_ascension(ascension_token_count, daily_discount_card, self_converting_yeast, moak_booster, chess_piece_equalizer, high_roller_table, chessatron_contraption, ethereal_shine, first_catch_of_the_day)

        ##############################################
        
        stats = {
            u_values.ascension_token: ascension_token_count,
            "prestige_level": ascension_number,

            "gamble_level": high_roller_table,
            "max_daily_rolls_discount": daily_discount_card,
            "loaf_converter_discount": self_converting_yeast,
            "chess_piece_equalizer": chess_piece_equalizer,
            "moak_booster": moak_booster,
            "chessatron_shadow_boost": chessatron_contraption,
            "shadow_gold_gem_luck_boost": ethereal_shine,
            "first_catch_level": first_catch_of_the_day,
        }

        return {
            "parse_successful": True,
            "stats_type": "hidden_bakery",
            "stats": stats
        }

    
    ###################
    ### $bread shop ###
    ###################

    if content.startswith("Welcome to the store!"):
        stats = {
            "total_dough": extract("You have **## dough**.")
        }

        daily_discount_card = extract("**Extra daily roll** - ## dough")
        if daily_discount_card is not None:
            stats["max_daily_rolls_discount"] = (128 - daily_discount_card) // 4
        
        max_daily_rolls = extract("Permanently increases the number of daily rolls you can make to ##.")
        if max_daily_rolls is not None:
            stats["max_daily_rolls"] = max_daily_rolls - 1
        
        loaf_converters = extract("Each loaf is ## times more likely to be something special, compared to baseline.")
        if loaf_converters is not None:
            loaf_converters -= 2
            stats["loaf_converter"] = loaf_converters

        self_converting_yeast = extract("**Loaf Converter** - ## dough")
        if self_converting_yeast is not None:
            stats["loaf_converter_discount"] = (256 - self_converting_yeast // (loaf_converters + 1)) // 12

        multiroller = extract("Every $bread command you send will automatically roll bread ## times.")
        if multiroller is not None:
            stats["multiroller"] = int(math.log2(multiroller)) - 1

        compound_roller = extract("Every bread multiroll message will have up to ## rolls contained within.")
        if compound_roller is not None:
            stats["compound_roller"] = int(math.log2(compound_roller)) - 1

        recipe_refinement = extract("They will be ##x more effective for creating everything other than MoaKs.")
        if recipe_refinement is not None:
            stats["LC_booster"] = int(math.log2(recipe_refinement)) - 1
        
        if "Roll Summarizer" in content:
            stats["roll_summarizer"] = 0
        
        bling = re.search("A decorative <:\w+:\d+> for your stats and leaderboard pages\. Purely cosmetic\.", content)

        if bling is not None:
            bling = bling.group(0)

            for blingdex, bling_item in enumerate(u_values.bling_items): # blingdex is the index of bling
                if bling_item.internal_emoji in bling or bling_item.emoji in bling:
                    bling = blingdex
                    break
            
            stats["bling"] = bling
        
        return {
            "parse_successful": True,
            "stats_type": "bread_shop",
            "stats": stats
        }
    
    ####################
    ### $bread dough ###
    ####################

    if content.startswith("You have") and content.endswith(" dough**."):
        search_result = extract(
            "You have **## dough**."
        )

        if search_result is None:
            return {"parse_successful": False}

        return {
                "parse_successful": True,
                "stats_type": "dough",
                "stats": {
                    "total_dough": search_result
                }
            }

    ##########################
    ### $bread stats chess ###
    ##########################
    
    if content.startswith("Chess pieces of") and not content[-1] in ".?!":
        stats = {}

        for chess_piece in u_values.all_chess_pieces:
            extracted = extract(f"{chess_piece.internal_emoji} - ##")

            if extracted is None:
                continue

            stats[chess_piece] = extracted

        bling = re.search("Chess pieces of (<:\w+:\d+>)", content)

        if bling is not None:
            bling = bling.group(1)

            bling = u_values.bling_items.index(u_values.get_item(bling)) + 1
            
            stats["bling"] = bling
        else:
            stats["bling"] = 0

        if len(stats) == 0:
            return {"parse_successful": False}

        return {
                "parse_successful": True,
                "stats_type": "chess",
                "stats": stats
            }
    
    ###########################
    ### $bread stats gambit ###
    ###########################

    if content.startswith("Gambit shop bonuses for") and not content[-1] in ".?!":
        stats = {}

        for item_name in u_values.all_gambit:
            extracted = extract(f"{item_name.internal_emoji} - ##")

            if extracted is None:
                continue

            stats[item_name] = extracted

        bling = re.search("Gambit shop bonuses for (<:\w+:\d+>)", content)

        if bling is not None:
            bling = bling.group(1)

            bling = u_values.bling_items.index(u_values.get_item(bling)) + 1
        else:
            bling = 0

        if len(stats) == 0:
            return {"parse_successful": False}

        return {
                "parse_successful": True,
                "stats_type": "gambit",
                "stats": {"bling": bling, "dough_boosts": stats}
            }

    #####################
    ### $bread stonks ###
    #####################

    if content.startswith("Welcome to the stonk market!"):
        """
        Welcome to the stonk market, have a look around
        All the dough that brain of yours can think of can be found
        We've got mountains of cookies, some forty, they're best
        If none of it is going up it's time to divest

        Welcome to the stonk market, come and take a seat
        Would you like to see b6 or a3's incredible feat
        There's no need to panic, this isn't a test, haha
        Just invest at the peak and we'll do the rest
        """

        stats = {}
        
        search_result = extract("You have **## dough** to spend.")

        if search_result is None:
            return {"parse_successful": False}
        
        stats["total_dough"] = search_result

        for stonk in u_values.stonks:
            search_result = extract("&& - ## dough", emoji_discord=stonk.internal_emoji, emoji_ascii=stonk.emoji)

            if search_result is None:
                continue

            stats[f"{stonk.internal_emoji}_value"] = search_result

        return {
                "parse_successful": True,
                "stats_type": "stonks",
                "stats": stats
            }
    
    ########################
    ### $bread portfolio ###
    ########################

    if content.startswith("Investment portfolio for"):
        stats = {}

        bling = re.search("Investment portfolio for (<:\w+:\d+>)", content)

        if bling is not None:
            bling = bling.group(1)

            bling = u_values.bling_items.index(u_values.get_item(bling)) + 1
            
            stats["bling"] = bling
        else:
            stats["bling"] = 0

        for stonk in u_values.stonks:
            search_result = extract("&& -- ## stonks", emoji_discord=stonk.internal_emoji, emoji_ascii=stonk.emoji)
            
            if search_result is None:
                stats[stonk] = 0
                continue

            stats[stonk] = search_result

            stats[f"{stonk.internal_emoji}_value"] = extract("&& -- ## stonks, worth **## dough**", emoji_discord=stonk.internal_emoji, emoji_ascii=stonk.emoji, group_id=2)
        
        ## DETERMINING STONK VALUES ##
        
        for stonk in u_values.stonks:
            dough_value = stats.get(f"{stonk.internal_emoji}_value", None)

            # If dough_value is None then the key doesn't exist, which likely means the person doesn't have any of that stonk.
            if dough_value is None:
                continue

            dough_value //= stats[stonk]

            stats[f"{stonk.internal_emoji}_value"] = dough_value

        ##############################

        if len(stats) == 0:
            return {"parse_successful": False}

        return {
                "parse_successful": True,
                "stats_type": "portfolio",
                "stats": stats
            }
    
    #####################
    ### $bread invest ###
    #####################

    if content.startswith("You invested in "):
        dough_invested = extract("stonks for **## dough**.")
        stonks_gained = extract("You invested in ##")
        
        stonk_invested = None
        for stonk in u_values.stonks:
            if stonk.emoji in content or stonk.internal_emoji in content:
                stonk_invested = stonk.internal_emoji
                break
        
        stats = {
            "total_dough": extract("You have **## dough** remaining."),
            f"{stonk_invested}_value": dough_invested // stonks_gained
        }

        return {
            "parse_successful": True,
            "stats_type": "invest",
            "stats": stats
        }
    
    #####################
    ### $bread divest ###
    #####################
    # This one has two cases, for if you divest a specific amount or all of a stonk, and if you divest all your stonks.

    # If you divest a specific amount or all of a stonk.
    if content.startswith("You sold"):
        dough_divested = extract("stonks for **## dough**.")
        amount_divested = extract("You sold ##")

        total_dough = extract("You now have **## dough**")
        stonk_remaining = extract("and ##")

        stonk_invested = None
        for stonk in u_values.stonks:
            if stonk.emoji in content or stonk.internal_emoji in content:
                stonk_invested = stonk
                break
        
        stonk_value = dough_divested // amount_divested

        stats = {
            "total_dough": total_dough,
            stonk_invested: stonk_remaining,
            f"{stonk_invested.internal_emoji}_value": stonk_value
        }

        return {
            "parse_successful": True,
            "stats_type": "divest_specific",
            "stats": stats
        }
    
    # If you divest all your stonks.
    if content.startswith("You divested all of your stonks for"):
        return {
            "parse_successful": True,
            "stats_type": "divest_all",
            "stats": {
                "total_dough": extract("You now have **## dough**.")
            }
        }
    
    ####################
    ### $brick stats ###
    ####################

    if content.startswith("Brick stats for"):
        stats = {
            "bricks": extract("&& - ##", emoji_discord=":bricks:", emoji_ascii="🧱"),
            "brick_gold": extract("&& - ##", emoji_discord="<:brick_gold:971239215968944168>"),
            "total_bricks": extract("Total bricks: ##"),
            "total_timeout": extract("Total timeout: ## minute")
        }

        return {
            "parse_successful": True,
            "stats_type": "brick_stats",
            "stats": stats
        }
    
    # If nothing is found, say the parsing was unsuccessful.
    return {"parse_successful": False}

############################################################################################################################################

def get_stored_data(
        database: u_files.DatabaseInterface,
        user_id: int
    ) -> BreadDataAccount:
    """Gets a piece of stored data.

    Args:
        user_id (int): The user id to look up.

    Returns:
        BreadDataAccount: A BreadDataAccount object representing the data.
    """
    return BreadDataAccount(user_id, database)

def parse_gamble(message: discord.Message | str) -> list[typing.Type[u_values.Item]] | None:
    """Parses a gamble message to determine the items it contains. This will check if the message is a gamble via `utility.interface.is_gamble()`.

    Args:
        message (discord.Message): The gamble message to parse.

    Returns:
        list[typing.Type[u_values.Item]] | None: The items in the gamble, in order from left to right, top to bottom. None will be returned if the message is not a gamble.
    """
    if not u_interface.is_gamble(message):
        return None
    
    try:
        content = message.content
    except AttributeError:
        content = message
    
    raw = u_interface.remove_starting_ping(content).replace("\n", "").split(" ")

    return [u_values.get_item(item, "gamble_item") for item in raw]

def parse_roll(message: discord.Message) -> list[dict[str, str | int | list[typing.Type[u_values.Item]]]] | None:
    """Parses a message to determine the items it contains.

    Args:
        message (discord.Message): The message to parse.

    Returns:
        list[dict[str, str | int | list[typing.Type[u_values.Item]]]] | None: A list of dictionaries. Each inner dictionary contains the roll type under the key `type`, and the roll contents under `items`. `items` is a single roll in a compound roller message. This will return None if the message is not a bread roll. 
    """
    if not u_interface.is_bread_roll(message):
        return None
    
    by_roll = u_interface.remove_starting_ping(message.content).replace("\n", "").split("---")
    by_roll_raw = u_interface.remove_starting_ping(message.content).split("---")

    output = []

    for roll, raw in zip(by_roll, by_roll_raw):
        if len(roll) == 0:
            continue

        split = roll.split(" ")

        add = []

        for item in split:
            if len(item) == 0:
                continue
            
            add.append(u_values.get_item(item))

        first_line = raw.split("\n")[0]
        per_line_count = len(re.findall("(<a?)?:[\d\w_]+:(\d+>)?", first_line))
        if per_line_count == 10:
            roll_type = "lottery"
        elif per_line_count == 8:
            # That is not a bread roll, that is a chessatron completion.
            return None
        else:
            roll_type = len(add)
        
        output.append({
            "type": roll_type,
            "items": add
        })
    
    return output

    
