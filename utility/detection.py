"""Auto-detection for the bingo objectives."""

import discord
import typing
import re
import itertools
import traceback

import sys

import utility.files as u_files
import utility.custom as u_custom
import utility.interface as u_interface
import utility.values as u_values
import utility.bread as u_bread
import utility.stonks as u_stonks
import utility.text as u_text
import utility.checks as u_checks
import utility.bingo as u_bingo

import importlib

importlib.reload(u_values)

eleven_plus_messages = {
    11: "Eleven breads? How strange.",
    12: "TWELVE BREADS??",
    13: "NANI????!? THIRTEEN BUREADOS!?!?",
    14: "Fourteen breads? That's a lot of breads. Like really a lot.",
    15: "Woah! Fifteen breads! It really do be like that.",
    16: "Surely that's not possible. Sixteen breads?!",
    17: "Seventeen breads? You're a wizard, Harry.",
    18: "A historical occurence! Eighteen breads!",
    19: "Nineteen breads. I have no words for such a confluence of events.",
    20: "Holy hell! 20 breads!"
}
        
######################################################################################################################################################
##### DECORATOR ######################################################################################################################################
######################################################################################################################################################

class AutoDetection():
    def __init__(self,
            *, objectives: dict[int, str]
        ) -> None:
        """Decorates a function to be used for auto-detection.

        Args:
            objectives (dict[int, str]): Dict with the id as the key and the value as the name of the objective.
        """
        self.objectives = objectives
        self.detection_type = "main"

    def __call__(self, f) -> typing.Callable:

        async def wrapped(
            bot: u_custom.CustomBot,
            message: discord.Message,
            database: u_files.DatabaseInterface,
            objective_id: int,
            bingo_data: dict,
            **kwargs
        ) -> bool:
            """Wrapped autodetection function.

            Args:
                bot (u_custom.CustomBot): The bot object for the bot.
                message (discord.Message): The message that triggered the autodetection.
                database (u_files.DatabaseInterface): The database.
                objective_id (int): The id of the objective that is being checked, in case a function can detect two different objectives.
                bingo_data (dict): The current live bingo data.

            Returns:
                bool: Whether the auto detection was triggered.
            """
            return await f(
                bot = bot,
                message = message,
                database = database,
                bingo_data = bingo_data,
                objective_id = objective_id,
                **kwargs
            )
        
        wrapped.objectives = self.objectives
        wrapped.detection_type = self.detection_type
        wrapped.func = f
        
        return wrapped

class StonkDetection():
    def __call__(self, f) -> typing.Callable:

        async def wrapped(
            stonk_data: dict[str, list[int]],
            **kwargs
        ) -> bool:
            return await f(
                stonk_data = stonk_data,
                **kwargs
            )
        
        wrapped.detection_type = "stonks"
        wrapped.func = f
        
        return wrapped
    

            

        
######################################################################################################################################################
##### AUTO DETECTION FUNCTIONS #######################################################################################################################
######################################################################################################################################################




    
     
######################################################################################################################################################
### BREAD ROLL #######################################################################################################################################
######################################################################################################################################################

@AutoDetection(
    objectives = {
        "d0": "MoaK",
        
        "d32": "14+ roll",
        "w10": "16+ roll",

        "d33": "Someone gets a gold gem",

        "d34": "3+ gems in one roll (between the dashes)",
        "w11": "3+ gems in one roll (between the dashes)",
        
        "d45": "MoaK and Gold Gem in one $bread",

        "d84": "Someone rolls three natural 1s in a row",
        "w29": "Someone rolls four natural 1s in a row",
        
        "d85": "Someone obtains all give gems from only rolling, no alchemy",
        "d88": "Someone rolls the same gem color three times in a row",
        "d89": "Someone rolls a ten with at least 5 special rbeads and 3 chess pieces",

        "d91": "Someone rolls four ascending numbers in a row without any breaks (like 1, 2 , 3, and 4)",
        "w31": "Someone rolls four ascending numbers in a row without any breaks (like 1, 2 , 3, and 4)",
        
        "d96": "Someone rolls an 11+ outside of #bread-rolls",
        "w33": "Someone rolls an 11+ outside of #bread-rolls",
        
        "d104": "5 of the same special appears in 1 roll",

        "d152": "690+ rolls without an 11+ in #smap",
        "w63": "690+ rolls without an 11+ in #smap",
        
        "d170": "someone rolls and it contains at least 2 gems, 2 chess pieces, and 2 special bread",

        "d173": "A roll of 5+ is all the same special",
        "w75": "A roll of 5+ is all the same special"
    }
)
async def item_in_roll(
        message: discord.Message,
        objective_id: int,
        database: u_files.DatabaseInterface,
        **kwargs
    ) -> bool:
    if not u_interface.is_bread_roll(message):
        return False
    
    # These objectives don't require the roll to be parsed.
    if objective_id in ["d45"]:
        return u_values.gem_gold.internal_emoji in message.content and u_values.anarchy_chess.internal_emoji in message.content
    
    if objective_id in ["d0", "d33"]:
        items = {
            "d0": u_values.anarchy_chess,
            "d33": u_values.gem_gold
        }
        
        return items[objective_id].internal_emoji in message.content
    
    # The following objectives require the roll to be parsed.
    parsed = u_bread.parse_roll(message)

    if not parsed:
        return False
    
    if objective_id == "d32":
        for roll in parsed:
            if len(roll) >= 14:
                return True
        
        return False
    
    if objective_id == "w10":
        for roll in parsed:
            if len(roll) >= 16:
                return True
        
        return False
    
    if objective_id in ["d96", "w33"]:
        if message.channel.id == 967544442468843560:
            return False
        
        for roll in parsed:
            if len(roll) >= 11:
                return True
        
        return False

    if objective_id in ["d34", "w11"]:
        for roll in parsed:
            if len(roll) < 3: # Oddly enough, if a roll has 2 items it cannot have 3 gems.
                continue

            gem_sum = [
                    item
                    for item in roll
                    if item.has_attribute("shiny")
                ]

            if len(gem_sum) >= 3:
                return True
        
        return False
    
    if objective_id in ["d84", "w29"]:
        consecutive = 0
        search = 3 if objective_id == "d84" else 4

        for roll in parsed:
            if len(roll) == 1:
                consecutive += 1

                if consecutive >= search:
                    return True
            else:
                consecutive = 0
        
        return False
    
    if objective_id == "d85":
        gems = []

        flattened = itertools.chain.from_iterable(parsed)
        for item in flattened:
            if item not in gems and item.has_attribute("shiny"):
                gems.append(item)
                if len(gems) == len(u_values.all_shiny):
                    return True
        
        
        return False
    
    if objective_id == "d88":
        consecutive = 0
        previous = None

        flattened = itertools.chain.from_iterable(parsed)
        for item in flattened:
            if not item.has_attribute("shiny"):
                continue

            if item == previous:
                consecutive += 1
                if consecutive >= 3:
                    return True
            else:
                previous = item
                consecutive = 1
        
        
        return False
    
    if objective_id == "d89":
        for roll in parsed:
            if len(roll) != 10:
                continue

            special_count = 0
            chess_count = 0

            for special in u_values.special_and_rare:
                special_count += roll.count(special)

            for chess in u_values.all_chess_pieces:
                chess_count += roll.count(chess)

            if special_count >= 5 and chess_count >= 3:
                return True
        
        return False
    
    if objective_id in ["d91", "w31"]:
        consecutive = 0
        previous = len(parsed[0])

        for roll in parsed[1:]:
            if len(roll) == previous + 1:
                consecutive += 1

                if consecutive >= 4:
                    return True
            else:
                consecutive = 1

            previous = len(roll)
        
        return False
    
    if objective_id == "d104":
        for roll in parsed:
            for special in u_values.special_and_rare:
                if roll.count(special) >= 5:
                    return True
        
        return False
    
    if objective_id in ["d152", "w63"]:
        if message.channel.id != 959229175229726760:
            return False
        
        if len(parsed) != 1:
            return False
        
        key = f"{objective_id}-690_smap"
        
        if len(parsed[0]) <= 10:
            data = database.load("auto_detection", default={})

            current = data.get(key, 0) + 1

            data[key] = current

            database.save("auto_detection", data=data)

            if current >= 690:
                return True
        else:
            data = database.load("auto_detection", default = {})

            data[key] = 0
            
            database.save("auto_detection", data=data)
        
        return False
    
    if objective_id == "d170":
        for roll in parsed:
            special_count = 0
            chess_count = 0
            gem_count = 0

            for special in u_values.special_and_rare:
                special_count += roll.count(special)

            for chess in u_values.all_chess_pieces:
                chess_count += roll.count(chess)

            for gem in u_values.all_shiny:
                gem_count += roll.count(gem)

            if special_count >= 2 and chess_count >= 2 and gem_count >= 2:
                return True
        
        return False
    
    if objective_id in ["d173", "w75"]:
        for roll in parsed:
            if len(roll) < 5:
                continue

            item = roll[0]

            if item not in u_values.special_and_rare:
                continue

            if roll.count(item) == len(roll):
                return True
        
        return False
    
    # Failsafe.
    return False




    
     
######################################################################################################################################################
### ROLL RESULT ######################################################################################################################################
######################################################################################################################################################
# This is the summary Machine-Mind sends if you do not have the Roll Summarizer.

@AutoDetection(
    objectives = {
        "d0": "MoaK",
        "d5": "Someone wins the lottery",

        "d19": "Kapola gets a lottery",
        "w5": "Kapola gets a lottery",
        
        "d32": "14+ roll",
        "w10": "16+ roll",

        "d33": "Someone gets a gold gem",

        "d96": "Someone rolls an 11+ outside of #bread-rolls",
        "w33": "Someone rolls an 11+ outside of #bread-rolls"
    }
)
async def roll_result(
        message: discord.Message,
        objective_id: int,
        **kwargs
    ) -> bool:
    if not u_interface.mm_checks(message, check_reply=True):
        return False
    
    if objective_id in ["d19", "w5"]:
        if "You won the lottery" not in message.content:
            return False
        
        if u_interface.is_reply(message, allow_ping=False):
            return message.reference.resolved.author.id == 713053430075097119
        
        # Here, the message is a reply, but done with a ping.
        mention = u_text.extract_number("<@(\d+)>", message.content.split("\n")[0], default=None)

        return mention == 713053430075097119
    
    if objective_id in ["d32", "w10"]:
        low = 14 if objective_id == "d32" else 16

        if any([eleven_plus_messages[text] in message.content for text in range(low, 21)]):
            return True
        
        if re.match("Holy hell! [\d,]+ breads!", message.content):
            return True
        
        return False
    
    if objective_id in ["d96", "w33"]:
        if message.channel.id == 967544442468843560:
            return False
        
        if any([text in message.content for text in eleven_plus_messages.values()]):
            return True
        
        if re.match("Holy hell! [\d,]+ breads!", message.content):
            return True
        
        return False

    text_check = {
        "d0": "That sure is pretty rare!",
        "d5": "You won the lottery",
        "d33": "The fabled gold gem!"
    }
    
    if objective_id in text_check:
        return text_check[objective_id] in message.content
    
    # Failsafe.
    return False




    
     
######################################################################################################################################################
### ROLL SUMMARY #####################################################################################################################################
######################################################################################################################################################
# This is the summary Machine-Mind sends if you have the Roll Summarizer.

@AutoDetection(
    objectives = {
        "d0": "MoaK",
        "d5": "Someone wins the lottery",

        "d19": "Kapola gets a lottery",
        "w5": "Kapola gets a lottery",

        "d32": "14+ roll",
        "w10": "16+ roll",
        
        "d33": "Someone gets a gold gem",
        "d45": "MoaK and Gold Gem in one $bread",
        "d85": "Someone obtains all five gems from only rolling, no alchemy",

        "d178": "Someone gets two lotteries in a single day",
        "w79": "Someone gets two lotteries in a single day",
        
        "d189": "Someone makes 750k or more dough from just rolling"
    }
)
async def roll_summary(
        message: discord.Message,
        objective_id: int,
        **kwargs
    ) -> bool:
    if not u_interface.mm_checks(message, check_reply=True):
        return False
    
    if "Summary of results:" not in message.content:
        return False
    
    # These objectives involve someone winning the lottery.
    if objective_id in ["d5", "d178", "w79", "d19", "w5"]:
        amount = u_text.extract_number("lottery_win: ([\d,]+)", message.content, default=0)
        if amount < 1:
            return False
        
        # The person has won the lottery.
        
        if objective_id == "d5":
            return True
        
        if objective_id in ["d178", "w79"]:
            return amount >= 2
        
        if objective_id in ["d19", "w5"]:
            if u_interface.is_reply(message, allow_ping=False):
                return message.reference.resolved.author.id == 713053430075097119
            
            # Here, the message is a reply, but done with a ping.
            mention = u_text.extract_number("<@(\d+)>", message.content.split("\n")[0], default=None)

            return mention == 713053430075097119
    
    if objective_id in ["d32", "w10"]:
        if "fourteen_or_higher: " in message.content and objective_id == "d32":
            return True
        
        highest_roll = u_text.extract_number("The highest roll was ([\d,]+)", message.content, default=0)

        low = 14 if objective_id == "d32" else 16

        if highest_roll >= low:
            return True
        
        if any([eleven_plus_messages[text] in message.content for text in range(low, 21)]):
            return True
        
        if re.match("Holy hell! [\d,]+ breads!", message.content):
            return True
        
        return False

    if objective_id == "d45":
        return u_text.extract_number(f"{re.escape(u_values.gem_gold.internal_emoji)}: ([\d,]+)", message.content, default=0) >= 1 and u_text.extract_number(f"{re.escape(u_values.anarchy_chess.internal_emoji)}: ([\d,]+)", message.content, default=0) >= 1

    if objective_id == "d85":
        return all([
            u_text.extract_number(f"{re.escape(item.internal_emoji)}: ([\d,]+)", message.content, default=0) >= 1
            for item in u_values.all_shiny
        ])

    if objective_id == "d189":
        return u_text.extract_number("Total gain: \*\*([\d,]+) dough\*\*", message.content, default=0) >= 750_000
    
    summary_items = {
        "d0": u_values.anarchy_chess,
        "d33": u_values.gem_gold
    }

    if objective_id in summary_items:
        pattern = "{}: ([\d,]+)".format(re.escape(summary_items[objective_id].internal_emoji))
        matched = re.search(pattern, message.content)

        if matched is not None and u_text.return_numeric(matched.group(1)) >= 1:
            return True

    # Failsafe.
    return False




    
     
######################################################################################################################################################
### BREAD PORTFOLIO ##################################################################################################################################
######################################################################################################################################################

@AutoDetection(
    objectives = {
        "d79": "Someone makes over a 5m dough profit from stonks",
        "w28": "Someone makes over a 3b dough profit from stonks",
        
        "d168": "Someone goes all in on one stonk and makes a profit",

        "d206": "Someone invests 25k+ in stonks and their portfolio does not change on a tick",
        "w93": "Someone invests 250k+ in stonks and their portfolio does not change on a tick"
    }
)
async def portfolio(
        message: discord.Message,
        objective_id: int,
        **kwargs
    ) -> bool:
    if not u_interface.mm_checks(message, check_reply=True):
        return False
    
    if not message.content.startswith("Investment portfolio for "):
        return False
    
    change_amount = u_text.extract_number(r"In the last tick, your portfolio value changed by \*\*([\d\-,]+) dough\*\*\.", message.content, default=0)
    
    if objective_id == "d79":
        return change_amount >= 5_000_000
    
    if objective_id == "w28":
        return change_amount >= 3_000_000_000
    
    if objective_id in ["d206", "w93"]:
        lower = 25_000 if objective_id == "d206" else 250_000
        if u_text.extract_number("Your portfolio is worth \*\*([\d,]+) dough\*\*\.", message.content, default=0) < lower:
            return False

        return change_amount == 0
    
    if objective_id == "d168":
        if change_amount <= 0:
            return False
        
        found = False

        for stonk in u_values.stonks:
            if stonk.internal_emoji in message.content or stonk.emoji in message.content:
                if found:
                    return False
                found = True
        
        return found




    
     
######################################################################################################################################################
### STONK INVEST #####################################################################################################################################
######################################################################################################################################################

@AutoDetection(
    objectives = {
        "d188": "Someone lands on 3 or 4 dough after investing in stonks"
    }
)
async def invest_confirmation(
        message: discord.Message,
        objective_id: int,
        **kwargs
    ) -> bool:
    if not u_interface.mm_checks(message, check_reply=True):
        return False
    
    if not message.content.startswith("You invested in"):
        return False
    
    if objective_id == "d188":
        return u_text.extract_number("You have \*\*([\d,]+) dough\*\* remaining\.", message.content, default=0) in [3, 4]




    
     
######################################################################################################################################################
### BRICK STATS ######################################################################################################################################
######################################################################################################################################################

@AutoDetection(
    objectives = {
        "d159": "Someone reaches a new hundred milestone on $brick stats"
    }
)
async def brick_stats(
        message: discord.Message,
        objective_id: int,
        **kwargs
    ) -> bool:
    if not u_interface.mm_checks(message, check_reply=False):
        return False
    
    if not(message.content.startswith("Brick stats for") or message.content[-1] in ".?!"):
        return False
    
    gold_brick = u_text.extract_number(f"{u_values.brick_gold.internal_emoji} - ([\d,]+)", message.content, default=0)
    total = u_text.extract_number("Total bricks: ([\d,]+)", message.content, default=0)
    
    if objective_id == "d159":
        return str(gold_brick).endswith("00") or str(total).endswith("00")




    
     
######################################################################################################################################################
### ALCHEMY COMPLETION ###############################################################################################################################
######################################################################################################################################################

@AutoDetection(
    objectives = {
        "d1": "Someone gets an omega",
        "d33": "Someone gets a gold gem",
        
        "d86": "Someone alchemizes 30+ of one chess piece at the same time",
        "w30": "Someone alchemizes 10,000+ of one chess piece at the same time",
        
        "d90": "Someone alchemizes 3 red gems from 3 blue gems",
        "d92": "Someone alchemizes 1,000+ specials at once"
    }
)
async def alchemy_completion(
        message: discord.Message,
        objective_id: int,
        **kwargs
    ) -> bool:
    if not u_interface.mm_checks(message, check_reply=True):
        return False
    
    if "Well done. You have created" not in message.content:
        return False
    
    searched = re.search(r"Well done\. You have created ([\d,]+) (.+)\. You now have", message.content)

    if searched is None:
        return False

    alchemize_amount = u_text.return_numeric(searched.group(1))
    alchemized_item = u_values.get_item(searched.group(2))

    detect_items = {
        "d1": (u_values.omega_chessatron, 1),
        "d33": (u_values.gem_gold, 1),
        "d86": (u_values.all_chess_pieces, 30),
        "w30": (u_values.all_chess_pieces, 10_000),
        "d90": (u_values.gem_red, 3),
        "d92": (u_values.special_and_rare, 1_000)
    }

    if objective_id in detect_items:
        if isinstance(detect_items[objective_id][0], list):
            for item in detect_items[objective_id][0]:
                if item == alchemized_item and alchemize_amount >= detect_items[objective_id][1]:
                    return True
            
        if alchemized_item == detect_items[objective_id][0] and alchemize_amount >= detect_items[objective_id][1]:
            return True
    
    # Failsafe.
    return False




    
     
######################################################################################################################################################
### DIPSAR SPAM ######################################################################################################################################
######################################################################################################################################################

@AutoDetection(
    objectives = {
        "d3": "Kapola :despair: spam"
    }
)
async def despair_spam(
        message: discord.Message,
        objective_id: int,
        **kwargs
    ) -> bool:
    if message.author.id != 713053430075097119: # Kapola's id.
        return False
    
    if len(re.findall("<:despair:\d+>", message.content)) >= 5:
        return True

    # Failsafe.
    return False




    
     
######################################################################################################################################################
### GENERAL MESSAGES #################################################################################################################################
######################################################################################################################################################

@AutoDetection(
    objectives = {
        "d31": "Someone says 'Holy ____' and doesn't say 'holy hell'",
        "d59": "Someone pings '@gets pinged too much'",
        "d71": "An announcement is made in #announcements",
        
        "d77": "Savings sends a message outside of the 3 normal channels",
        "w26": "Savings sends a message outside of the 3 normal channels",
        
        "d154": "The Bingo-Bot automatically ticks off a square",
        "w65": "The Bingo-Bot automatically ticks off a square",

        "d192": "Latent talks about pancakes"
    }
)
async def general_messages(
        message: discord.Message,
        objective_id: int,
        bot: u_custom.CustomBot,
        **kwargs
    ) -> bool:
    if objective_id == "d31":
        match = re.search("holy(?! hell)", message.content.lower())
        return match is not None
    
    if objective_id == "d71":
        return message.channel.id == 958763826025742336
    
    if objective_id in ["d77", "w26"]:
        if message.author.id != 718631368908734545:
            return False
        
        if isinstance(message.channel, discord.Thread):
            channel = message.channel.parent
        else:
            channel = message.channel
        
        return channel.id not in [980267115821035550, 994460122875174942, 958487694676205628]
    
    if objective_id in ["d154", "w65"]:
        if message.author.id != bot.user.id:
            return False
        
        if not u_interface.is_reply(message):
            return False
        
        return re.search("(\d+ )?(weekly )?bingo objectives? completed!", message.content.lower()) is not None
    
    if objective_id == "d192":
        if message.author.id != 973811353036927047:
            return False
        
        return "pancake" in message.content.lower()
    
    search = {
        "d59": "<@&967443956659019786>"
    }

    return search[objective_id] in message.content




    
     
######################################################################################################################################################
### MESSAGE PREFIX ###################################################################################################################################
######################################################################################################################################################

@AutoDetection(
    objectives = {
        "d7": "$brick gamble",
        "d12": "Someone fakes '$brick' message",
        "d29": "Someone does $bread (move)",
        "d54": "Someone mispells or uses the wrong prefix for '$bread'",
        "d57": "Someone tries to $bread outside of #bread-rolls, #bread-activities, #bread, and #smap",
        "d62": "Someone $thanks MM",
        "d151": "A moderator abuses their powers",
        "d166": "Someone gets bricked by a moderator or admin"
    }
)
async def message_prefix(
        message: discord.Message,
        objective_id: int,
        **kwargs
    ) -> bool:
    mod_content = f"{message.content} " # Add a space so something like `mod_content.startswith("$brick gamble ")` works.

    if objective_id == "d29":
        if not mod_content.startswith("$bread "):
            return False
        
        return len(u_text.extract_chess_moves(mod_content.split(" ")[1])) >= 1
    
    if objective_id == "d54":
        return any(
            [
                mod_content.startswith(f"{prefix} ")
                for prefix in ["$brad", "$braed", "$brade", "$bead", "$brea", "$bred", "$berad", "$rbead", "$bredd"]
            ]
        )
    
    if objective_id == "d57":
        if not mod_content.startswith("$bread "):
            return False
        
        return message.channel.id not in [967544442468843560, 1063317762191147008, 958705808860921906, 959229175229726760]
    
    if objective_id in ["d151", "d166"]:
        if not mod_content.startswith("$brick "):
            return False
        
        if not u_checks.in_authority(message.author):
            return False
        
        split = message.content.split(" ")

        if len(split) <= 1:
            return False
        
        split = split[1]
        
        user = discord.utils.find(lambda m: split in [m.name, m.display_name, m.global_name, m.mention, m.id, str(m)], message.guild.members)

        if user is None:
            return False
        
        if user == message.author:
            return False
        
        return True

    startswith = {
        "d7": "$brick gamble",
        "d12": r"\$brick",
        "d62": "$thanks"
    }
    
    if objective_id in startswith:
        return mod_content.startswith(f"{startswith[objective_id]} ")
    return False




    
     
######################################################################################################################################################
### MACHINE-MIND MESSAGES ############################################################################################################################
######################################################################################################################################################

@AutoDetection(
    objectives = {
        "d17": "Golden brick",
        "w3": "Golden brick",

        "d26": "MM chess en passant!!",
        "d28": "Bongcloud in an MM chess game",
        "d50": "Someone attempts to gift negative dough",
        "d51": "Someone gifts MM something",
        "d60": "Someone draws an MM chess game", # I have no idea why, but this one needs to be 'dNaN' in order to work, it makes no sense.
        "d118": "Someone tries to brick Melodie and gets bricked themself",

        "d127": "Someone ascends",
        "w54": "Someone ascends",
        
        "d167": "Someone resigns in a discord chess game"
    }
)
async def mm_messages(
        message: discord.Message,
        objective_id: int,
        **kwargs
    ) -> bool:
    if not u_interface.mm_checks(message, check_reply=False):
        return False
    
    # These objectives require MM's message being a reply.
    if objective_id in ["d50", "d60", "d118", "d127", "d167"]:
        if not u_interface.is_reply(message):
            return False
        
        if objective_id == "d50":
            return message.content == "Trying to steal bread? Mum won't be very happy about that."
        
        if objective_id == "d60":
            return message.content == "The game has been drawn."
        
        if objective_id == "d118":
            return message.content == "Do you really think I'd brick *my own mother?*"
        
        if objective_id in ["d127", "w54"]:
            return "Congratulations! You have ascended to a higher plane of existence." in message.content
        
        if objective_id == "d167":
            return message.content in ["White resigned.", "Black resigned."]
    
    if objective_id in ["d17", "w3"]:
        return message.content == u_values.brick_gold.internal_emoji
    
    if objective_id == "d51":
        return message.content.endswith("has been gifted to <@960869046323134514>.")
    
    # These objectives are for MM chess games.
    if message.content.startswith("```\nSend '$move ***' to make a move, such as '$move e4'."):
        if message.content[-1] in ".?!":
            return False
        
        if objective_id == "d26":
            move_list = [item[0] for item in u_text.extract_chess_moves(message.content.split("\n")[-1])]

            if len(move_list) <= 1:
                return False
            
            if len(move_list[-2]) != 2 or not move_list[-2].islower(): # looking for something like `d5`
                return False
            
            if len(move_list[-1]) != 4 or not (move_list[-1].islower()) or move_list[-1][1] != "x": # looking for something like `exd6`
                return False
            
            move_file = move_list[-2][0]

            if move_file not in "abcdefgh":
                return False

            move_rank = move_list[-2][1]

            if move_rank not in "45": # Pawns moving two squares can only end up on one of these.
                return False
            
            expected = "3" if move_rank == "4" else "6"

            if move_list[-1][1:] != f"x{move_file}{expected}":
                return False
            
            return True
            

        if objective_id == "d28":
            return (message.content.endswith("Ke2 ```") or message.content.endswith("Ke7 ```"))
            
    # Failsafe.
    return False




    
     
######################################################################################################################################################
### STONK TICKS ######################################################################################################################################
######################################################################################################################################################

@StonkDetection()
@AutoDetection(
    objectives = {
        "d4": "Pretzels suck, again",
        "w0": "Pretzels suck, again",

        "d46": "All stonks go down in one tick",
        "w19": "All stonks go down in one tick",

        "d63": "A stonk goes up for 3 ticks in a row",
        "w24": "A stonk goes up for 3 ticks in a row",

        "d78": "Fortune cookies suffer a sizable drop (over -30 dough in one tick)",
        "w27": "Fortune cookies suffer a sizable drop (over -30 dough in one tick)",

        "d103": "Fortune cookies increases by 80+ dough in one tick",
        "w38": "Fortune cookies increases by 80+ dough in one tick",

        "d137": "A stonk gets split",
        "w57": "A stonk gets split",

        "d181": "Cookies change by a total of 1",
        "w80": "Cookies change by a total of 1",

        "d182": "Cookies stagnate for 2+ ticks in a row",
        "w81": "Cookies stagnate for 2+ ticks in a row",

        "d186": "A stonk goes down 2 ticks in a row",
        "w84": "A stonk goes down 3 ticks in a row",

        "d193": "Pancakes go up 500 dough in one tick",

        "d195": "Pancakes rise more than 1,500 dough in 3 ticks",
        "w86": "Pancakes rise more than 1,500 dough in 3 ticks"

    }
)
async def stonk_change(
        stonk_data: dict,
        message: discord.Message,
        objective_id: int,
        **kwargs
    ) -> bool:
    if len(stonk_data) == 0:
        return False
    
    stonk_data = stonk_data.copy()
    
    # Filter for splits.
    for index in range(len(stonk_data[list(stonk_data.keys())[0]]) - 1, 0, -1):
        corrected = u_stonks.filter_splits(
                previous = {stonk: item[index - 1] for stonk, item in stonk_data.items()},
                current = {stonk: item[index] for stonk, item in stonk_data.items()}
            )["new"]
        for stonk in stonk_data:
            stonk_data[stonk][index - 1] = corrected[stonk]

    # Now for the actual detection.
            
    if objective_id in ["d4", "w0"]:
        data = stonk_data.get(u_values.pretzel, [])
        try:
            return data[-3] >= data[-2] >= data[-1]
        except IndexError:
            return False
        
    elif objective_id in ["d46", "w19"]:
        return all([
            stonk_data[stonk][-2] > stonk_data[stonk][-1]
            for stonk in stonk_data
            if len(stonk_data[stonk]) >= 2
        ])
    
    elif objective_id in ["d63", "w24"]:
        for stonk in stonk_data:
            if len(stonk_data[stonk]) < 3:
                continue
            
            if stonk_data[stonk][-3] < stonk_data[stonk][-2] < stonk_data[stonk][-1]:
                return True
            
    elif objective_id in ["d78", "w27"]:
        data = stonk_data.get(u_values.fortune_cookie, [])
        try:
            return data[-1] - data[-2] < -30
        except IndexError:
            return False
        
    elif objective_id in ["d103", "w38"]:
        data = stonk_data.get(u_values.fortune_cookie, [])
        try:
            return data[-1] - data[-2] >= 80
        except IndexError:
            return False
        
    elif objective_id in ["d137", "w57"]:
        return "Split!" in message.content
        
    elif objective_id in ["d181", "w80"]:
        data = stonk_data.get(u_values.cookie, [])
        try:
            return abs(data[-1] - data[-2]) == 1
        except IndexError:
            return False
        
    elif objective_id in ["d182", "w81"]:
        data = stonk_data.get(u_values.cookie, [])
        try:
            return data[-1] == data[-2] == data[-3]
        except IndexError:
            return False
    
    if objective_id == "d186":
        for stonk in stonk_data:
            data = stonk_data.get(stonk, [])
            try:
                if data[-3] > data[-2] > data[-1]:
                    return True
            except IndexError:
                return False
    
    if objective_id == "w84":
        for stonk in stonk_data:
            data = stonk_data.get(stonk, [])
            try:
                if data[-4] > data[-3] > data[-2] > data[-1]:
                    return True
            except IndexError:
                return False
    
    if objective_id == "d193":
        data = stonk_data.get(u_values.pancakes, [])
        try:
            return data[-1] - data[-2] >= 500
        except IndexError:
            return False
    
    if objective_id in ["d195", "w86"]:
        data = stonk_data.get(u_values.pancakes, [])
        try:
            return data[-1] - data[-4] >= 1500
        except IndexError:
            return False
    
    # Failsafe.
    return False




    
     
######################################################################################################################################################
### INITIAL GAMBLE BOARD #############################################################################################################################
######################################################################################################################################################

@AutoDetection(
    objectives = {
        "d6": "Gamble board with 1 or fewer positives",
        
        "d35": "3+ brick options in 1 gamble",
        "w12": "4+ brick options in 1 gamble",

        "d36": "3+ anarchy options in 1 gamble",
        "w13": "3+ anarchy options in 1 gamble",

        "d106": "A checkmate appears in gambling",
        "w40": "A checkmate appears in gambling",

        "d107": "A pin appears in gambling",
        "w41": "A pin appears in gambling",

        "d108": "A horsey royal fork appears in gambling",
        "w42": "A horsey royal fork on a gambling board",

        "d111": "Two pawns next to each other horizontally and a 'holy hell' appear on the same board",
        "w45": "Two pawns next to each other horizontally and a 'holy hell' appear on the same board",
        
        "d113": "Three different brick variants in one gamble",
        "w47": "Three different brick variants in one gamble",

        "d114": "Half of the options on a gambling board are exactly the same",
        "w48": "Half of the options on a gambling board are exactly the same",

        "d120": "A Tetris piece is found in gambling",
        "w51": "2 Tetris pieces are found in a single gambling board",

        "d122": "3+ types of horseys appear in one gamble",
        "w52": "3+ types of horseys appear in one gamble",

        "d123": "All 16 starting options in one gamble are different",
        "w53": "All 16 starting options in one gamble are different",

        "d190": "four unique chess pieces are found on a gambling board",
        "w85": "four unique chess pieces are found on a gambling board"
    }
)
async def initial_gamble_board(
        message: discord.Message,
        objective_id: int,
        **kwargs
    ) -> bool:
    gamble_data = u_bread.parse_gamble(message)

    if gamble_data is None:
        return False

    if objective_id == "d6":
        return sum(
            [
                gamble_data.count(item)
                for item in u_values.gamble_positives
            ]
        ) <= 1
    
    elif objective_id in ["d35", "w12"]:
        return sum(
            [
                gamble_data.count(item)
                for item in u_values.gamble_bricks
            ]
        ) >= (3 if objective_id == "d35" else 4)
    
    elif objective_id in ["d36", "w13"]:
        return sum(
            [
                gamble_data.count(item)
                for item in u_values.gamble_anarchy
            ]
        ) >= 3
    
    elif objective_id in ["d106", "w40"]:
        if u_values.bking not in gamble_data:
            return False
        
        controlled_squares = [False for _ in gamble_data]

        king_index = [] # more like kingdex
        
        for index, item in enumerate(gamble_data):
            if item == u_values.bking:
                king_index.append(index)
                continue

            if item not in u_values.black_chess_pieces:
                continue

            if item == u_values.bpawn:
                if index < 4:
                    continue
                if index % 4 != 0:
                    controlled_squares[index - 5] = True
                if index % 4 != 3:
                    controlled_squares[index - 3] = True
                continue
                
            xpos = index % 4
            ypos = index // 4
            
            if item == u_values.bbishop or item == u_values.bqueen:
                for i in range(1, min(xpos, ypos) + 1):
                    controlled_squares[index - 5 * i] = True
                    if gamble_data[index - 5 * i] in u_values.black_chess_pieces:
                        break
                
                for i in range(1, min(3 - xpos, 3 - ypos) + 1):
                    controlled_squares[index + 5 * i] = True
                    if gamble_data[index + 5 * i] in u_values.black_chess_pieces:
                        break
                
                for i in range(1, min(3 - xpos, ypos) + 1):
                    controlled_squares[index - 3 * i] = True
                    if gamble_data[index - 3 * i] in u_values.black_chess_pieces:
                        break
                
                for i in range(1, min(xpos, 3 - ypos) + 1):
                    controlled_squares[index + 3 * i] = True
                    if gamble_data[index + 3 * i] in u_values.black_chess_pieces:
                        break
            
            if item == u_values.brook or item == u_values.bqueen:
                for i in range(1, xpos + 1):
                    controlled_squares[index - i] = True
                    if gamble_data[index - i] in u_values.black_chess_pieces:
                        break
                    
                for i in range(1, 3 - xpos + 1):
                    controlled_squares[index + i] = True
                    if gamble_data[index + i] in u_values.black_chess_pieces:
                        break

                for i in range(1, ypos + 1):
                    controlled_squares[index - 4 * i] = True
                    if gamble_data[index - 4 * i] in u_values.black_chess_pieces:
                        break

                for i in range(1, 3 - ypos + 1):
                    controlled_squares[index + 4 * i] = True
                    if gamble_data[index + 4 * i] in u_values.black_chess_pieces:
                        break
            
            if item == u_values.bknight:
                positions = []
                for pos_id in range(8):
                    positions.append(
                        (
                            xpos + (((pos_id + 1) % 4 < 2) + 1) * (1 if ((pos_id + 2) % 8 < 4) else -1),
                            ypos + (((pos_id - 1) % 4 < 2) + 1) * (-1 if pos_id > 3 else 1)
                        )
                    )

                for pos in positions:
                    if pos[0] < 0 or pos[0] >= 4 or pos[1] < 0 or pos[1] >= 4:
                        continue

                    controlled_squares[pos[0] + 4 * pos[1]] = True
        

        for king_try in king_index:
            king_try_xpos = king_try % 4
            king_try_ypos = king_try // 4

            # Now mark off the squares controlled by every other king on the board.
            control_copy = controlled_squares.copy()
            for king in king_index:
                if king == king_try:
                    continue

                king_xpos = king % 4
                king_ypos = king // 4
                for xmod, ymod in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
                    if king_xpos + xmod < 0 or king_xpos + xmod >= 4 or king_ypos + ymod < 0 or king_ypos + ymod >= 4:
                        continue

                    control_copy[king_xpos + xmod + 4 * (king_ypos + ymod)] = True
            
            for xmod, ymod in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 0), (0, 1), (1, -1), (1, 0), (1, 1)]:
                if king_try_xpos + xmod < 0 or king_try_xpos + xmod >= 4 or king_try_ypos + ymod < 0 or king_try_ypos + ymod >= 4:
                    continue

                if control_copy[king_try_xpos + xmod + 4 * (king_try_ypos + ymod)]:
                    continue

                # This square is not controlled by any other pieces.
                return False
            
            # If it gets here, then all the squares are controlled, and thus the objective is met.
            return True
        
        # It shouldn't ever get here, but as a failsafe...
        return False
    
    elif objective_id in ["d107", "w41"]:
        if u_values.bking not in gamble_data:
            return False

        main_pieces = [
            u_values.bknight,
            u_values.bbishop,
            u_values.brook,
            u_values.bqueen
        ]
        
        for index, item in enumerate(gamble_data):
            if item != u_values.bking:
                continue

            xpos = index % 4
            ypos = index // 4

            modifiers = [ # modification amount, number of iterations, piece (other than queens) that this works with
                (-5, min(xpos, ypos), u_values.bbishop), # up left
                (-4, ypos, u_values.brook), # up
                (-3, min(3 - xpos, ypos), u_values.bbishop), # up right
                (-1, xpos, u_values.brook), # left
                (1, 3 - xpos, u_values.brook), # right
                (3, min(xpos, 3 - ypos), u_values.bbishop), # down left
                (4, 3 - ypos, u_values.brook), # down
                (5, min(3 - xpos, 3 - ypos), u_values.bbishop) # down right
            ]

            for mod, max_iterations, piece in modifiers:
                pinned = False

                for i in range(1, max_iterations + 1):
                    pos = index + mod * i
                    if pos < 0 or pos >= 16:
                        break

                    if gamble_data[pos] not in u_values.black_chess_pieces:
                        continue

                    if pinned:
                        if gamble_data[pos] == piece or gamble_data[pos] == u_values.bqueen:
                            return True
                        continue

                    if gamble_data[pos] in main_pieces:
                        pinned = True
                        continue

                    if gamble_data[pos] == u_values.bpawn and abs(mod) != 4:
                        pinned = True
                        continue
            
        return False

    elif objective_id in ["d108", "w42"]:
        if u_values.bknight not in gamble_data:
            return False
        if u_values.bking not in gamble_data:
            return False
        if u_values.bqueen not in gamble_data:
            return False
        
        
        for index, item in enumerate(gamble_data):
            if item != u_values.bknight:
                continue

            king = False
            queen = False

            xpos = index % 4
            ypos = index // 4
            
            positions = []
            for pos_id in range(8):
                positions.append(
                    (
                        xpos + (((pos_id + 1) % 4 < 2) + 1) * (1 if ((pos_id + 2) % 8 < 4) else -1),
                        ypos + (((pos_id - 1) % 4 < 2) + 1) * (-1 if pos_id > 3 else 1)
                    )
                )

            for pos in positions:
                if pos[0] < 0 or pos[0] >= 4 or pos[1] < 0 or pos[1] >= 4:
                    continue

                index = pos[0] + 4 * pos[1]
                
                if gamble_data[index] == u_values.bqueen:
                    queen = True
                if gamble_data[index] == u_values.bking:
                    king = True
                
                if queen and king:
                    return True

        return False

    
    elif objective_id in ["d111", "w45"]:
        if u_values.holy_hell not in gamble_data:
            return False
        if gamble_data.count(u_values.bpawn) <= 1:
            return False
        
        for index, item in enumerate(gamble_data):
            if item != u_values.bpawn:
                continue

            if index % 4 != 0:
                if gamble_data[index - 1] == u_values.bpawn:
                    return True

            if index % 4 != 3:
                if gamble_data[index + 1] == u_values.bpawn:
                    return True

        return False
        
    
    elif objective_id in ["d113", "w47"]:
        return sum([
            item in gamble_data
            for item in u_values.gamble_bricks
        ]) >= 3
    
    elif objective_id in ["d114", "w48"]:
        return max(
            [
                gamble_data.count(item)
                for item in gamble_data
            ]
        ) >= 8
    
    elif objective_id in ["d120", "w51"]:
        pairs = {}

        def check(index: int, modifier: int, item: typing.Type[u_values.Item]) -> None:
            nonlocal pairs

            if gamble_data[index + modifier] != item:
                return
            
            if item in pairs:
                pairs[item].append((index, index + modifier))
            else:
                pairs[item] = [(index, index + modifier)]

        for index, item in enumerate(gamble_data):
            if index <= 11:
                # down
                check(index, 4, item)

            if index % 4 != 3:
                # right
                check(index, 1, item)
        
        tetrises_found = 0
        
        for item in pairs:
            if len(pairs[item]) < 3:
                continue

            covered = []

            for pair1, pair2 in pairs[item]:
                if pair1 in covered or pair2 in covered:
                    continue

                found = [pair1, pair2]

                for subsearch_1, subsearch_2 in pairs[item]:
                    if not (subsearch_1 in found or subsearch_2 in found):
                        continue

                    if subsearch_1 in found:
                        found.append(subsearch_2)
                    else:
                        found.append(subsearch_1)

                # Add all the items in `found` to `covered`.
                covered[0:0] = found
                
                tetrises_found += len(found) // 4

                if tetrises_found >= 1:
                    if objective_id == "w51":
                        if tetrises_found >= 2:
                            return True
                        continue

                    # Daily objective.
                    return True
        
        # If no tetrises are found.
        return False
    
    elif objective_id in ["d122", "w52"]:
        horseys = [
            u_values.horsey,
            u_values.anarchy_chess,
            u_values.bknight,
            u_values.bcapy
        ]
        return sum([
            item in gamble_data
            for item in horseys
        ]) >= 3
    
    elif objective_id in ["d123", "w53"]:
        return len([
            True
            for item in gamble_data
            if gamble_data.count(item) >= 2
        ]) == 0
      
    elif objective_id in ["d190", "w85"]:
        return sum([
            item in gamble_data
            for item in u_values.gamble_chess_piece
        ]) >= 4
    
    # Failsafe.
    return False




    
     
######################################################################################################################################################
### GAMBLE RESULT ####################################################################################################################################
######################################################################################################################################################

@AutoDetection(
    objectives = {
        "d9": "Someone gets an anarchy gambling",

        "d44": "Half of gamble options are postive and one isn't picked",
        "w18": "Half of gamble options are postive and one isn't picked",

        "d116": "A gold brick is won while gambling",
        "w50": "A gold brick is won while gambling",
        
        "d187": "Someone gambles at least 50 and gets a brick"
    }
)
async def gamble_result(
        message: discord.Message,
        objective_id: int,
        database: u_files.DatabaseInterface,
        **kwargs
    ) -> bool:
    if not u_interface.mm_checks(message, check_reply=True):
        return False

    if "You found a brick" in message.content:
        if "Looks like you'll" in message.content:
            item_won = u_values.brick_gold

            dough_won = re.search(r"Looks like you'll be able to sell this one for ([\d,]+) dough.", message.content)
            if dough_won is None:
                return False

            dough_won = u_text.return_numeric(dough_won.group(1))
        else:
            item_won = u_values.bricks
            dough_won = 0
    elif "Sorry, you didn't win anything. Better luck next time." in message.content:
        item_won = u_values.horsey
        dough_won = 0
    else:
        if not message.content.startswith("With a"):
            return False
        
        item_regex = re.search("With a (.+), you won ([\d,]+) dough.", message.content)

        if item_regex is None:
            return False
        
        item_won = u_values.get_item(item_regex.group(1))
        dough_won = u_text.return_numeric(item_regex.group(2))
    
    

    if objective_id == "d9":
        return item_won in [u_values.anarchy, u_values.holy_hell, u_values.anarchy_chess]
    
    if objective_id in ["d44", "w18"]:
        if item_won in u_values.gamble_positives:
            return False
        
        if not u_interface.is_reply(message, allow_ping=False):
            return False
        
        search_id = message.reference.resolved.id
        gamble_data = database.load("bread", "gamble_messages", default={})

        gamble_content = None

        for value in gamble_data.values():
            if value["command"] != search_id:
                continue
            
            gamble_content = value["content"]
            break

        if gamble_content is None:
            return False

        parsed = u_bread.parse_gamble(gamble_content)

        positives = 0

        for item in u_values.gamble_positives:
            positives += parsed.count(item)

        return positives >= 8
    
    if objective_id in ["d116", "w50"]:
        return item_won == u_values.brick_gold
    
    if objective_id == "d187":
        # We can't detect this one if we don't have the gamble command message, so this checks if the message has a ping at the start or not.
        if not u_interface.is_reply(message, allow_ping=False):
            return False
        
        wager = u_text.extract_number("\$bread gamble ([\d,]+)", message.reference.resolved.content, default=4)

        return item_won in u_values.gamble_bricks and wager >= 50




    
     
######################################################################################################################################################
### BUY MESSAGE ######################################################################################################################################
######################################################################################################################################################

@AutoDetection(
    objectives = {
        "d55": "Nixon buys extra gambles",
        "w22": "Nixon buys extra gambles",

        "d121": "Duck Duck Go r/place buys extra gambles"
    }
)
async def buy_message(
        message: discord.Message,
        objective_id: int,
        **kwargs
    ) -> bool:
    if not message.content.startswith("$bread buy "):
        return False
    
    if "extra_gamble" in message.content or "extra gamble" in message.content:
        if objective_id in ["d55", "w22"]:
            return message.author.id == 972501446085992490
        elif objective_id == "d121":
            return message.author.id == 658290426435862619
    
    # Failsafe.
    return False




    
     
######################################################################################################################################################
### PURCHASE CONFIRMATION ############################################################################################################################
######################################################################################################################################################

@AutoDetection(
    objectives = {
        "d185": "Someone purchases 10+ special bread packs at once"
    }
)
async def purchase_confirmation(
        message: discord.Message,
        objective_id: int,
        **kwargs
    ) -> bool:
    if not u_interface.mm_checks(message, check_reply=True):
        return False
    
    if len(list(re.finditer(" : \+[\d,]+, -> [\d,]+", message.content))) >= 8:
        # Very very likely a special bread pack.
        individual_amount = {}

        for item in u_values.special_and_rare:
            individual_amount[item] = u_text.extract_number(f"{item.internal_emoji} : \+([\d,]+), -> [\d,]+", message.content, default=0)
            individual_amount[item] += u_text.extract_number(f"{item.emoji} : \+([\d,]+), -> [\d,]+", message.content, default=0)
        
        bought = sum(individual_amount.values()) // 100

        if objective_id == "d185":
            return bought >= 10






######################################################################################################################################################
##### I/O FUNCTIONS ##################################################################################################################################
######################################################################################################################################################

async def handle_completed(
        bot: u_custom.CustomBot,
        message: discord.Message,
        database: u_files.DatabaseInterface,
        completed_objectives: list[str],
        bingo_data: dict
    ) -> None:
    """Handles completed objectives. This will handle updating the live data and sending any messages that need to be sent.

    Args:
        bot (u_custom.CustomBot): The bot object.
        message (discord.Message): The message that triggered this.
        database (u_files.DatabaseInterface): The database.
        completed_objectives (list[str]): The list of objectives that were completed as a list of strings. Each string should be the board it's on ('d' or 'w') and id of the objective. Example: ['d0', 'w33'].
    """
    if completed_objectives is None:
        completed_objectives = []
    
    daily_lines = []
    weekly_lines = []

    alternate = False

    daily_tile_list = None
    weekly_tile_list = None

    for objective in completed_objectives:
        tile_list = None
        if objective.startswith("d"):
            if daily_tile_list is None:
                daily_tile_list = u_bingo.tile_list_5x5(database)
                
            tile_list = daily_tile_list.copy()
        else:
            if weekly_tile_list is None:
                weekly_tile_list = u_bingo.tile_list_9x9(database)

            tile_list = weekly_tile_list.copy()
        
        tile_data = tile_list[int(objective[1:])]

        if not alternate and tile_data.get("alternate", False):
            alternate = True
        
        full_id = "{:03d}".format(int(objective[1:]))

        if objective.startswith("d"):
            spot = bingo_data["daily_tile_string"].index(full_id)
            bingo_data["daily_enabled"][spot] = True
        else:
            spot = bingo_data["weekly_tile_string"].index(full_id)
            bingo_data["weekly_enabled"][spot] = True
        
        if tile_data.get("silent", True):
            if objective.startswith("d"):
                daily_lines.append(f"- {tile_data['name']} ({full_id})")
            else:
                weekly_lines.append(f"- {tile_data['name']} ({full_id})")
        
    # Update the database.
    new = {
        "daily_tile_string": "".join(bingo_data["daily_tile_string"]),
        "daily_enabled": u_bingo.compile_enabled(bingo_data["daily_enabled"]),
        "daily_board_id": bingo_data["daily_board_id"],
        "weekly_tile_string": "".join(bingo_data["weekly_tile_string"]),
        "weekly_enabled": u_bingo.compile_enabled(bingo_data["weekly_enabled"]),
        "weekly_board_id": bingo_data["weekly_board_id"]
    }

    u_bingo.update_live(
        database = database,
        bot = bot,
        new_data = new
    )

    # Potentially send the message.

    if len(daily_lines) + len(weekly_lines) == 0:
        # Nothing to send, the objective(s) completed were likely silent ones.
        print("Nothing to send.")
        return
    
    if u_checks.sensitive_check(message.channel) or alternate:
        if message.channel.id == 958705808860921906 or (isinstance(message.channel, discord.Thread) and message.channel.parent.id == 958705808860921906):
            reference = await bot.fetch_channel(1138583859508813955)
        else:
            reference = await bot.fetch_channel(958705808860921906)
    else:
        reference = message

    content_lines = []

    if len(daily_lines) > 0:
        if len(daily_lines) == 1:
            content_lines.append("Bingo objective completed!")
        else:
            content_lines.append(f"{len(daily_lines)} bingo objectives completed!")
        
        content_lines += daily_lines
    
    if len(weekly_lines) > 0:
        if len(daily_lines) == 1:
            content_lines.append("Weekly bingo objective completed!")
        else:
            content_lines.append(f"{len(weekly_lines)} weekly bingo objectives completed!")
        
        content_lines += weekly_lines
    
    print("\n".join(content_lines))

    try:
        if isinstance(reference, discord.Message):
            await reference.reply(
                "\n".join(content_lines),
                mention_author = False
            )
        else:
            await reference.send(
                "\n".join(content_lines)
            )
    except discord.Forbidden:
        print(traceback.format_exc())

        reference = await bot.fetch_channel(1196865970355052644)
        await reference.send(
            "\n".join([message.jump_url, "\n\n"] + content_lines)
        )
    
    try:
        await message.add_reaction("<a:you_did_a_thing:1090712320663109772>")
    except discord.Forbidden:
        pass
        
    

        

        
        

async def run_detection(
        objective_id: int,
        bot: u_custom.CustomBot,
        message: discord.Message,
        database: u_files.DatabaseInterface,
        bingo_data: dict,
        **kwargs
    ) -> bool:
    """Tests a single objective from the provided objective id.

    Args:
        objective_id (int): The id of the objective to run.
        bot (u_custom.CustomBot): The bot object.
        message (discord.Message): The message that is being checked.
        database (u_files.DatabaseInterface): The database.
        bingo_data (dict): The current live bingo data.

    Returns:
        bool: Whether the objective was triggered.
    """
    if objective_id not in all_detection:
        return False
    
    for func in all_detection[objective_id]:
        if await func(
                bot = bot,
                message = message,
                database = database,
                objective_id = objective_id,
                bingo_data = bingo_data,
                **kwargs
            ):
            return True
    
    return False

async def run_detection_set(
        objectives: list[int],
        bot: u_custom.CustomBot,
        message: discord.Message,
        database: u_files.DatabaseInterface,
        bingo_data: dict,
        **kwargs
    ) -> list[int]:
    """Runs a set of objective tests from the provided list of objective ids.

    Args:
        objectives (list[int]): A list of objective ids to test.
        bot (u_custom.CustomBot): The bot object.
        message (discord.Message): The message to test the objectives on.
        database (u_files.DatabaseInterface): The database.
        bingo_data (dict): The current live bingo data.

    Returns:
        list[int]: A list of objective ids that were triggered. If an objective was not triggered it will not be in here, so an empty list means nothing was triggered.
    """
    triggered = []

    if len(objectives) == 0:
        objectives = main_detection_dict.keys()

    for objective_id in objectives:
        if await run_detection(
                objective_id = objective_id,
                bot = bot,
                message = message,
                database = database,
                bingo_data = bingo_data,
                **kwargs
            ):
                triggered.append(objective_id)
    
    return triggered

async def on_stonk_tick_detection(
        bot: u_custom.CustomBot,
        message: discord.Message,
        database: u_files.DatabaseInterface,
        stonk_data: dict,
        bingo_data: dict
    ) -> None:   
    """Runs the on stonk tick part of the auto detection for both the daily and weekly boards.

    Args:
        bot (u_custom.CustomBot): The bot object.
        message (discord.Message): The message that is being processed.
        database (u_files.DatabaseInterface): The database.
        stonk_data (dict): The stonk data for this tick.
        bingo_data (dict): The current bingo data. Should include the following:
        - daily_tile_string (list[str]): The daily board tile string, as a list of strings.
        - daily_enabled (list[bool]): List of booleans for whether each tile is completed on the daily board.
        - weekly_tile_string (list[str]): The weekly board tile string, as a list of strings.
        - weekly_enabled (list[bool]): List of booleans for whether each tile is completed on the weekly board.
    """
    triggered = []

    for index, objective in enumerate(bingo_data.get("daily_tile_string", list())):
        if bingo_data.get("daily_enabled", list())[index]:
            continue
        key = f"d{int(objective)}"

        if key not in stonk_detection_dict:
            continue
        
        try:
            if await run_detection(
                    stonk_data = stonk_data,
                    objective_id = key,
                    bot = bot,
                    message = message,
                    database = database,
                    bingo_data = bingo_data
                ):
                triggered.append(key)
        except:
            print(traceback.format_exc())
            continue

    for index, objective in enumerate(bingo_data.get("weekly_board", list())):
        if bingo_data.get("weekly_enabled", list())[index]:
            continue
        key = f"w{int(objective)}"

        if key not in stonk_detection_dict:
            continue

        try:
            if await run_detection(
                    stonk_data = stonk_data,
                    objective_id = key,
                    bot = bot,
                    message = message,
                    database = database,
                    bingo_data = bingo_data
                ):
                triggered.append(key)
        except:
            print(traceback.format_exc())
            continue
    
    if len(triggered) >= 1:
        await handle_completed(
            bot = bot,
            message = message,
            database = database,
            completed_objectives = triggered,
            bingo_data = bingo_data
        )

async def chains_detection(
        bot: u_custom.CustomBot,
        message: discord.Message,
        database: u_files.DatabaseInterface,
        chain_data: dict,
        bingo_data: dict
    ) -> None:   
    """Runs the chains part of the auto detection for both the daily and weekly boards.

    Args:
        bot (u_custom.CustomBot): The bot object.
        message (discord.Message): The message that is being processed.
        database (u_files.DatabaseInterface): The database.
        chain_data (dict): The data for the chain that is being processed.
        bingo_data (dict): The current bingo data. Should include the following:
        - daily_tile_string (list[str]): The daily board tile string, as a list of strings.
        - daily_enabled (list[bool]): List of booleans for whether each tile is completed on the daily board.
        - weekly_tile_string (list[str]): The weekly board tile string, as a list of strings.
        - weekly_enabled (list[bool]): List of booleans for whether each tile is completed on the weekly board.
    """

    triggered = []

    if "105" in bingo_data.get("daily_tile_string", list()): # The same message is sent 30+ times in a row in #chains
        if message.channel.id == 1020394850463531019 and chain_data.get("count", 0) >= 30:
            triggered.append("d105")

    if "161" in bingo_data.get("daily_tile_string", list()): # A chain of 10+ messages occurs outside of #chains
        if message.channel.id != 1020394850463531019 and chain_data.get("count", 0) >= 10:
            triggered.append("d161")

    if "039" in bingo_data.get("weekly_tile_string", list()): # The same message is sent 60+ times in a row in #chains
        if message.channel.id == 1020394850463531019 and chain_data.get("count", 0) >= 60:
            triggered.append("w39")

    if "071" in bingo_data.get("weekly_tile_string", list()): # A chain of 30+ messages occurs outside of #chains
        if message.channel.id != 1020394850463531019 and chain_data.get("count", 0) >= 30:
            triggered.append("w71")
    
    if len(triggered) >= 1:
        await handle_completed(
            bot = bot,
            message = message,
            database = database,
            completed_objectives = triggered,
            bingo_data = bingo_data
        )

async def on_message_detection(
        bot: u_custom.CustomBot,
        message: discord.Message,
        database: u_files.DatabaseInterface,
        bingo_data: dict
    ) -> None:
    """Runs the on message part of the auto detection for both the daily and weekly boards.

    Args:
        bot (u_custom.CustomBot): The bot object.
        message (discord.Message): The message that is being processed.
        database (u_files.DatabaseInterface): The database.
        bingo_data (dict): The current bingo data. Should include the following:
        - daily_tile_string (list[str]): The daily board tile string, as a list of strings.
        - daily_enabled (list[bool]): List of booleans for whether each tile is completed on the daily board.
        - weekly_tile_string (list[str]): The weekly board tile string, as a list of strings.
        - weekly_enabled (list[bool]): List of booleans for whether each tile is completed on the weekly board.
    """
    triggered = []

    for index, objective in enumerate(bingo_data.get("daily_tile_string", list())):
        if bingo_data.get("daily_enabled", list())[index]:
            continue
        key = f"d{int(objective)}"


        if key not in main_detection_dict:
            continue
        
        try:
            if await run_detection(
                    objective_id = key,
                    bot = bot,
                    message = message,
                    database = database,
                    bingo_data = bingo_data
                ):
                triggered.append(key)
        except:
            print(traceback.format_exc())
            continue

    for index, objective in enumerate(bingo_data.get("weekly_tile_string", list())):
        if bingo_data.get("weekly_enabled", list())[index]:
            continue
        key = f"w{int(objective)}"

        if key not in main_detection_dict:
            continue

        try:
            if await run_detection(
                    objective_id = key,
                    bot = bot,
                    message = message,
                    database = database,
                    bingo_data = bingo_data
                ):
                triggered.append(key)
        except:
            print(traceback.format_exc())
            continue
    
    if len(triggered) >= 1:
        await handle_completed(
            bot = bot,
            message = message,
            database = database,
            completed_objectives = triggered,
            bingo_data = bingo_data
        )

######################################################################################################################################################
##### MODULE PREP ####################################################################################################################################
######################################################################################################################################################


main_detection_dict = {}
stonk_detection_dict = {}
all_detection = {}

def prep():
    global autodetection_dict, stonk_detection_dict, all_detection

    global_copy = globals().copy()
    for func in global_copy:
        try:
            detection_type = global_copy[func].detection_type
            if global_copy[func].detection_type != "main":
                global_copy[func] = global_copy[func].func
            
            if detection_type == "stonks":
                dict_use = stonk_detection_dict
            else:
                dict_use = main_detection_dict

            for objective_id in global_copy[func].objectives:
                if objective_id in dict_use:
                    if global_copy[func] in dict_use[objective_id]:
                        continue
                    
                    dict_use[objective_id].append(global_copy[func])
                    continue

                dict_use[objective_id] = [global_copy[func]]
        except AttributeError:
            continue

    all_detection = main_detection_dict.copy()
    all_detection.update(stonk_detection_dict)

def on_reload():
    importlib.reload(u_values)

    for module_name, module in sys.modules.copy().items():
        if not module_name.startswith("utility."):
            continue

        importlib.reload(module)

    prep()

prep()