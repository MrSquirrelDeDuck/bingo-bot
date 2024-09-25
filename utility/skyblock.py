"""Utilities and constants for the Hypixel Skyblock related utility commands."""

import typing

Powder = str
MITHRIL_POWDER = "Mithril Powder"
GEMSTONE_POWDER = "Gemstone Powder"
GLACITE_POWDER = "Glacite Powder"

class HotmPerk:
    def __init__(
            self: typing.Self,
            name: str,
            cost_type: Powder,
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
        return int(self.cost_formula(level))
    
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
    cost_type = MITHRIL_POWDER,
    hotm_level = 1,
    max_level = 50
)

# HotM 2

Mining_Speed_Boost = HotmPerk(
    name = "Mining Speed Boost",
    cost_type = MITHRIL_POWDER,
    hotm_level = 2
)

Precision_Mining = HotmPerk(
    name = "Precision Mining",
    cost_type = MITHRIL_POWDER,
    hotm_level = 2
)

Mining_Fortune = HotmPerk(
    name = "Mining Fortune",
    cost_formula = lambda l: (l + 1) ** 3.05,
    cost_type = MITHRIL_POWDER,
    hotm_level = 2,
    max_level = 50
)

Titanium_Insanium = HotmPerk(
    name = "Titanium_Insanium",
    cost_formula = lambda l: (l + 1) ** 3.1,
    cost_type = MITHRIL_POWDER,
    hotm_level = 2,
    max_level = 50
)

Pickobulus = HotmPerk(
    name = "Pickobulus",
    cost_type = MITHRIL_POWDER,
    hotm_level = 2
)

# HotM 3

Luck_of_the_Cave = HotmPerk(
    name = "Luck of the Cave",
    cost_formula = lambda l: (l + 1) ** 3.07,
    cost_type = MITHRIL_POWDER,
    hotm_level = 3,
    max_level = 45
)

Efficient_Miner = HotmPerk(
    name = "Efficient Miner",
    cost_formula = lambda l: (l + 1) ** 2.6,
    cost_type = MITHRIL_POWDER,
    hotm_level = 3,
    max_level = 100
)

Quick_Forge = HotmPerk(
    name = "Quick Forge",
    cost_formula = lambda l: (l + 1) ** 3.2,
    cost_type = MITHRIL_POWDER,
    hotm_level = 3,
    max_level = 20
)

# HotM 4

Sky_Mall = HotmPerk(
    name = "Sky Mall",
    cost_type = GEMSTONE_POWDER,
    hotm_level = 4
)

Old_School = HotmPerk(
    name = "Old-School",
    cost_formula = lambda l: (l + 1) ** 4,
    cost_type = GEMSTONE_POWDER,
    hotm_level = 4,
    max_level = 20
)

Professional = HotmPerk(
    name = "Professional",
    cost_formula = lambda l: (l + 1) ** 2.3,
    cost_type = GEMSTONE_POWDER,
    hotm_level = 4,
    max_level = 140
)

Mole = HotmPerk(
    name = "Mole",
    cost_formula = lambda l: (l + 1) ** 2.2,
    cost_type = GEMSTONE_POWDER,
    hotm_level = 4,
    max_level = 200
)

Gem_Lover = HotmPerk(
    name = "Gem Lover",
    cost_formula = lambda l: (l + 1) ** 4,
    cost_type = GEMSTONE_POWDER,
    hotm_level = 4,
    max_level = 20
)

Seasoned_Mineman = HotmPerk(
    name = "Seasoned Mineman",
    cost_formula = lambda l: (l + 1) ** 2.3,
    cost_type = GEMSTONE_POWDER,
    hotm_level = 4,
    max_level = 100
)

Front_Loaded = HotmPerk(
    name = "Front Loaded",
    cost_type = GEMSTONE_POWDER,
    hotm_level = 4
)

# HotM 5

Daily_Grind = HotmPerk(
    name = "Daily Grind",
    cost_type = GEMSTONE_POWDER,
    hotm_level = 5
)

Daily_Powder = HotmPerk(
    name = "Daily Powder",
    cost_type = GEMSTONE_POWDER,
    hotm_level = 5
)

# HotM 6

Anomalous_Desire = HotmPerk(
    name = "Anomalous Desire",
    cost_type = GEMSTONE_POWDER,
    hotm_level = 6
)

Blockhead = HotmPerk(
    name = "Blockhead",
    cost_formula = lambda l: (l + 1) ** 4,
    cost_type = GEMSTONE_POWDER,
    hotm_level = 6,
    max_level = 20
)

Subterranean_Fisher = HotmPerk(
    name = "Subterranean Fisher",
    cost_formula = lambda l: (l + 1) ** 3.07,
    cost_type = GEMSTONE_POWDER,
    hotm_level = 6,
    max_level = 40
)

Keep_it_Cool = HotmPerk(
    name = "Keep it Cool",
    cost_formula = lambda l: (l + 1) ** 3.07,
    cost_type = GEMSTONE_POWDER,
    hotm_level = 6,
    max_level = 50
)

Lonesome_Miner = HotmPerk(
    name = "Lonesome Miner",
    cost_formula = lambda l: (l + 1) ** 3.07,
    cost_type = GEMSTONE_POWDER,
    hotm_level = 6,
    max_level = 45
)

Great_Explorer = HotmPerk(
    name = "Great Explorer",
    cost_formula = lambda l: (l + 1) ** 4,
    cost_type = GEMSTONE_POWDER,
    hotm_level = 6,
    max_level = 20
)

Maniac_Miner = HotmPerk(
    name = "Maniac Miner",
    cost_type = GEMSTONE_POWDER,
    hotm_level = 6
)

# HotM 7

Speedy_Mineman = HotmPerk(
    name = "Speedy Mineman",
    cost_formula = lambda l: (l + 1) ** 3.2,
    cost_type = GEMSTONE_POWDER,
    hotm_level = 7,
    max_level = 50
)

Powder_Buff = HotmPerk(
    name = "Powder Buff",
    cost_formula = lambda l: (l + 1) ** 3.2,
    cost_type = GEMSTONE_POWDER,
    hotm_level = 7,
    max_level = 50
)

Fortunate_Mineman = HotmPerk(
    name = "Fortunate Mineman",
    cost_formula = lambda l: (l + 1) ** 3.2,
    cost_type = GEMSTONE_POWDER,
    hotm_level = 7,
    max_level = 50
)

# HotM 8

Miners_Blessing = HotmPerk(
    name = "Miner's Blessing",
    cost_type = GLACITE_POWDER,
    hotm_level = 8
)

No_Stone_Unturned = HotmPerk(
    name = "No Stone Unturned",
    cost_formula = lambda l: (l + 1) ** 3.05,
    cost_type = GLACITE_POWDER,
    hotm_level = 8,
    max_level = 50
)

Strong_Arm = HotmPerk(
    name = "Strong Arm",
    cost_formula = lambda l: (l + 1) ** 2.3,
    cost_type = GLACITE_POWDER,
    hotm_level = 8,
    max_level = 100
)

Steady_Hand = HotmPerk(
    name = "Steady Hand",
    cost_formula = lambda l: (l + 1) ** 2.6,
    cost_type = GLACITE_POWDER,
    hotm_level = 8,
    max_level = 100
)

Warm_Hearted = HotmPerk(
    name = "Warm Hearted",
    cost_formula = lambda l: (l + 1) ** 3.1,
    cost_type = GLACITE_POWDER,
    hotm_level = 8,
    max_level = 50
)

Surveyor = HotmPerk(
    name = "Surveyor",
    cost_formula = lambda l: (l + 1) ** 4,
    cost_type = GLACITE_POWDER,
    hotm_level = 8,
    max_level = 20
)

Mineshaft_Mayhem = HotmPerk(
    name = "Mineshaft Mayhem",
    cost_type = GLACITE_POWDER,
    hotm_level = 8
)

# HotM 9

Metal_Head = HotmPerk(
    name = "Metal Head",
    cost_formula = lambda l: (l + 1) ** 4,
    cost_type = GLACITE_POWDER,
    hotm_level = 9,
    max_level = 20
)

Rags_to_Riches = HotmPerk(
    name = "Rags to Riches",
    cost_formula = lambda l: (l + 1) ** 3.05,
    cost_type = GLACITE_POWDER,
    hotm_level = 9,
    max_level = 50
)

Eager_Adventurer = HotmPerk(
    name = "Eager Adventurer",
    cost_formula = lambda l: (l + 1) ** 2.3,
    cost_type = GLACITE_POWDER,
    hotm_level = 9,
    max_level = 100
)

# HotM 10

Gemstone_Infusion = HotmPerk(
    name = "Gemstone Infusion",
    cost_type = GLACITE_POWDER,
    hotm_level = 10
)

Crystalline = HotmPerk(
    name = "Crystalline",
    cost_formula = lambda l: (l + 1) ** 3.3,
    cost_type = GLACITE_POWDER,
    hotm_level = 10,
    max_level = 50
)

Gifts_from_the_Departed = HotmPerk(
    name = "Gifts from the Departed",
    cost_formula = lambda l: (l + 1) ** 2.45,
    cost_type = GLACITE_POWDER,
    hotm_level = 10,
    max_level = 100
)

Mining_Master = HotmPerk(
    name = "Mining Master",
    cost_formula = lambda l: (l + 7) ** 5,
    cost_type = GLACITE_POWDER,
    hotm_level = 10,
    max_level = 10
)

Dead_Mans_Chest = HotmPerk(
    name = "Dead Man's Chest",
    cost_formula = lambda l: (l + 1) ** 3.2,
    cost_type = GLACITE_POWDER,
    hotm_level = 10,
    max_level = 50
)

Vanguard_Seeker = HotmPerk(
    name = "Vanguard Seeker",
    cost_formula = lambda l: (l + 1) ** 3.1,
    cost_type = GLACITE_POWDER,
    hotm_level = 10,
    max_level = 50
)

Sheer_Force = HotmPerk(
    name = "Sheer Force",
    cost_type = GLACITE_POWDER,
    hotm_level = 10
)

#######

all_hotm_perks = [
    # HotM 1
    Mining_Speed,
    # HotM 2
    Mining_Speed_Boost, Precision_Mining, Mining_Fortune, Titanium_Insanium, Pickobulus,
    # HotM 3
    Luck_of_the_Cave, Efficient_Miner, Quick_Forge,
    # HotM 4
    Sky_Mall, Old_School, Professional, Mole, Gem_Lover, Seasoned_Mineman, Front_Loaded,
    # HotM 5
    Daily_Grind, Daily_Powder,
    # HotM 6
    Anomalous_Desire, Blockhead, Subterranean_Fisher, Keep_it_Cool, Lonesome_Miner, Great_Explorer, Maniac_Miner,
    # HotM 7
    Speedy_Mineman, Powder_Buff, Fortunate_Mineman,
    # HotM 8
    Miners_Blessing, No_Stone_Unturned, Strong_Arm, Steady_Hand, Warm_Hearted, Surveyor, Mineshaft_Mayhem,
    # HotM 9
    Metal_Head, Rags_to_Riches, Eager_Adventurer,
    # HotM 10
    Gemstone_Infusion, Crystalline, Gifts_from_the_Departed, Mining_Master, Dead_Mans_Chest, Vanguard_Seeker, Sheer_Force
]