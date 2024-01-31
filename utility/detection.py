"""Auto-detection for the bingo objectives."""

import discord
import typing
import re

import sys

import utility.files as u_files
import utility.custom as u_custom
import utility.interface as u_interface
import utility.values as u_values
import utility.bread as u_bread
import utility.stonks as u_stonks
import utility.text as u_text

import importlib

importlib.reload(u_values)
        
######################################################################################################################################################
##### DECORATOR ######################################################################################################################################
######################################################################################################################################################

class AutoDetection():
    def __init__(self,
            objectives: dict[int, str]
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

@AutoDetection(
    objectives = {
        "d0": "MoaK",
        "d33": "Someone gets a gold gem"
    }
)
async def item_in_roll(
        message: discord.Message,
        objective_id: int,
        **kwargs
    ) -> bool:
    if not u_interface.is_bread_roll(message):
        return False
    
    items = {
        "d0": u_values.anarchy_chess,
        "d33": u_values.gem_gold
    }
    
    return items[objective_id].internal_emoji in message.content

######################################################################################################################################################

@AutoDetection(
    objectives = {
        "d0": "MoaK",
        "d33": "Someone gets a gold gem",
        "d5": "Someone wins the lottery",
        "d19": "Kapola gets a lottery"
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
    
    if objective_id == "d5":
        return "You won the lottery" in message.content

    if objective_id == "d19":
        print(message.reference)
        return "You won the lottery" in message.content and message.reference.resolved.author.id == 713053430075097119
    
    summary_items = {
        "d0": u_values.anarchy_chess,
        "d33": u_values.gem_gold
    }

    if objective_id in summary_items:
        pattern = "{}: (\d+)".format(re.escape(summary_items[objective_id].internal_emoji))
        matched = re.search(pattern, message.content)

        if matched is not None and int(matched.group(1)) >= 1:
            return True

    # Failsafe.
    return False

######################################################################################################################################################

@AutoDetection(
    objectives = {
        "d1": "Someone gets an omega",
        "d33": "Someone gets a gold gem"
    }
)
async def alchemy_check(
        message: discord.Message,
        objective_id: int,
        **kwargs
    ) -> bool:
    if not u_interface.mm_checks(message, check_reply=True):
        return False
    
    if "Well done. You have created" not in message.content:
        return False
    
    searched = re.search(r"Well done\. You have created (\d+) (<:.+:\d+>)\. You now have", message.content)

    alchemize_amount = int(searched.group(1))
    alchemized_item = searched.group(2)

    detect_items = {
        "d1": u_values.omega_chessatron,
        "d33": u_values.gem_gold
    }

    if objective_id in detect_items:
        if alchemized_item == detect_items[objective_id].internal_emoji and alchemize_amount >= 1:
            return True
    
    # Failsafe.
    return False

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

@AutoDetection(
    objectives = {
        "d31": "Someone says 'Holy ____' and doesn't say 'holy hell'"
    }
)
async def in_message(
        message: discord.Message,
        objective_id: int,
        **kwargs
    ) -> bool:
    if objective_id == "d31":
        match = re.search("holy(?! hell)", message.content.lower())
        return match is not None
            

######################################################################################################################################################

@AutoDetection(
    objectives = {
        "d7": "$brick gamble",
        "d12": "Someone fales '$brick' message",
        "d29": "Someone does $bread (move)"
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

    startswith = {
        "d7": "$brick gamble",
        "d12": r"\$brick"
    }
    
    if objective_id in startswith:
        return mod_content.startswith(startswith[objective_id])
    return False

######################################################################################################################################################

@AutoDetection(
    objectives = {
        "d17": "Golden brick",
        "d26": "MM chess en passant!!",
        "d28": "Bongcloud in an MM chess game",
    }
)
async def mm_messages(
        message: discord.Message,
        objective_id: int,
        **kwargs
    ) -> bool:
    if not u_interface.mm_checks(message, check_reply=False):
        return False
    
    if objective_id == "d17":
        return message.content == u_values.brick_gold.internal_emoji
    
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

@AutoDetection(
    objectives = {
        "d9": "Someone gets an anarchy gambling"
    }
)
async def gamble_result(
        message: discord.Message,
        objective_id: int,
        **kwargs
    ) -> bool:
    if not u_interface.mm_checks(message, check_reply=True):
        return False

    if "You found a brick" in message.content:
        if "looks like you'll" in message.content:
            item_won = u_values.brick_gold

            dough_won = re.match("Looks like you'll be able to sell this one for ([\d,]+) dough.", message.content)
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
        
        item_regex = re.search("With a ([\w\d:<>]+), you won ([\d,]+) dough.", message.content)

        if item_regex is None:
            return False
        
        item_won = u_values.get_item(item_regex.group(1))
        dough_won = u_text.return_numeric(item_regex.group(2))
    
    

    if objective_id == "d9":
        return item_won in [u_values.anarchy, u_values.holy_hell, u_values.anarchy_chess]


    


    

@AutoDetection(
    objectives = {
        "d55": "Nixon buys extra gambles",
        "w22": "Nixon buys extra gambles",

        "d121": "Duck Duck Go r/place buys extra gambles"
    }
)
async def purchased_item(
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
##### I/O FUNCTIONS ##################################################################################################################################
######################################################################################################################################################

async def handle_completed(
        bot: u_custom.CustomBot,
        message: discord.Message,
        database: u_files.DatabaseInterface,
        completed_objectives: list[str]
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
    
    if len(completed_objectives) == 0:
        return

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

# async def on_stonk_tick_detection(
#         bot: u_custom.CustomBot,
#         message: discord.Message,
#         bingo_data: dict
#     ) -> None:   
#     """Runs the on stonk tick part of the auto detection for both the daily and weekly boards.

#     Args:
#         bot (u_custom.CustomBot): The bot object.
#         message (discord.Message): The message that is being processed.
#         bingo_data (dict): The current bingo data. Should include the following:
#         - daily_board (list[str]): The daily board tile string, as a list of strings.
#         - daily_enabled (list[bool]): List of booleans for whether each tile is completed on the daily board.
#         - weekly_board (list[str]): The weekly board tile string, as a list of strings.
#         - weekly_enabled (list[bool]): List of booleans for whether each tile is completed on the weekly board.
#     """

# async def chains_detection(
#         bot: u_custom.CustomBot,
#         message: discord.Message,
#         bingo_data: dict
#     ) -> None:   
#     """Runs the chains part of the auto detection for both the daily and weekly boards.

#     Args:
#         bot (u_custom.CustomBot): The bot object.
#         message (discord.Message): The message that is being processed.
#         bingo_data (dict): The current bingo data. Should include the following:
#         - daily_board (list[str]): The daily board tile string, as a list of strings.
#         - daily_enabled (list[bool]): List of booleans for whether each tile is completed on the daily board.
#         - weekly_board (list[str]): The weekly board tile string, as a list of strings.
#         - weekly_enabled (list[bool]): List of booleans for whether each tile is completed on the weekly board.
#     """


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
        bingo_data (dict): The current bingo data. Should include the following:
        - daily_board (list[str]): The daily board tile string, as a list of strings.
        - daily_enabled (list[bool]): List of booleans for whether each tile is completed on the daily board.
        - weekly_board (list[str]): The weekly board tile string, as a list of strings.
        - weekly_enabled (list[bool]): List of booleans for whether each tile is completed on the weekly board.
    """
    triggered = []

    for index, objective in enumerate(bingo_data.get("daily_board", list())):
        if bingo_data.get("daily_enabled", list())[index]:
            continue
        key = f"d{int(objective)}"

        if key not in main_detection_dict:
            continue

        if await run_detection(
                objective_id = key,
                bot = bot,
                message = message,
                database = database,
                bingo_data = bingo_data
            ):
            triggered.append(key)

    for index, objective in enumerate(bingo_data.get("weekly_board", list())):
        if bingo_data.get("weekly_enabled", list())[index]:
            continue
        key = f"w{int(objective)}"

        if key not in main_detection_dict:
            continue

        if await run_detection(
                objective_id = key,
                bot = bot,
                message = message,
                database = database,
                bingo_data = bingo_data
            ):
            triggered.append(key)
    
    await handle_completed(
        bot = bot,
        message = message,
        database = database,
        completed_objectives = triggered
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