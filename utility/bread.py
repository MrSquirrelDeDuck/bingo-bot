"""Utility functions for working with the Bread Game."""

import discord
import re
import typing
import math
import datetime
import json
import random

# pip install pytz
import pytz

import utility.text as u_text
import utility.values as u_values
import utility.interface as u_interface
import utility.files as u_files
import utility.solvers as u_solvers
import utility.values as u_values

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
            item: typing.Type[u_values.Item] | str,
            default: typing.Any = 0
        ) -> int | typing.Any:
        if item in self.data:
            return self.data.get(item, default)

        if isinstance(item, u_values.Item):
            item = item.internal_emoji

        return self.data.get(item, default)
    
    def set(
            self: typing.Self,
            item: typing.Type[u_values.Item] | str,
            value: int | typing.Any
        ) -> None:
        if isinstance(item, u_values.Item):
            item = item.internal_emoji
            
        self.data[item] = value
    
    def increment(
            self: typing.Self,
            item: typing.Type[u_values.Item] | str,
            amount: int | typing.Any
        ) -> int:
        """Increments an item by an amount, returns the new value."""
        if isinstance(item, u_values.Item):
            item = item.internal_emoji
        
        self.data[item] = self.get(item, 0) + amount
        
        return self.get(item)
    
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
        # for key in data.copy():
        #     item = u_values.get_item(key)

        #     if item is None:
        #         continue

        #     data[item] = data.pop(key)

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
                    list_data[index] = value.internal_emoji
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
                    modify_key = key.internal_emoji
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
    def anarchy_tron_value(self: typing.Self) -> int:
        omegas = self.get(u_values.omega_chessatron)
        ascension = self.ascension
        shadowmegas = self.active_shadowmegas
        anarchy_omegas = self.get(u_values.anarchy_omega_chessatron)

        return calculate_anarchy_tron_value(
            ascension = ascension,
            omega_count = omegas,
            active_shadowmegas = shadowmegas,
            anarchy_omega_chessatron = anarchy_omegas
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
    
    @property
    def disallowed_recipes(self: typing.Self) -> list[str]:
        """Generates a list of alchemy recipes in the format `<item>_recipe_<recipe id>` that this account does not have the requirements for.
        
        Note that recipe ids are 1 indexed, so there will be no recipe 0."""
        out = []

        for item, recipes in u_values.alchemy_recipes.items():
            for recipe_id, recipe in enumerate(recipes, start=1):
                if "requirement" not in recipe:
                    continue

                for stat, amount in recipe.get("requirement", []):
                    if self.get(stat) < amount:
                        out.append(f"{item}_recipe_{recipe_id}")
                        break
        
        return out
    

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
        chessatron_contraption: int = 0,
        include_prestige_boost: bool = True
    ) -> int:
    """Calculates the value of a chessatron.

    Args:
        ascension (int, optional): The ascension the player is on. Defaults to 0.
        omega_count (int, optional): The number of omegas the player has. Defaults to 0.
        active_shadowmegas (int, optional): The number of active shadowmegas the player has, does not need to be provided if `shadowmegas` and `chessatron_contraption` is provided. Defaults to 0.
        shadowmegas (int, optional): The total number of shadowmegas the player has, not the number of active shadowmegas. This and `chessatron_contraption` can be provided or `active_shadowmegas` can be provided. Defaults to 0.
        chessatron_contraption (int, optional): The level of Chessatron Contraption the player has. This and `shadowmegas` can be provided or `active_shadowmegas` can be provided. Defaults to 0.
        include_prestige_boost (bool, optional): Whether to include the prestige boost in the calculation. Defaults to True.

    Returns:
        int: The amount of dough the player gets for each chessatron they make.
    """
    active_shadowmegas = max(active_shadowmegas, min(shadowmegas, chessatron_contraption * 5))

    out = (2000 + (100 * omega_count) * (1 + 0.02 * active_shadowmegas))
    
    if include_prestige_boost:
        out *= (1 + (0.1 * ascension))
        
    return round(out)

def calculate_anarchy_tron_value(
        ascension: int = 0,
        omega_count: int = 0,
        anarchy_omega_chessatron: int = 0,
        active_shadowmegas: int = 0,
        shadowmegas: int = 0,
        chessatron_contraption: int = 0,
        include_prestige_boost: bool = True
    ) -> int:
    """Calculates the value of an anarchy chessatron.

    Args:
        ascension (int, optional): The ascension the player is on. Defaults to 0.
        omega_count (int, optional): The number of omegas the player has. Defaults to 0.
        anarchy_omega_chessatron (int, optional): The number of anarchy omega chessatrons the player has. Defaults to 0.
        active_shadowmegas (int, optional): The number of active shadowmegas the player has, does not need to be provided if `shadowmegas` and `chessatron_contraption` is provided. Defaults to 0.
        shadowmegas (int, optional): The total number of shadowmegas the player has, not the number of active shadowmegas. This and `chessatron_contraption` can be provided or `active_shadowmegas` can be provided. Defaults to 0.
        chessatron_contraption (int, optional): The level of Chessatron Contraption the player has. This and `shadowmegas` can be provided or `active_shadowmegas` can be provided. Defaults to 0.
        include_prestige_boost (bool, optional): Whether to include the prestige boost in the calculation. Defaults to True.

    Returns:
        int: The amount of dough the player gets for each chessatron they make.
    """
    multiplier = 350 + (anarchy_omega_chessatron * 25)
    regular_tron = calculate_tron_value(ascension, omega_count, active_shadowmegas, shadowmegas, chessatron_contraption, include_prestige_boost=False)
    
    out = regular_tron * multiplier
    
    if include_prestige_boost:
        out *= (1 + (0.1 * ascension))
    
    return round(out)

def calculate_loaf_converter_cost(
        current: int,
        goal: int,
        self_converting_yeast: int = 0
    ) -> int:
    """Calculates the cumulative cost of getting from a number to a number of Loaf Converters.

    Args:
        current (int): The start number of Loaf Converters.
        goal (int): The ending number of Loaf Converters.
        self_converting_yeast (int, optional): The number of Self Converting Yeast levels. Defaults to 0.

    Returns:
        int: The amount of dough required to get from the current number of Loaf Converters to the goal.
    """
    # \left(g-c\right)\left(256-12s\right)c+\frac{\left(g-c\right)\left(g-c+1\right)\left(256-12s\right)}{2}
    return int(((goal - current) * (256 - (12 * self_converting_yeast)) * current) + (((goal - current) * ((goal - current) + 1) * (256 - (12 * self_converting_yeast))) // 2))

def calculate_maximum_trons(
        bking: int,
        bqueen: int,
        brook: int,
        bbishop: int,
        bknight: int,
        bpawn: int,
        wking: int,
        wqueen: int,
        wrook: int,
        wbishop: int,
        wknight: int,
        wpawn: int,
    ) -> dict[str | u_values.Item, int]:
    """Calculates the maximum number of trons that can be made with the given chess pieces. This works for both regular and anarchy pieces."""
    
    kings = (bking + wking) / 2
    queens = (bqueen + wqueen) / 2
    rooks = (brook + wrook) / 4
    bishops = (bbishop + wbishop) / 4
    knights = (bknight + wknight) / 4
    pawns = ((bpawn - wpawn) / 3 + wpawn) / 8
    
    return {
        "max": int(min(kings, queens, rooks, bishops, knights, pawns)),
        "kings": kings,
        "queens": queens,
        "rooks": rooks,
        "bishops": bishops,
        "knights": knights,
        "pawns": pawns
    }
    
def max_trons_regular(pieces: dict[typing.Type[u_values.Item], int]) -> dict[str | u_values.Item, int]:
    """Calculates the maximum number of trons that can be made with the given regular chess pieces.
    
    This calls calculate_maximum_trons, but allows you to pass a dict of items instead of individual values."""
    return calculate_maximum_trons(
        pieces.get(u_values.bking, 0),
        pieces.get(u_values.bqueen, 0),
        pieces.get(u_values.brook, 0),
        pieces.get(u_values.bbishop, 0),
        pieces.get(u_values.bknight, 0),
        pieces.get(u_values.bpawn, 0),
        pieces.get(u_values.wking, 0),
        pieces.get(u_values.wqueen, 0),
        pieces.get(u_values.wrook, 0),
        pieces.get(u_values.wbishop, 0),
        pieces.get(u_values.wknight, 0),
        pieces.get(u_values.wpawn, 0)
    )
    
def max_trons_anarchy(pieces: dict[typing.Type[u_values.Item], int]) -> dict[str | u_values.Item, int]:
    """Calculates the maximum number of trons that can be made with the given anarchy chess pieces.
    
    This calls calculate_maximum_trons, but allows you to pass a dict of items instead of individual values."""
    return calculate_maximum_trons(
        pieces.get(u_values.bking_anarchy, 0),
        pieces.get(u_values.bqueen_anarchy, 0),
        pieces.get(u_values.brook_anarchy, 0),
        pieces.get(u_values.bbishop_anarchy, 0),
        pieces.get(u_values.bknight_anarchy, 0),
        pieces.get(u_values.bpawn_anarchy, 0),
        pieces.get(u_values.wking_anarchy, 0),
        pieces.get(u_values.wqueen_anarchy, 0),
        pieces.get(u_values.wrook_anarchy, 0),
        pieces.get(u_values.wbishop_anarchy, 0),
        pieces.get(u_values.wknight_anarchy, 0),
        pieces.get(u_values.wpawn_anarchy, 0)
    )

def regular_iterative_tronning(
        starting_chess_pieces: dict[typing.Type[u_values.Item], int],
        starting_omega_items: dict[typing.Type[u_values.Item], int],
        ascension: int = 0, # a
        active_shadowmegas: int = 0, # c
        starting_omegas: int = 0, # p
    ) -> dict[str, int]:
    """Calculates the results of iterative tronning with regular chessatrons.
    
    Args:
        starting_chess_pieces (dict[typing.Type[u_values.Item], int]): The starting chess pieces.
        starting_omega_items (dict[typing.Type[u_values.Item], int]): The starting omega items.
        ascension (int, optional): The ascension the player is on. Defaults to 0.
        active_shadowmegas (int, optional): The number of active shadowmegas the player has. Defaults to 0.
        starting_omegas (int, optional): The number of omegas the player has. Defaults to 0.
        
    Returns:
        dict[str, int]: The resulting data if iterative tronning were to happen."""
    # Equation:
    # \left(\left(\left(t-5k\right)\left(2000\ +\ 100\left(k+p\right)\cdot\left(1+0.02c\right)\right)\right)+5\left(2000k+100\left(1+0.02c\right)\left(\frac{k\left(k-1\right)}{2}+pk\right)\right)+40000k\right)\left(1+0.1a\right)
    
    # Prepare the data.
    max_omegas = min(starting_omega_items.values()) # o
    
    max_trons = max_trons_regular(starting_chess_pieces)["max"] # t
    
    m = min(max_trons, max_omegas * 5)
    k = int(m // 5)
    remaining_trons = (max_trons - (5 * k))
    
    # \left(\left(t-5k\right)\left(2000\ +\ 100\left(k+p\right)\cdot\left(1+0.02c\right)\right)\right)
    leftover_trons = remaining_trons * (2000 + 100 * (k + starting_omegas) * (1 + 0.02 * active_shadowmegas))
    
    # 5\left(2000k+100\left(1+0.02c\right)\left(\frac{k\left(k-1\right)}{2}+pk\right)\right)
    main_trons = 5 * (2000 * k + 100 * (1 + 0.02 * active_shadowmegas) * ((k * (k - 1) // 2) + (starting_omegas * k)))
    
    # 40000k
    omegas_made = 40000 * k
    
    # \left(1+0.1a\right)
    ascension_multiplier = 1 + (0.1 * ascension)
    
    total_dough_made = (leftover_trons + main_trons + omegas_made) * ascension_multiplier
    
    return {
        "dough_gained": total_dough_made,
        "omegas_made": k,
        "extra_trons": remaining_trons,
        "total_trons": max_trons
    }

def anarchy_iterative_tronning(
        starting_anarchy_pieces: dict[typing.Type[u_values.Item], int],
        starting_omega_items: dict[typing.Type[u_values.Item], int],
        ascension: int = 0, # a
        active_shadowmegas: int = 0, # s
        starting_omegas: int = 0, # u
        starting_anarchy_omegas: int = 0, # p
    ) -> dict[str, int]:
    """Calculates the results of iterative tronning with regular chessatrons.
    
    Args:
        starting_anarchy_pieces (dict[typing.Type[u_values.Item], int]): The starting anarchy pieces.
        starting_omega_items (dict[typing.Type[u_values.Item], int]): The starting omega items.
        ascension (int, optional): The ascension the player is on. Defaults to 0.
        active_shadowmegas (int, optional): The number of active shadowmegas the player has. Defaults to 0.
        starting_omegas (int, optional): The number of omegas the player has. Defaults to 0.
        starting_anarchy_omegas (int, optional): The number of anarchy omegas the player has. Defaults to 0.
        
    Returns:
        dict[str, int]: The resulting data if iterative tronning were to happen."""
    # Equation:
    # \left(\left(\left(t-5k\right)g\left(k+p,\ u-k,\ s\right)\right)+5\left(700000k+50000\left(\frac{k\left(k-1\right)}{2}+pk\right)+35000\left(1+0.02s\right)\left(uk-\frac{k\left(k-1\right)}{2}\right)+2500\left(1+0.02s\right)\left(u\left(\frac{k\left(k-1\right)}{2}+pk\right)-\left(\frac{\left(k-1\right)k\left(2k-1\right)}{6}+p\frac{k\left(k-1\right)}{2}\right)\right)\right)+31004150k\right)\left(1+0.1a\right)
    
    # Prepare the data.
    max_anarchy_omegas = min(
        starting_omega_items.get(u_values.chessatron, 0) // 25,
        starting_omegas
    )
    
    max_trons = max_trons_anarchy(starting_anarchy_pieces)["max"] # t
    
    k = int(min(max_trons, max_anarchy_omegas * 5) // 5)
    remaining_trons = (max_trons - (5 * k))
    
    # \left(\left(t-5k\right)g\left(k+p,\ u-k,\ s\right)\right)
    leftover_trons = remaining_trons * calculate_anarchy_tron_value(
        ascension = ascension,
        omega_count = starting_omegas - k,
        anarchy_omega_chessatron = starting_anarchy_omegas + k,
        active_shadowmegas = active_shadowmegas,
        include_prestige_boost = False
    )
    
    # 5\left(700000k+50000\left(\frac{k\left(k-1\right)}{2}+pk\right)+35000\left(1+0.02s\right)\left(uk-\frac{k\left(k-1\right)}{2}\right)+2500\left(1+0.02s\right)\left(u\left(\frac{k\left(k-1\right)}{2}+pk\right)-\left(\frac{\left(k-1\right)k\left(2k-1\right)}{6}+p\frac{k\left(k-1\right)}{2}\right)\right)\right)
    main_trons = 5 * (700_000 * k + 50_000 * ((k * (k - 1)) // 2 + starting_anarchy_omegas * k) + 35_000 * (1 + 0.02 * active_shadowmegas) * (starting_omegas * k - ((k * (k - 1)) // 2)) + 2_500 * (1 + 0.02 * active_shadowmegas) * (starting_omegas * (((k * (k - 1)) // 2) + (starting_anarchy_omegas * k)) - ((((k - 1) * k * (2 * k - 1)) // 6) + (starting_anarchy_omegas * (k * (k - 1)) // 2))))
    
    # 31004150k
    omegas_made = 31004150 * k # hehe
    
    # \left(1+0.1a\right)
    ascension_multiplier = 1 + (0.1 * ascension)
    
    total_dough_made = (leftover_trons + main_trons + omegas_made) * ascension_multiplier
    
    return {
        "dough_gained": total_dough_made,
        "omegas_made": k,
        "extra_trons": remaining_trons,
        "total_trons": max_trons
    }

def get_ascension(
        tokens: int = 0,
        ddc: int = 0,
        scy: int = 0,
        mb: int = 0,
        cpe: int = 0,
        hrt: int = 0,
        cc: int = 0,
        es: int = 0,
        fcotd: int = 0,
        fr: int = 0,
        cn: int = 0
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
        fr (int, optional): Level of Fuel Refinement. Defaults to 0.
        cn (int, optional): Level of Corruption Negation. Defaults to 0.

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
        int((fr + 4) / 4) * fr - 4 * (int(fr / 4) * (int(fr / 4) + 1) / 2), # FR
        int((cn + 2) / 2) * cn - 2 * (int(cn / 2) * (int(cn / 2) + 1) / 2), # CN
        tokens
    ]

    token_sum = sum(token_list)

    return int(((token_sum - 31) / 6 + 6 if token_sum-1 > 30 else (token_sum - 1) / 5) + 1)

async def parse_attempt(
        message: discord.Message,
        require_reply: bool = False,
        require_stats: bool = True,
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

    if not replied_to.content.startswith("Stats for:") and require_stats:
        return False
    
    if custom_check is not None:
        if custom_check(replied_to):
            return False
                    
    return await parse_stats(message.reference.resolved)
    








###############################################################
##### STATS PARSER ############################################
###############################################################

async def parse_stats(message: discord.Message) -> dict[str | typing.Type[u_values.Item], int | dict[str, bool] | bool]:
    """Parses a Machine-Mind message and returns a dict of as many stats as it can figure out, both user stats and internal stats, like stonks, will be returned in the `stats` dict.
    
    The following messages can be parsed:
    - $bread stats (Main, individual items if it's split, and continued.)
    - $bread stats chess
    - $bread stats gambit
    - $bread stats space
    - $bread portfolio
    - $bread invest
    - $bread divest
    - $bread shop
    - $bread hidden
    - $bread dough
    - $bread stonks
    - $bread export
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
    - "space": `$bread stats space`.
    - "stonks": `$bread stonks`.
    - "portfolio": `$bread portfolio`.
    - "invest": `$bread invest`.
    - "divest_specific": `$bread divest [all|amount] [stonk]`.
    - "divest_all": `$bread divest all`.
    - "brick_stats": `$brick stats`.
    - "dump": `$bread export`.
    """

    content = message.content
    
    ###################
    ### $bread dump ###
    ###################

    if len(content) == 0:
        text_dict = None

        for attachment in message.attachments:
            if attachment.filename != "export.json":
                continue

            attachment_bytes = await attachment.read()

            text_dict = json.loads(attachment_bytes)
            
            for key in text_dict.copy():
                item = u_values.get_item(key)
                
                if item is None:
                    continue
                
                text_dict[item] = text_dict.pop(key)
        
        if text_dict is not None:
            return {
                "parse_successful": True,
                "stats_type": "dump",
                "stats": text_dict
            }
        

    
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
        else:
            pattern = pattern.replace("##", "([\d,]+)").replace("&&", emoji_discord)

        search_result = re.search(pattern, text)

        if search_result is None:
            if emoji_ascii == "":
                return default
            
            pattern = surrounding
            if escape:
                pattern = re.escape(pattern)
                pattern = pattern.replace("\#\#", "([\d,]+)").replace("\&\&", emoji_ascii)
            else:
                pattern = pattern.replace("##", "([\d,]+)").replace("&&", emoji_ascii)

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
        fuel_refinement = extract("more fuel with ## level", default = 0)
        corruption_negation = extract("lower chance of a loaf becoming corrupted with ## level", default = 0)

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
            "fuel_refinement": fuel_refinement,
            "corruption_negation": corruption_negation,
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

        ascension_token_count = extract(f"You have **## {u_values.ascension_token.internal_emoji}**.", default=0)

        daily_discount_card = (124 - extract("Reduces the cost of a daily roll by ##, to ##.", group_id=2, default = 4)) // 4
        self_converting_yeast = (244 - extract("Reduces the cost of each loaf converter level by ##, to ##.", group_id=2, default = 16)) // 12
        moak_booster = extract("Increases the chances of finding a MoaK by ##%, to ##% of base.", group_id=2)
        chess_piece_equalizer = extract("Every Chess piece will have an increased chance of being white, to ##%.")
        high_roller_table = extract("Join the high roller table. Increases your maximum bid while gambling to ##.")
        chessatron_contraption = extract("for each shadowmega chessatron you own. Works for up to ## shadowmega chessatrons.", default = 250) // 5 - 1
        ethereal_shine = extract("Allows your shadow gold gems to help you find new gems. Up to ## shadow gold gems will", default = 500) // 10 - 1
        first_catch_of_the_day = extract("The first ## special items you find each day will be", default = -1) - 1
        fuel_refinement = extract("Increases the amount of fuel you create to ##% of base.")
        corruption_negation = extract("Decreases the amount of corrupted loaves by ##%, to ##% of base.", group_id=2)

        if fuel_refinement is None:
            # If it's in the message, but the part about it is the "here's what you must do" thing.
            if "Fuel Refinement" in content:
                fuel_refinement = 0
            else:
                fuel_refinement = 8
        else:
            fuel_refinement = (fuel_refinement - 100) // 25 - 1

        if corruption_negation is None:
            # If it's in the message, but the part about it is the "here's what you must do" thing.
            if "Corruption Negation" in content:
                corruption_negation = 0
            else:
                corruption_negation = 5
        else:
            corruption_negation = (100 - corruption_negation) // 10 - 1

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
        
        ascension_number = get_ascension(
            tokens = ascension_token_count,
            ddc = daily_discount_card,
            scy = self_converting_yeast,
            mb = moak_booster,
            cpe = chess_piece_equalizer,
            hrt = high_roller_table,
            cc = chessatron_contraption,
            es = ethereal_shine,
            fcotd = first_catch_of_the_day,
            fr = fuel_refinement,
            cn = corruption_negation,
        )

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
            "fuel_refinement": fuel_refinement,
            "corruption_negation": corruption_negation
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

        for chess_piece in u_values.every_chess_piece:
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

    ##########################
    ### $bread stats space ###
    ##########################
    
    if content.startswith("Space stats for:"):
        stats = {}
        
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
        
        ######

        parse_list = {
            "space_level": "You have a tier ## Bread Rocket",
            "autopilot_level": "With a level ## autopilot",
            "fuel_tank": "with ## Fuel Tank level(s?)",
            "fuel_research": "By having ## level(s?) of fuel research",
            "telescope_level": "With ## telescope level(s?)",
            "advanced_exploration": "With ## level(s?) of Advanced Exploration",
            "engine_efficiency": "less fuel with ## level(s?) of Engine Efficiency",
            "trade_hubs_created": "Throughout your time in space you've created ## Trade",
            "projects_completed": "and helped contribute to ## completed project"
        }

        for key, value in parse_list.items():
            direct(key, value, default=0, escape=False)

        if len(stats) == 0:
            return {"parse_successful": False}

        return {
            "parse_successful": True,
            "stats_type": "space",
            "stats": stats
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
    return {"parse_successful": False, "stats_type": None}

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

    
def calculate_rolling_odds(
        priority: str,
        tile_seed: str,
        day_seed: str,
        planet_deviation: float = None,
        in_nebula: bool = False,
        black_hole: bool = False,
        effective_deviation: float = None
    ) -> dict[str, dict[str, float] | float]:
    odds = {
        "special_bread": 1,
        "rare_bread": 1,
        "chess_piece": 1,
        "gem_red": 1,
        "gem_blue": 1,
        "gem_purple": 1,
        "gem_green": 1,
        "gem_gold": 1,
        "anarchy_chess": 1,
        "anarchy_piece": 1
    }

    if effective_deviation is None:
        if in_nebula:
            denominator = 1
        else:
            denominator = math.tau

        if black_hole:
            # If it's a black hole, make it a little crazier by dividing the denominator by 5.
            denominator /= 5

        deviation = (1 - planet_deviation) / denominator
    else:
        deviation = effective_deviation

    raw_seed = tile_seed
    tile_seed = tile_seed + day_seed

    sqrt_phi = math.sqrt((1 + math.sqrt(5)) / 2)

    # Get the planet seed for each category.
    # These do not change per day.
    for key in odds.copy():
        odds[key] = random.Random(f"{raw_seed}{key}").gauss(mu=1, sigma=deviation)

        if key == priority:
            odds[key] = (abs(odds[key] - 1) + 1) * sqrt_phi

    # Now to get the actual modifiers.
    # These do change per day, but tend to be around the default seeds calculated above.
    for key, value in odds.copy().items():
        sigma = deviation / 2.5

        if key == priority:
            sigma = deviation / 1.5

        odds[key] = random.Random(f"{tile_seed}{key}").gauss(mu=value, sigma=sigma)

        # Incredibly unlikely to be an issue, but this forces the priority item to be greater than 1.
        # This prevents the priority item from being less common than normal.
        if key == priority and odds[key] < 1:
            odds[key] = abs(odds[key] - 1) + 1
    
    return {
        "odds": odds,
        "deviation": deviation
    }