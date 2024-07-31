"""Utilities and constants for the Hypixel Skyblock related utility commands."""

import typing

class HotmPerk:
    def __init__(
            self: typing.Self,
            name: str,
            cost_type: str,
            hotm_level: int,
            max_level: int = None,
            cost_formula: typing.Callable[[int], int] = None
        ) -> None:
        self.name = name
        self.cost_type = cost_type
        self.hotm_level = hotm_level

        if max_level is None:
            self.max_level = 1
        else:
            self.max_level = max_level
        
        if cost_formula is None:
            self.cost_formula = lambda l: 0
        else:
            self.cost_formula = cost_formula
    
    def __str__(self: typing.Self):
        return self.name
    
    def __repr__(self: typing.Self):
        return self.__str__()

    def formatted_cost(
            self: typing.Self,
            level: int
        ) -> str:
        if level == 1:
            item = "Token of the Mountain"
        else:
            item = self.cost_type
        
        return f"{self.get_cost(level)} {item}"
    
    def get_cost(
            self: typing.Self,
            level: int
        ) -> int:
        return self.cost_formula(level)
    
    def get_cost_sum(
            self: typing.Self,
            start: int,
            end: int
        ) -> int:
        costs = [self.get_cost(level) for level in range(start + 1, end + 1)]

        return sum(costs)

#################################################################################################
#### HOTM PERKS #################################################################################
#################################################################################################

# HotM 1

Mining_Speed = HotmPerk(
    name = "Mining Speed",
    cost_formula = lambda l: (l + 1) ** 3,
    cost_type = "Mithril Powder",
    hotm_level = 1,
    max_level = 50
)

# HotM 2

Mining_Fortune = HotmPerk(
    name = "Mining Fortune",
    cost_formula = lambda l: (l + 1) ** 3.05,
    cost_type = "Mithril Powder",
    hotm_level = 2,
    max_level = 50
)

Quick_Forge = HotmPerk(
    name = "Quick Forge",
    cost_formula = lambda l: (l + 1) ** 4,
    cost_type = "Mithril Powder",
    hotm_level = 2,
    max_level = 20
)

Titanium_Insanium = HotmPerk(
    name = "Titanium Insanium",
    cost_formula = lambda l: (l + 1) ** 3.1,
    cost_type = "Mithril Powder",
    hotm_level = 2,
    max_level = 50
)

Pickobulus = HotmPerk(
    name = "Pickobulus",
    cost_type = "Mithril Powder",
    hotm_level = 2
)

Mining_Speed_Boost = HotmPerk(
    name = "Mining Speed Boost",
    cost_type = "Mithril Powder",
    hotm_level = 2
)

# HotM 3

Daily_Powder = HotmPerk(
    name = "Daily Powder",
    cost_formula = lambda l: 200 + ((l + 1) * 18),
    cost_type = "Mithril Powder",
    hotm_level = 3,
    max_level = 100
)

Luck_of_the_Cave = HotmPerk(
    name = "Luck of the Cave",
    cost_formula = lambda l: (l + 1) ** 3.07,
    cost_type = "Mithril Powder",
    hotm_level = 3,
    max_level = 45
)

Crystallized = HotmPerk(
    name = "Crystallized",
    cost_formula = lambda l: (l + 1) ** 3.4,
    cost_type = "Mithril Powder",
    hotm_level = 3,
    max_level = 30
)

# HotM 4

Efficient_Miner = HotmPerk(
    name = "Efficient Miner",
    cost_formula = lambda l: (l + 1) ** 2.6,
    cost_type = "Mithril Powder",
    hotm_level = 4,
    max_level = 100
)

Mining_Madness = HotmPerk(
    name = "Mining Madness",
    cost_type = "Mithril Powder",
    hotm_level = 4
)

Sky_Mall = HotmPerk(
    name = "Sky Mall",
    cost_type = "Mithril Powder",
    hotm_level = 4
)

Orbiter = HotmPerk(
    name = "Orbiter",
    cost_formula = lambda l: l * 70,
    cost_type = "Mithril Powder",
    hotm_level = 4,
    max_level = 80
)

Precision_Mining = HotmPerk(
    name = "Precision Mining",
    cost_type = "Mithril Powder",
    hotm_level = 4
)

Seasoned_Mineman = HotmPerk(
    name = "Seasoned Mineman",
    cost_formula = lambda l: (l + 1) ** 2.3,
    cost_type = "Mithril Powder",
    hotm_level = 4,
    max_level = 100
)

Front_Loaded = HotmPerk(
    name = "Front Loaded",
    cost_type = "Mithril Powder",
    hotm_level = 4
)

# HotM 5

Star_Powder = HotmPerk(
    name = "Star Powder",
    cost_type = "Mithril Powder",
    hotm_level = 5
)

Goblin_Killer = HotmPerk(
    name = "Goblin Killer",
    cost_type = "Mithril Powder",
    hotm_level = 5
)

# HotM 6

Mole = HotmPerk(
    name = "Mole",
    cost_formula = lambda l: (l + 1) ** 2.2,
    cost_type = "Gemstone Powder",
    hotm_level = 6,
    max_level = 190
)

Profesional = HotmPerk(
    name = "Professional",
    cost_formula = lambda l: (l + 1) ** 2.3,
    cost_type = "Gemstone Powder",
    hotm_level = 6,
    max_level = 140
)

Lonesome_Miner = HotmPerk(
    name = "Lonesome Miner",
    cost_formula = lambda l: (l + 1) ** 3.07,
    cost_type = "Gemstone Powder",
    hotm_level = 6,
    max_level = 45
)

Great_Explorer = HotmPerk(
    name = "Great Explorer",
    cost_formula = lambda l: (l + 1) ** 4,
    cost_type = "Gemstone Powder",
    hotm_level = 6,
    max_level = 20
)

Vein_Seeker = HotmPerk(
    name = "Vein Seeker",
    cost_type = "Gemstone Powder",
    hotm_level = 6
)

Fortunate = HotmPerk(
    name = "Fortunate",
    cost_formula = lambda l: (l + 1) ** 3.05,
    cost_type = "Mithril Powder",
    hotm_level = 6,
    max_level = 20
)

Maniac_Miner = HotmPerk(
    name = "Maniac Miner",
    cost_type = "Gemstone Powder",
    hotm_level = 6
)

# HotM 7

Powder_Buff = HotmPerk(
    name = "Powder Buff",
    cost_formula = lambda l: (l + 1) ** 3.2,
    cost_type = "Gemstone Powder",
    hotm_level = 7,
    max_level = 50
)

Mining_Speed_2 = HotmPerk(
    name = "Mining Speed 2",
    cost_formula = lambda l: (l + 1) ** 3.2,
    cost_type = "Gemstone Powder",
    hotm_level = 7,
    max_level = 50
)

Mining_Fortune_2 = HotmPerk(
    name = "Mining Fortune 2",
    cost_formula = lambda l: (l + 1) ** 3.2,
    cost_type = "Gemstone Powder",
    hotm_level = 7,
    max_level = 50
)

# HotM 8

Daily_Grind = HotmPerk(
    name = "Daily Grind",
    cost_formula = lambda l: 200 + ((l - 1) * 18),
    cost_type = "Glacite Powder",
    hotm_level = 8,
    max_level = 100
)

Dust_Collector = HotmPerk(
    name = "Dust Collector",
    cost_formula = lambda l: (l + 1) ** 4,
    cost_type = "Glacite Powder",
    hotm_level = 8,
    max_level = 20
)

Warm_Hearted = HotmPerk(
    name = "Warm Hearted",
    cost_formula = lambda l: (l + 1) ** 3.1,
    cost_type = "Glacite Powder",
    hotm_level = 8,
    max_level = 50
)

Keen_Eye = HotmPerk(
    name = "Keen Eye",
    cost_type = "Glacite Powder",
    hotm_level = 8
)

Strong_Arm = HotmPerk(
    name = "Strong Arm",
    cost_formula = lambda l: (l + 1) ** 2.3,
    cost_type = "Glacite Powder",
    hotm_level = 8,
    max_level = 100
)

No_Stone_Unturned = HotmPerk(
    name = "No Stone Unturned",
    cost_formula = lambda l: (l + 1) ** 3.05,
    cost_type = "Glacite Powder",
    hotm_level = 8,
    max_level = 50
)

Mineshaft_Mayhem = HotmPerk(
    name = "Mineshaft Mayhem",
    cost_type = "Glacite Powder",
    hotm_level = 8
)

# HotM 9

SubZero_Mining = HotmPerk(
    name = "SubZero Mining",
    cost_formula = lambda l: (l + 1) ** 2.3,
    cost_type = "Glacite Powder",
    hotm_level = 9,
    max_level = 100
)

Surveyor = HotmPerk(
    name = "Surveyor",
    cost_formula = lambda l: (l + 1) ** 4,
    cost_type = "Glacite Powder",
    hotm_level = 9,
    max_level = 20
)

Eager_Adventurer = HotmPerk(
    name = "Eager Adventurer",
    cost_formula = lambda l: (l + 1) ** 2.3,
    cost_type = "Glacite Powder",
    hotm_level = 9,
    max_level = 100
)

# HotM 10

Dead_Mans_Chest = HotmPerk(
    name = "Dead Man's Chest",
    cost_formula = lambda l: (l + 1) ** 3.2,
    cost_type = "Glacite Powder",
    hotm_level = 10,
    max_level = 50
)

Frozen_Solid = HotmPerk(
    name = "Frozen Solid",
    cost_type = "Glacite Powder",
    hotm_level = 10
)

Gifts_from_the_Departed = HotmPerk(
    name = "Gifts from the Departed",
    cost_formula = lambda l: (l + 1) ** 2.45,
    cost_type = "Glacite Powder",
    hotm_level = 10,
    max_level = 100
)

Gemstone_Infusion = HotmPerk(
    name = "Gemstone Infusion",
    cost_type = "Glacite Powder",
    hotm_level = 10
)

Excavator = HotmPerk(
    name = "Excavator",
    cost_formula = lambda l: (l + 1) ** 3,
    cost_type = "Glacite Powder",
    hotm_level = 10,
    max_level = 50
)

Rags_to_Riches = HotmPerk(
    name = "Rags to Riches",
    cost_formula = lambda l: (l + 1) ** 3.05,
    cost_type = "Glacite Powder",
    hotm_level = 10,
    max_level = 50
)

Hazardous_Miner = HotmPerk(
    name = "Hazardous Miner",
    cost_type = "Glacite Powder",
    hotm_level = 10
)

#######

all_hotm_perks = [
    Mining_Speed, # HotM 1
    Mining_Fortune, Quick_Forge, Titanium_Insanium, Pickobulus, Mining_Speed_Boost, # HotM 2
    Daily_Powder, Luck_of_the_Cave, Crystallized, # HotM 3
    Efficient_Miner, Mining_Madness, Sky_Mall, Orbiter, Precision_Mining, Seasoned_Mineman, Front_Loaded, # HotM 4
    Star_Powder, Goblin_Killer, # HotM 5
    Mole, Profesional, Lonesome_Miner, Great_Explorer, Vein_Seeker, Fortunate, Maniac_Miner, # HotM 6
    Powder_Buff, Mining_Speed_2, Mining_Fortune_2, # HotM 7
    Daily_Grind, Dust_Collector, Warm_Hearted, Keen_Eye, Strong_Arm, No_Stone_Unturned, Mineshaft_Mayhem, # HotM 8
    SubZero_Mining, Surveyor, Eager_Adventurer, # HotM 9
    Dead_Mans_Chest, Frozen_Solid, Gifts_from_the_Departed, Gemstone_Infusion, Excavator, Rags_to_Riches, Hazardous_Miner, # HotM 10
]