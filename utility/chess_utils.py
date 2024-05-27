"""Home of the various Chess bots.

This can't be called `chess` due to conflicting with the `chess` library."""

from discord.ext import commands
import discord
import typing
import random
import io
import time
import datetime
import pytz
import copy
import math
import os

# pip install chess
import chess
import chess.pgn
import chess.svg

# pip install CairoSVG
import cairosvg

import utility.files as u_files
import utility.interface as u_interface
import utility.text as u_text

class ChessBot:
    name = "generic_bot"
    description = """Generic Chess bot."""
    creator = "Duck"

    def __init__(
            self: typing.Self,
            database_data: dict
        ) -> None:
        self.load(database_data)
    
    # Not needed for subclasses, this one is fine.
    @classmethod
    def formatted_name(cls: typing.Callable) -> str:
        return cls.name.replace("_"," ").title()
    
    # Not needed for subclasses, this one is fine.
    @classmethod
    def get_elo(
            cls: typing.Callable,
            database: u_files.DatabaseInterface
        ) -> int:
        return get_bot_elo(
            database = database,
            bot = cls.name
        )
    
    # Not needed for subclasses, this one is fine.
    @classmethod
    def get_name(
            cls: typing.Callable,
            database: u_files.DatabaseInterface
        ) -> str:
        return f"{cls.formatted_name()} ({u_text.smart_number(round(cls.get_elo(database)))})"

    ############### Data interaction. ###############
    
    # Optional for subclasses, required if data needs to be saved between moves.
    def load(
            self: typing.Self,
            data: dict
        ) -> None:
        """Method called when the bot is initialized, and allows for the loading of data from the database."""
        pass

    # Optional for subclasses, required if data needs to be saved between moves.
    def save(self: typing.Self) -> dict | None:
        """Method called after the bot is run. The dict returned will be saved to the database.
        This allows for the saving of data between moves.
        This only gets saved if the output is a dictionary, even a list will not be saved.

        If `None` is returned then nothing will be saved."""
        return None

    ############### Main interaction. ###############

    # Required for subclasses.
    def turn(
            self: typing.Self,
            board: chess.Board
        ) -> chess.Move:
        """Method called when it is this bot's turn in the Chess game.

        Args:
            board (chess.Board): A copy of the current board.

        Returns:
            chess.Move: The move this bot would like to play.
        """
        # Return the first listed legal move.
        return list(board.legal_moves)[0]

#######################################################################################################################
##### THE BOTS ########################################################################################################
#######################################################################################################################

class RandomSimple(ChessBot):
    name = "random_simple"
    description = """Gets a list of all possible moves, and chooses a random one.."""
    creator = "Duck"

    def turn(
            self: typing.Self,
            board: chess.Board
        ) -> chess.Move:
        return random.choice(list(board.legal_moves))

class RandomBot(ChessBot):
    name = "random"
    description = """Chooses a random piece, and then from there a random move that piece can make.\nThis means each piece has an equal chance of being moved.\nFor a bot that chooses a random move from a giant list of all the possible moves `random_simple` is what you're looking for."""
    creator = "Duck"

    def turn(
            self: typing.Self,
            board: chess.Board
        ) -> chess.Move:
        all_pieces = []

        for piece in chess.PIECE_TYPES:
            pieces = board.pieces(piece, board.turn)

            for tile in pieces:
                all_pieces.append(tile)
        
        for _ in all_pieces:
            chosen_tile = random.choice(all_pieces)
                
            all_moves = board.legal_moves

            possible_moves = []
            for move in all_moves:
                if move.from_square == chosen_tile:
                    possible_moves.append(move)
            
            if len(possible_moves) == 0:
                continue
            
            return random.choice(possible_moves)
        
        # Failsafe, this should never happen, and it might not even help.
        return random.choice(list(board.legal_moves))

class MoveCount(ChessBot):
    name = "move_count"
    creator = "Duck"
    description = "Tries to maximize the amount of moves it has."

    def count_moves(
            self: typing.Self,
            board: chess.Board,
            side: bool
        ) -> int:
        if board.turn == side:
            return len(list(board.legal_moves))

        board.push(chess.Move.null())
        amt = len(list(board.legal_moves))
        board.pop()
        return amt

    def turn(
            self: typing.Self,
            board: chess.Board
        ) -> chess.Move:
        try:
            board_copy = copy.deepcopy(board)

            side = board.turn

            amounts = {}

            for move in board.legal_moves:
                board_copy.push(move)
                if board_copy.is_checkmate():
                    return move
                # If the game is over, but it's not checkmate.
                if board_copy.is_game_over():
                    continue
                
                track = []
                
                for depth_move in board_copy.legal_moves:
                    board_copy.push(depth_move)
                    track.append(self.count_moves(board_copy, side))

                    board_copy.pop()

                board_copy.pop()

                if len(track) == 0:
                    track = [0]

                amounts[move] = min(track)
            
            if len(amounts) == 0:
                return random.choice(list(board.legal_moves))

            play = max(amounts, key=amounts.get)
            board.push(play)

            board.pop()
            
            return play
        except AssertionError:
            return random.choice(list(board.legal_moves))

class Pi(ChessBot):
    name = "pi"
    creator = "Duck"
    description = "π"

    def __init__(
            self: typing.Self,
            database_data: dict
        ) -> None:
        try:
            with open(os.path.join("data", "100k_pi.txt"), "r") as file_read:
                self.digits = file_read.read()
        except FileNotFoundError:
            self.digits = None

        super().__init__(database_data)
    
    def load(
            self: typing.Self,
            data: dict
        ) -> None:
        if self.digits is None:
            self.digit_position = None
        else:
            self.initial = data.get("initial", random.randint(50, 50_000))
            self.digit_position = data.get("digit_position", self.initial)
    
    def save(self: typing.Self) -> dict | None:
        return {
            "digit_position": self.digit_position,
            "initial": self.initial
        }
    
    def increment(self: typing.Self) -> None:
        if self.initial < 25_000:
            self.digit_position += 1
        else:
            self.digit_position -= 1
    
    def turn(
            self: typing.Self,
            board: chess.Board
        ) -> chess.Move:
        while True:
            if self.digits is None:
                return random.choice(list(board.legal_moves))
            
            digits = int(self.digits[self.digit_position * 2:self.digit_position * 2 + 2])

            all_pieces = []
            for j in range(6):
                pieces = board.pieces(chess.PIECE_TYPES[j], board.turn)

                for tile in pieces:
                    all_pieces.append((board.piece_at(tile), tile))

            piece_count = len(all_pieces)
            
            cutoff = (100 // piece_count) * piece_count

            if digits >= cutoff:
                while digits >= cutoff:
                    self.increment()
                    digits = int(self.digits[self.digit_position * 2:self.digit_position * 2 + 2])

            chosen_piece, chosen_tile = all_pieces[int(digits / cutoff * piece_count)]
            
            all_moves = board.legal_moves

            possible_moves = []
            for move in all_moves:
                if move.from_square == chosen_tile:
                    possible_moves.append(move)
            
            ###########################################
            self.increment()
            digits = int(self.digits[self.digit_position * 2:self.digit_position * 2 + 2])
            ###########################################

            possible_move_count = len(possible_moves)

            if possible_move_count == 0:
                self.increment()
                continue
            
            cutoff = (100 // possible_move_count) * possible_move_count

            if digits >= cutoff:
                while digits >= cutoff:
                    self.increment()
                    digits = int(self.digits[self.digit_position * 2:self.digit_position * 2 + 2])
        
            return possible_moves[int(digits / cutoff * possible_move_count)]

class E(ChessBot):
    name = "e"
    creator = "Duck"
    description = "e"

    def __init__(
            self: typing.Self,
            database_data: dict
        ) -> None:
        try:
            with open(os.path.join("data", "100k_pi.txt"), "r") as file_read:
                self.digits = file_read.read()
        except FileNotFoundError:
            self.digits = None

        super().__init__(database_data)
    
    def load(
            self: typing.Self,
            data: dict
        ) -> None:
        if self.digits is None:
            self.digit_position = None
        else:
            self.initial = data.get("initial", random.randint(50, 50_000))
            self.digit_position = data.get("digit_position", self.initial)
    
    def save(self: typing.Self) -> dict | None:
        return {
            "digit_position": self.digit_position,
            "initial": self.initial
        }
    
    def increment(self: typing.Self) -> None:
        if self.initial < 25_000:
            self.digit_position += 1
        else:
            self.digit_position -= 1
    
    def turn(
            self: typing.Self,
            board: chess.Board
        ) -> chess.Move:
        while True:
            if self.digits is None:
                return random.choice(list(board.legal_moves))
            
            digits = int(self.digits[self.digit_position * 2:self.digit_position * 2 + 2])

            all_pieces = []
            for j in range(6):
                pieces = board.pieces(chess.PIECE_TYPES[j], board.turn)

                for tile in pieces:
                    all_pieces.append((board.piece_at(tile), tile))

            piece_count = len(all_pieces)
            
            cutoff = (100 // piece_count) * piece_count

            if digits >= cutoff:
                while digits >= cutoff:
                    self.increment()
                    digits = int(self.digits[self.digit_position * 2:self.digit_position * 2 + 2])

            chosen_piece, chosen_tile = all_pieces[int(digits / cutoff * piece_count)]
            
            all_moves = board.legal_moves

            possible_moves = []
            for move in all_moves:
                if move.from_square == chosen_tile:
                    possible_moves.append(move)
            
            ###########################################
            self.increment()
            digits = int(self.digits[self.digit_position * 2:self.digit_position * 2 + 2])
            ###########################################

            possible_move_count = len(possible_moves)

            if possible_move_count == 0:
                self.increment()
                continue
            
            cutoff = (100 // possible_move_count) * possible_move_count

            if digits >= cutoff:
                while digits >= cutoff:
                    self.increment()
                    digits = int(self.digits[self.digit_position * 2:self.digit_position * 2 + 2])
        
            return possible_moves[int(digits / cutoff * possible_move_count)]

class Tau(ChessBot):
    name = "tau"
    creator = "Duck"
    description = "τ"

    def __init__(
            self: typing.Self,
            database_data: dict
        ) -> None:
        try:
            with open(os.path.join("data", "100k_tau.txt"), "r") as file_read:
                self.digits = file_read.read()
        except FileNotFoundError:
            self.digits = None

        super().__init__(database_data)
    
    def load(
            self: typing.Self,
            data: dict
        ) -> None:
        if self.digits is None:
            self.digit_position = None
        else:
            self.initial = data.get("initial", random.randint(50, 50_000))
            self.digit_position = data.get("digit_position", self.initial)
    
    def save(self: typing.Self) -> dict | None:
        return {
            "digit_position": self.digit_position,
            "initial": self.initial
        }
    
    def increment(self: typing.Self) -> None:
        if self.initial < 25_000:
            self.digit_position += 1
        else:
            self.digit_position -= 1
    
    def turn(
            self: typing.Self,
            board: chess.Board
        ) -> chess.Move:
        while True:
            if self.digits is None:
                return random.choice(list(board.legal_moves))
            
            digits = int(self.digits[self.digit_position * 2:self.digit_position * 2 + 2])

            all_pieces = []
            for j in range(6):
                pieces = board.pieces(chess.PIECE_TYPES[j], board.turn)

                for tile in pieces:
                    all_pieces.append((board.piece_at(tile), tile))

            piece_count = len(all_pieces)
            
            cutoff = (100 // piece_count) * piece_count

            if digits >= cutoff:
                while digits >= cutoff:
                    self.increment()
                    digits = int(self.digits[self.digit_position * 2:self.digit_position * 2 + 2])

            chosen_piece, chosen_tile = all_pieces[int(digits / cutoff * piece_count)]
            
            all_moves = board.legal_moves

            possible_moves = []
            for move in all_moves:
                if move.from_square == chosen_tile:
                    possible_moves.append(move)
            
            ###########################################
            self.increment()
            digits = int(self.digits[self.digit_position * 2:self.digit_position * 2 + 2])
            ###########################################

            possible_move_count = len(possible_moves)

            if possible_move_count == 0:
                self.increment()
                continue
            
            cutoff = (100 // possible_move_count) * possible_move_count

            if digits >= cutoff:
                while digits >= cutoff:
                    self.increment()
                    digits = int(self.digits[self.digit_position * 2:self.digit_position * 2 + 2])
        
            return possible_moves[int(digits / cutoff * possible_move_count)]

class CCPBot(ChessBot):
    name = "ccpbot"
    description = """BORN TO BLUNDER / TOURNAMENT IS A FUCK / 將死 Capture Em All 1989 / I am martin / 410,757,864,530 HUNG QUEENS"""
    creator = "ph03n1x"

    def turn(
            self: typing.Self,
            board: chess.Board
        ) -> chess.Move:

        # This bot has the following priorities:
        # Priority 1: Checkmate
        # Priority 2: Deliver a check
        # Priority 3: Capture a piece
        # Priority 4: Push a piece closer to the king.

        # First, classify all the moves, and while doing so:
        # Step 1: If you find a checkmate, play it immediately.

        check_moves = []
        cap_moves = []

        board_copy = copy.deepcopy(board)
        for move in board.legal_moves:
            if board.gives_check(move): # Is it a check?
                check_moves.append(move) # If so, note the move as a check, then scan for mate.
                board_copy.push(move) 
                if board_copy.is_checkmate(): # If it is mate, then play it now.
                    return move
                board_copy.pop()
            elif board.is_capture(move): # If it is not check, check if it is a capture.
                cap_moves.append(move) # Note any captures.            

        # Step 2: If no mate exists, Check the king

        if len(check_moves) != 0:
            return random.choice(check_moves)

        # Step 3: ...and if that can't happen, Capture a piece

        if len(cap_moves) != 0:
            return random.choice(cap_moves)
        
        # Step 4: ...and if that can't happen, Push a piece closer to the enemy king.

        # All potential future boards will be assigned a "rating" value for average
        # distance from the enemy1 king with dist(). Lower is better.
        
        moveDict = {}

        for move in board.legal_moves:
            board_copy.push(move) 
            moveDict[move] = self.rateDistFromKing(board_copy, board.turn)
            board_copy.pop()

        return min(moveDict, key=moveDict.get)
            
    # Functions for use in turn().

    def helper_numToSquare(self, boardNum): # Must input an integer.
        if boardNum < 0 or boardNum >= 64:
            return None       
        return [(boardNum // 8)+1,boardNum % 8+1]

    def rateDistFromKing(self, thisBoard, color):
        # For now, all pieces' distance from the king will be judged.
        # It should be fairly easy to adjust this so that a piece type is ignored later.

        thisBoard.turn = color
        sumDist = 0
        totalPieces = 0
        for piece in chess.PIECE_TYPES:
            listPieces = list(thisBoard.pieces(piece, thisBoard.turn))
            for item in listPieces:
                sumDist += math.dist(self.helper_numToSquare(item),self.helper_numToSquare(thisBoard.king(not thisBoard.turn)))
                totalPieces += 1
        if totalPieces == 0:
            return 0
        return sumDist/totalPieces

class PacifistBot(ChessBot):
    name = "pacifistbot"
    description = """With the power of friendship I shall win!"""
    creator = "ph03n1x"

    PAC_PIECE_VALUES = [1,3,3,5,9,3] # For use in distance calc. P,N,B,R,Q,K

    def turn(
            self: typing.Self,
            board: chess.Board
        ) -> chess.Move:

        board_copy = copy.deepcopy(board)
        moveDict = {}

        for move in board.legal_moves:
            moveDict[move] = self.ratePacifism(move, board_copy, board.turn)

        # Uncomment this to see the board before every move.
        # print(board)
        # print()

        highValMove = max(moveDict, key=moveDict.get)
        highVal = self.ratePacifism(highValMove, board_copy, board.turn)
        return random.choice([k for k, v in moveDict.items() if v == highVal])
            
    # Functions for use in turn().

    def helper_numToSquare(self, boardNum): # Must input an integer.
        if boardNum < 0 or boardNum >= 64:
            print("Illegal input made.")
            return None       
        return [(boardNum // 8)+1,boardNum % 8+1]
    
    def helper_squareToNum(self, boardNum): # Must input a list.
        if type(boardNum) != list:
            print("Illegal input made.")
            return None       
        return (boardNum[0]-1)*8+(boardNum[1]-1)

    def ratePacifism(self, move, thisBoard, color):
        # For now, all pieces' distance from the king will be judged.
        # It should be fairly easy to adjust this so that a piece type is ignored later.

        thisBoard.turn = color
        sumDist = 0
        totalPieces = 0
        thisBoard.push(move) 
        if chess.Board.is_checkmate(thisBoard):
            thisBoard.pop()
            return -93258468905632490863452
        if chess.Board.is_check(thisBoard):
            checkCount = len(chess.Board.checkers(thisBoard))
            thisBoard.pop()
            return -5000*checkCount
        else:
            thisBoard.pop()
        if chess.Board.is_en_passant(thisBoard, move):
            return -100
        if chess.Board.is_capture(thisBoard, move):
            return -100*self.getPieceValue(thisBoard, move.to_square)
        return 0
        
    def getPieceValue(self, thisBoard, square):
        if chess.Board.piece_type_at(thisBoard, square) == chess.PAWN:
            return self.PAC_PIECE_VALUES[0]
        elif chess.Board.piece_type_at(thisBoard, square) == chess.KNIGHT:
            return self.PAC_PIECE_VALUES[1]
        elif chess.Board.piece_type_at(thisBoard, square) == chess.BISHOP:
            return self.PAC_PIECE_VALUES[2]
        elif chess.Board.piece_type_at(thisBoard, square) == chess.ROOK:
            return self.PAC_PIECE_VALUES[3]
        elif chess.Board.piece_type_at(thisBoard, square) == chess.QUEEN:
            return self.PAC_PIECE_VALUES[4]
        elif chess.Board.piece_type_at(thisBoard, square) == chess.KING:
            return self.PAC_PIECE_VALUES[5]
        else:
            print("The square is empty.", square)
            return 0

class BrokenCloset(ChessBot):
    name = "brokencloset"
    description = """Tries to put its king as close as possible to his boyfriend: The enemy king."""
    creator = "ph03n1x"

    BC_DIST_CAP = 0 # Adjust this if the bot seems to prioritize getting to the enemy king *too* much.

    def turn(
            self: typing.Self,
            board: chess.Board
        ) -> chess.Move:

        # Uncomment this to see the board before every move.
        # print(board)
        # print()

        if board.ply() == 0:
            return chess.Move(chess.E2,chess.E4)
        elif board.ply() == 1:
            return chess.Move(chess.E7,chess.E5)
        
        board_copy = copy.deepcopy(board)
        moveDict = {}

        for move in board.legal_moves:
            board_copy.push(move) 
            moveDict[move] = self.rateDistFromKing(board_copy, board.turn)
            board_copy.pop()

        lowValMove = min(moveDict, key=moveDict.get)
        board_copy.push(lowValMove) 
        lowVal = self.rateDistFromKing(board_copy, board.turn)
        board_copy.pop()
        return random.choice([k for k, v in moveDict.items() if v == lowVal])

    # Functions for use in turn().

    def helper_numToSquare(self, boardNum): # Must input an integer.
        if boardNum < 0 or boardNum >= 64:
            print("Illegal input made.")
            return None       
        return [(boardNum // 8)+1,boardNum % 8+1]
    
    def helper_squareToNum(self, boardNum): # Must input a list.
        if type(boardNum) != list:
            print("Illegal input made.")
            return None       
        return (boardNum[0]-1)*8+(boardNum[1]-1)

    def rateDistFromKing(self, thisBoard, color):
        # For now, all pieces' distance from the king will be judged.
        # It should be fairly easy to adjust this so that a piece type is ignored later.

        thisBoard.turn = color
        if thisBoard.king(thisBoard.turn) == None or thisBoard.king(not thisBoard.turn) == None:
            print("A king is missing.")
            return 0
        pieceDist = math.dist(self.helper_numToSquare(thisBoard.king(thisBoard.turn)),self.helper_numToSquare(thisBoard.king(not thisBoard.turn)))
        if pieceDist < (self.BC_DIST_CAP): # Replace 13**0.5 with the highest distance you want to matter.
            return self.BC_DIST_CAP
        else:
            return pieceDist

class RandomCheckmate(ChessBot):
    name = "random_checkmate"
    description = """The same as `random`, but if it has mate in 1 it will take it."""
    creator = "Duck"

    def turn(
            self: typing.Self,
            board: chess.Board
        ) -> chess.Move:
        board_copy = copy.deepcopy(board)

        for move in board_copy.legal_moves:
            board_copy.push(move)
            if board_copy.is_checkmate():
                board_copy.pop()
                return move
            board_copy.pop()
        
        # Regular Random.
            
        all_pieces = []

        for piece in chess.PIECE_TYPES:
            pieces = board.pieces(piece, board.turn)

            for tile in pieces:
                all_pieces.append(tile)
        
        for _ in all_pieces:
            chosen_tile = random.choice(all_pieces)
                
            all_moves = board.legal_moves

            possible_moves = []
            for move in all_moves:
                if move.from_square == chosen_tile:
                    possible_moves.append(move)
            
            if len(possible_moves) == 0:
                continue
            
            return random.choice(possible_moves)
        
        # Failsafe, this should never happen, and it might not even help.
        return random.choice(list(board.legal_moves))


#######################################################################################################################
##### BOT INTERACTION #################################################################################################
#######################################################################################################################

def get_bot(name: str) -> typing.Type[ChessBot] | None:
    """Attempts to get a Chess bot by name.

    Args:
        name (str): The name to try and find.

    Returns:
        typing.Type[ChessBot] | None: The found bot class, or None if nothing was found.
    """
    if name is None:
        return None
    
    for func in globals().values():
        try:
            if func == ChessBot:
                continue

            if issubclass(func, ChessBot):
                if func.name.lower() == name.lower():
                    return func
        except TypeError:
            continue
    
    return None

def get_bot_list() -> dict[str, typing.Type[ChessBot]]:
    """Returns a dict of bot names as keys, and the bot class as the value."""
    out = {}

    for func in globals().values():
        try:
            if func == ChessBot:
                continue
            
            if issubclass(func, ChessBot):
                out[func.name] = func
        except TypeError:
            continue
    
    return out

def run_match(
        white: ChessBot,
        black: ChessBot
    ) -> dict:
    """Runs a Chess match between the given bots, and returns the data."""
    board = chess.Board()

    white_data = {}
    black_data = {}

    white_obj = white(white_data) # type: ChessBot
    black_obj = black(black_data) # type: ChessBot

    moves = []
    
    move_number = 1
    while board.outcome() is None:

        if board.turn == chess.WHITE:
            white_obj.load(white_data)
            
            move = white_obj.turn(board)

            white_data = white_obj.save()
        else:
            black_obj.load(black_data)
            
            move = black_obj.turn(board)

            black_data = black_obj.save()
        
        moves.append(board.san(move))
        board.push(move)
        move_number += 1
    
    return {
        "winner": board.outcome().winner,
        "pgn": f"""[White "[Bot] {white_obj.name}"]\n[Black "[Bot] {black_obj.name}"]\n[Result "{board.outcome().result()}"]\n\n{convert_move_stack(moves)}{board.outcome().result()}""",
        "fen": board.fen()
    }

class ChessBotConverter(commands.Converter):
    """Converter that can be used in a command to automatically convert an argument to a Chess bot."""
    async def convert(self, ctx, arg: str) -> type[ChessBot]:
        converted = get_bot(arg)

        if not converted:
            raise commands.errors.BadArgument
        
        return converted


#######################################################################################################################
##### DATABASE INTERACTION ############################################################################################
#######################################################################################################################

def get_game(
        database: u_files.DatabaseInterface,
        channel: discord.TextChannel | int | str
    ) -> dict | None:
    """Fetches the information regarding a Chess game from the database.

    Args:
        database (u_files.DatabaseInterface): The database object.
        channel (discord.TextChannel | int | str): The channel to get the game for.

    Returns:
        dict | None: The game information, or None if no game exists.
    """
    channel = u_interface.get_channel_id(channel)

    # Hierarchy: 'chess', 'games', <channel id>
    return database.load("chess", "games", channel, default=None)

def update_game(
        database: u_files.DatabaseInterface,
        channel: discord.TextChannel | int | str,
        data: dict
    ) -> None:
    """Updates the data for a Chess game in the database.

    Args:
        database (u_files.DatabaseInterface): The database object.
        channel (discord.TextChannel | int | str): The channel the game is in.
        data (dict): The new data.
    """
    channel = u_interface.get_channel_id(channel)

    database.save("chess", "games", channel, data=data)

#######################################################################################################################
##### RENDERING #######################################################################################################
#######################################################################################################################

def render_board(
        board: chess.Board,
        path: str = "images/generated/chess_position.png",
        flipped: bool = False
    ) -> str:
    """Renders a chess.Board object into an image and returns the file path.

    Args:
        board (chess.Board): The board object.
        path (str): The path to save the file to.

    Returns:
        str: The file path.
    """

    last_move = None

    if len(board.move_stack) > 0:
        last_move = board.move_stack[-1]

    board_svg = chess.svg.board(board, lastmove=last_move, flipped=flipped)

    cairosvg.svg2png(bytestring=board_svg, write_to=path)
    
    return path

def render_data(data: dict) -> str:
    """Renders the board of the given game dictionary."""
    board = get_board_from_dict(data)

    flipped = False
    if data["player_side"] == "black":
        flipped = True

    return render_board(board, flipped=flipped)

#######################################################################################################################
##### MISC. UTILITY FUNCTIONS #########################################################################################
#######################################################################################################################

def make_game(
        initial_player: discord.Member,
        player_side: str,
        bot: typing.Type[ChessBot],
        starting_fen: str
    ) -> dict:
    """Returns a dictionary for the starting information about a game.

    Args:
        initial_player (discord.Member): The player.
        bot (typing.Type[ChessBot]): The Chess bot class.
        starting_fen (str): The starting fen string.

    Returns:
        dict: The game dictionary.
    """
    return {
        "players": [initial_player.id],
        "bot_name": bot.name,
        "bot_data": {},
        "starting_fen": starting_fen,
        "moves": [],
        "last_move": int(time.time()),
        "player_side": player_side
    }


def convert_move_stack(move_stack: list[str]) -> str:
    """Converts a list of strings into PGN format."""
    output = ""
    for move_num, move in enumerate(move_stack):
        if ((move_num) % 2 == 0):
            output += str(int(move_num/2)+1) + ". "
        output += move + " "
    return output

def get_board_from_dict(data: dict) -> chess.Board:
    """Converts a game dictionary to a `chess.Board` object."""
    pgn = io.StringIO("[Variant \"From Position\"]\n[FEN \"{fen_string}\"]\n\n{moves}".format(
        fen_string = data["starting_fen"],    
        moves = convert_move_stack(data["moves"])
    ))
    game = chess.pgn.read_game(pgn)

    board = game.headers.board()

    if game is not None:
        for move in game.mainline_moves():
            board.push(move)
    
    return board

def get_board_from_pgn(pgn: str) -> chess.Board:
    """Converts a pgn to a `chess.Board` object."""
    pgn = io.StringIO(pgn)
    game = chess.pgn.read_game(pgn)

    board = game.headers.board()

    if game is not None:
        for move in game.mainline_moves():
            board.push(move)

    return board

def get_pgn(
        guild: discord.Guild,
        data: dict
    ) -> str:
    """Converts a game dictionary to a pgn string."""
    members = u_interface.get_members(guild, data["players"])
    members = u_interface.member_display_names(members)

    if data["player_side"] == "white":
        player_white = ", ".join(members)
        player_black = f"[Bot] {data['bot_name']}"
    else:
        player_white = f"[Bot] {data['bot_name']}"
        player_black = ", ".join(members)

    pgn = io.StringIO("[Variant \"From Position\"]\n[FEN \"{fen_string}\"]\n\n{moves}".format(
        fen_string = data["starting_fen"],    
        moves = convert_move_stack(data["moves"])
    ))

    game = chess.pgn.read_game(pgn)
    board = get_board_from_dict(data)

    if game is None:
        return f"White: {player_white}\nBlack: {player_black}"

    game.headers["Event"] = guild.name
    del game.headers["Site"]
    del game.headers["Round"]

    if data["starting_fen"] == chess.STARTING_FEN:
        del game.headers["Variant"]
        del game.headers["FEN"]

    # Date
    game.headers["Date"] = get_date()

    game.headers["White"] = player_white
    game.headers["Black"] = player_black

    outcome = board.outcome()
    if outcome is None:
        del game.headers["Result"]
    else:
        game.headers["Result"] = outcome.result()

    
    return str(game)

def get_date() -> str:
    """Returns the current date in the format used in PGN strings."""
    timezone = pytz.timezone("US/Pacific")
    timestamp = timezone.localize(datetime.datetime.now())

    return f"{timestamp.year}.{timestamp.month}.{timestamp.day}"


#######################################################################################################################
##### ELO FUNCTIONS ###################################################################################################
#######################################################################################################################

def elo_probability(
        player_1: int,
        player_2: int
    ) -> float:
    """The estimated probability that player 1 will win with the elo rating system.
    
    Args:
        player_1 (int): The rating of player 1.
        player_2 (int): The rating of player 2."""
    return 1.0 / (1 + math.pow(10, (player_1 - player_2) / 400))

def new_elo_ratings(
        rating_1: int,
        rating_2: int,
        outcome: int
    ) -> tuple[int, int]:
    """Calculates new elo ratings for the two given input ratings.

    Args:
        rating_1 (int): The rating of the first player.
        rating_2 (int): The rating of the second player.
        outcome (int): The outcome, 1 for the first player winning, 2 of the second and 3 for a draw.

    Returns:
        tuple[int, int]: The new ratings of players 1 and 2 respectively.
    """
    probability_a = elo_probability(rating_2, rating_1)
    probability_b = elo_probability(rating_1, rating_2)
 
    if (outcome == 1):
        new_1 = rating_1 + 30 * (1 - probability_a)
        new_2 = rating_2 + 30 * (0 - probability_b)
    elif outcome == 2:
        new_1 = rating_1 + 30 * (0 - probability_a)
        new_2 = rating_2 + 30 * (1 - probability_b)
    else:
        new_1 = rating_1 + 30 * (0.5 - probability_a)
        new_2 = rating_2 + 30 * (0.5 - probability_b)

    return new_1, new_2

def get_bot_elo(
        database: u_files.DatabaseInterface,
        bot: str | ChessBot
    ) -> int:
    """Gets a bot's elo from the database.

    Args:
        database (u_files.DatabaseInterface): The database.
        bot (str | ChessBot): The name or object of the bot.

    Returns:
        int: The bot's elo.
    """
    try:
        bot = bot.name
    except AttributeError:
        pass

    data = database.load("chess", "bot_ratings", default = {})

    return data.get(bot, 800.0)

def set_bot_elo(
        database: u_files.DatabaseInterface,
        bot: str | ChessBot,
        new_rating: int
    ) -> None:
    """Updates a bot's elo in the database.

    Args:
        database (u_files.DatabaseInterface): The databse.
        bot (str | ChessBot): The name of object of the bot to update.
        new_rating (int): The new rating.
    """
    try:
        bot = bot.name
    except AttributeError:
        pass

    data = database.load("chess", "bot_ratings", default = {})

    data[bot] = new_rating

    database.save("chess", "bot_ratings", data=data)

def handle_match_outcome(
        database: u_files.DatabaseInterface,
        bot_1: str | ChessBot,
        bot_2: str | ChessBot,
        outcome: int
    ) -> tuple[int, int]:
    """Handles the elo changes of two bots after a match.

    Args:
        database (u_files.DatabaseInterface): The database.
        bot_1 (str | ChessBot): The name or object of bot 1.
        bot_2 (str | ChessBot): The name or object of bot 2.
        outcome (int): The outcome of the match. 1 if bot 1 won, 2 if bot 2 won, 3 if it was a draw.

    Returns:
        tuple[int, int]: The new elo ratings of bots 1 and 2 respectively.
    """
    current_1 = get_bot_elo(database, bot_1)
    current_2 = get_bot_elo(database, bot_2)

    new_1, new_2 = new_elo_ratings(
        rating_1 = current_1,
        rating_2 = current_2,
        outcome = outcome
    )

    set_bot_elo(database, bot_1, new_1)
    set_bot_elo(database, bot_2, new_2)

    return new_1, new_2