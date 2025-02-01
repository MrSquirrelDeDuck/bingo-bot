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
import numpy as np

# pip install chess
import chess
import chess.pgn
import chess.svg

# pip install CairoSVG
import cairosvg

import utility.files as u_files
import utility.interface as u_interface
import utility.text as u_text

all_games = open(os.path.join("data", "chess_games.txt"), "r") # Sourced from https://github.com/SebLague/Chess-Coding-Adventure/blob/Chess-V1-Unity/Assets/Book/Games.txt
game_lines = all_games.readlines()

class ChessBot:
    name = "generic_bot"
    description = """Generic Chess bot."""
    creator = "Duck"
    color = 0x000000

    def __init__(
            self: typing.Self,
            database_data: dict
        ) -> None:
        self.load(database_data)
    
    # Not needed for subclasses, this one is fine.
    @classmethod
    def get_color_rgb(cls: typing.Callable) -> tuple[int, int, int]:
        h = cls.color
        return (h >> 16, h >> 8 & 255, h & 255)

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
    color = 0x2eccb7

    def turn(
            self: typing.Self,
            board: chess.Board
        ) -> chess.Move:
        return random.choice(list(board.legal_moves))

class RandomBot(ChessBot):
    name = "random"
    description = """Chooses a random piece, and then from there a random move that piece can make.\nThis means each piece has an equal chance of being moved.\nFor a bot that chooses a random move from a giant list of all the possible moves `random_simple` is what you're looking for."""
    creator = "Duck"
    color = 0x2ecc68

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
    color = 0x1e4b70

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
    color = 0x314159

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
    color = 0x271828

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
    color = 0x628318

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
    color = 0xde2810

    CCP_DIST_CAP = 5**0.5 # Adjust this to ensure pieces don't get TOO close.
    CCP_PIECE_VALUES = [1,3,3,9,5,5]
    CCP_FORCED_EP = True
    # CCP_PIECE_VALUES = [1,3,3,10,0.25,5]

    def turn(
            self: typing.Self,
            board: chess.Board
        ) -> chess.Move:

        # Uncomment this to see the board before every move.
        # print(board)
        # print()

        # This bot has the following priorities:
        # Priority 1: Checkmate
        # Priority 2: Deliver a check
        # Priority 3: Capture a piece
        # Priority 4: Push a piece closer to the king.

        # First, classify all the moves, and while doing so:
        # Step 1: If you find a checkmate, play it immediately.

        if board.has_legal_en_passant() and self.CCP_FORCED_EP:
            for move in board.legal_moves:
                if chess.Board.is_en_passant(board, move):
                    return move

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
            if board.is_capture(move): # If it is not check, check if it is a capture.
                cap_moves.append(move) # Note any captures.            

        # Step 2: If no mate exists, Check the king

        # Step 3: ...and if that can't happen, Capture a piece

        if len(cap_moves) != 0:
            return random.choice(cap_moves)
        
        if len(check_moves) != 0:
            return random.choice(check_moves)

        # Step 4: ...and if that can't happen, Push a piece closer to the enemy king.

        # All potential future boards will be assigned a "rating" value for average
        # distance from the enemy1 king with dist(). Lower is better.
        
        # return random.choice(list(board.legal_moves))

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
            # if piece == chess.KING:
                # continue
            listPieces = list(thisBoard.pieces(piece, thisBoard.turn))
            for item in listPieces:
                rawDist = math.dist(self.helper_numToSquare(item),self.helper_numToSquare(thisBoard.king(not thisBoard.turn)))
                if rawDist <= self.CCP_DIST_CAP:
                    sumDist += (self.CCP_DIST_CAP) * self.getPieceValue(thisBoard, item)
                else:
                    sumDist += rawDist * self.getPieceValue(thisBoard, item)
                totalPieces += 1 * self.getPieceValue(thisBoard, item)
        if totalPieces == 0:
            # Should only fire if the king is the only piece.
            return 0
        return sumDist/totalPieces
    
    def getPieceValue(self, thisBoard, square):
        if chess.Board.piece_type_at(thisBoard, square) == chess.PAWN:
            return self.CCP_PIECE_VALUES[0]
        elif chess.Board.piece_type_at(thisBoard, square) == chess.KNIGHT:
            return self.CCP_PIECE_VALUES[1]
        elif chess.Board.piece_type_at(thisBoard, square) == chess.BISHOP:
            return self.CCP_PIECE_VALUES[2]
        elif chess.Board.piece_type_at(thisBoard, square) == chess.ROOK:
            return self.CCP_PIECE_VALUES[3]
        elif chess.Board.piece_type_at(thisBoard, square) == chess.QUEEN:
            return self.CCP_PIECE_VALUES[4]
        elif chess.Board.piece_type_at(thisBoard, square) == chess.KING:
            return self.CCP_PIECE_VALUES[5]
        else:
            return 0

class PacifistBot(ChessBot):
    name = "pacifistbot"
    description = """With the power of friendship I shall win!"""
    creator = "ph03n1x"
    color = 0xdddddd

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
            # print("Illegal input made.")
            return None       
        return [(boardNum // 8)+1,boardNum % 8+1]
    
    def helper_squareToNum(self, boardNum): # Must input a list.
        if type(boardNum) != list:
            # print("Illegal input made.")
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
            # print("The square is empty.", square)
            return 0

class BrokenCloset(ChessBot):
    name = "brokencloset"
    description = """Tries to put its king as close as possible to his boyfriend: The enemy king."""
    creator = "ph03n1x"
    color = 0x078d70

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
            # print("Illegal input made.")
            return None       
        return [(boardNum // 8)+1,boardNum % 8+1]
    
    def helper_squareToNum(self, boardNum): # Must input a list.
        if type(boardNum) != list:
            # print("Illegal input made.")
            return None       
        return (boardNum[0]-1)*8+(boardNum[1]-1)

    def rateDistFromKing(self, thisBoard, color):
        # For now, all pieces' distance from the king will be judged.
        # It should be fairly easy to adjust this so that a piece type is ignored later.

        thisBoard.turn = color
        if thisBoard.king(thisBoard.turn) == None or thisBoard.king(not thisBoard.turn) == None:
            # print("A king is missing.")
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
    color = 0x43cc2e

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

class GiveawayBot(ChessBot):
    name = "giveaway"
    description = """This bot is convinced it's playing giveaway/antichess, and will attempt to abide by the variant's rules as best it can."""
    creator = "Duck"
    color = 0xd369ae

    def turn(
            self: typing.Self,
            board: chess.Board
        ) -> chess.Move:
        if board.ply() == 0:
            return chess.Move(chess.E2,chess.E3)
        elif board.ply() == 1:
            return chess.Move(chess.E7,chess.E6)

        move_data = {}

        for move in board.legal_moves:
            move_data[move] = self.rate_move(board, move, True)
        
        highest = move_data[max(move_data, key=move_data.get)]

        return random.choice([move for move, value in move_data.items() if value == highest])

    
    def rate_move(
            self: typing.Self,
            board: chess.Board,
            move: chess.Move,
            search: bool = True
        ) -> int:
        if board.is_capture(move):
            return 3
        
        if search:
            board.push(move)

            for search in board.legal_moves:
                ranking = self.rate_move(board, search, False)

                if ranking == 3:
                    board.pop()

                    return 2
            
            board.pop()

        rank = move.to_square // 8 + 1

        if board.turn:
            # White.
            return rank / 8 + 1
        else:
            # Black.
            return (8 - rank) / 8 + 1

class NyaaBot(ChessBot):
    name = "nyaabot"
    description = """Basic chess skills. Nyaaaaa ^w^"""
    creator = "ph03n1x"
    color = 0xacfffc

    PHO_DIST_CAP = 10**0.5 # If a piece is at least this close to the king, cap the reward gain.
    PHO_FORCED_EP = True # Take en passant if possible.
    PHO_BEST_BY_TEST = True # Premove e4/e5.
    PHO_PIECE_VALUES = [1,3,3,5,9,3] # For use in distance calc. P,N,B,R,Q,K

    def turn(
            self: typing.Self,
            board: chess.Board
        ) -> chess.Move:

        # Uncomment this to see the board before every move.
        # print(board)
        # print()



        if board.ply() == 0 and self.PHO_BEST_BY_TEST == True:
            return chess.Move(chess.E2,chess.E4)
        elif board.ply() == 1 and self.PHO_BEST_BY_TEST == True:
            return chess.Move(chess.E7,chess.E5)
        
        if board.has_legal_en_passant() and self.PHO_FORCED_EP:
            for move in board.legal_moves:
                if chess.Board.is_en_passant(board, move):
                    # print("HOLY HELL!")
                    return move

        check_moves = []
        cap_moves = []

        board_copy = copy.deepcopy(board)
        for move in board.legal_moves:
            if board.gives_check(move) and self.check_SanityCheck(board, move.to_square, move) == True: # Is it a sane check?
                check_moves.append(move) 
                board_copy.push(move) 
                if board_copy.is_checkmate(): # If it is mate, then play it now.
                    return move
                board_copy.pop()
            if board.is_capture(move) and self.capture_SanityCheck(board, move.from_square, move.to_square, move) == True: # If it is not check, check if it is a capture.
                cap_moves.append(move) # Note any captures.            

        # Step 2: If no mate exists, Check the king

        # if len(check_moves) != 0:
        #     return random.choice(check_moves)

        # Step 3: ...and if that can't happen, Capture a piece

        # if len(cap_moves) != 0:
        #     return random.choice(cap_moves)

        moveEvalDict = {}

        # Evaluation time!
        for move in board.legal_moves:
            moveEvalDict[move] = 0
            if move in check_moves:
                moveEvalDict[move] = moveEvalDict[move] + 0
            if move in cap_moves:
                moveEvalDict[move] = moveEvalDict[move] + self.getPieceValue(board, move.to_square)                
            moveEvalDict[move] = moveEvalDict[move] - self.ratePieceDistFromKing(board_copy, board.turn, move)
            moveEvalDict[move] = moveEvalDict[move] + self.attackVulnerableSquares(board_copy, board.turn, move)
            moveEvalDict[move] = moveEvalDict[move] + self.rateKingSafety(board_copy, board.turn, move)
            moveEvalDict[move] = moveEvalDict[move] + (self.pawnAdvancement(board_copy, board.turn, move))*0.5   
            moveEvalDict[move] = moveEvalDict[move] - self.checkYourselfDontWreckYourself(board_copy, board.turn, move)
            if self.move_Draws(board, move):
                moveEvalDict[move] = moveEvalDict[move] - 1000 # Must be stalemate or fivefold repetition.
            if self.move_blundersMate(board, move):
                moveEvalDict[move] = moveEvalDict[move] - 93258468905632490863452

        highValMove = max(moveEvalDict, key=moveEvalDict.get)
        board_copy.push(highValMove) 
        highVal = moveEvalDict.get(highValMove)
        board_copy.pop()
        if len([k for k, v in moveEvalDict.items() if v == highVal]) == 0:
            print("Oh shit!")

        # print(moveEvalDict)
        # print("Cap moves:", cap_moves)
        # print("Check moves:", check_moves)
        # print("The high val move is", highValMove, "with a value of", highVal)
        # print("Possible moves:", [k for k, v in moveEvalDict.items() if v == highVal])
        return random.choice([k for k, v in moveEvalDict.items() if v == highVal])
            


    # Functions for use in turn().

    def helper_numToSquare(self, boardNum: int): # Must input an integer.
        if boardNum < 0 or boardNum >= 64:
            # print("Illegal input made.")
            return None       
        return [(boardNum // 8)+1,boardNum % 8+1]
    
    def helper_squareToNum(self, boardNum: list): # Must input a list.
        if not isinstance(boardNum, list):
            # print("Illegal input made.")
            return None       
        return (boardNum[0]-1)*8+(boardNum[1]-1)

    def ratePieceDistFromKing(self, thisBoard, color, move):
        # For now, all pieces' distance from the king will be judged.
        # It should be fairly easy to adjust this so that a piece type is ignored later.
        chess.Board.push(thisBoard, move)
        thisBoard.turn = color # To fix whose turn it is
        sumDist = 0
        totalPieces = 0
        for piece in chess.PIECE_TYPES:
            listPieces = list(thisBoard.pieces(piece, thisBoard.turn))
            for item in listPieces:
                if chess.Board.piece_type_at(thisBoard, item) == chess.KING or chess.Board.piece_type_at(thisBoard, item) == chess.PAWN:
                    continue # The king should stay away from pieces. Pawns use a more complex system.
                pieceDist = math.dist(self.helper_numToSquare(item),self.helper_numToSquare(thisBoard.king(not thisBoard.turn)))
                # print("Distance of the", chess.square_name(item), chess.Board.piece_type_at(thisBoard, item), "is", pieceDist)
                if pieceDist < (self.PHO_DIST_CAP):
                    sumDist += (self.PHO_DIST_CAP) * self.getPieceValue(thisBoard, item)
                else:
                    sumDist += pieceDist * self.getPieceValue(thisBoard, item)
                totalPieces += 1 * self.getPieceValue(thisBoard, item)
        if totalPieces == 0:
            chess.Board.pop(thisBoard)           
            return 8
        chess.Board.pop(thisBoard)    
        # print(totalPieces)
        # print(sumDist)
        # print()
        return sumDist/totalPieces
    
    def rateKingSafety(self, thisBoard, color, move):
        chess.Board.push(thisBoard, move)
        thisBoard.turn = color # To fix whose turn it is
        sumDist = 0
        totalPieces = 0
        for piece in chess.PIECE_TYPES:
            listPieces = list(thisBoard.pieces(piece, not thisBoard.turn))
            for item in listPieces:
                if chess.Board.piece_type_at(thisBoard, item) == chess.KING or chess.Board.piece_type_at(thisBoard, item) == chess.PAWN:
                    continue # The king should stay away from pieces. Pawns use a more complex system.
                pieceDist = math.dist(self.helper_numToSquare(item),self.helper_numToSquare(thisBoard.king(thisBoard.turn)))
                # print("Distance of the", chess.square_name(item), chess.Board.piece_type_at(thisBoard, item), "is", pieceDist)
                if pieceDist < (self.PHO_DIST_CAP):
                    sumDist += (self.PHO_DIST_CAP) * self.getPieceValue(thisBoard, item)
                else:
                    sumDist += pieceDist * self.getPieceValue(thisBoard, item)
                totalPieces += 1 * self.getPieceValue(thisBoard, item)
        if totalPieces == 0:
            chess.Board.pop(thisBoard)           
            return 8
        chess.Board.pop(thisBoard)    
        # print(totalPieces)
        # print(sumDist)
        # print()
        return sumDist/totalPieces
    
    def pawnAdvancement(self, thisBoard, color, move):
        pushPoints = 0
        if move.promotion != None:
            if move.promotion != chess.QUEEN:
                return 0
            else:
                return 10.5
        chess.Board.push(thisBoard, move)
        thisBoard.turn = color # To fix whose turn it is
        listPieces = list(thisBoard.pieces(chess.PAWN, thisBoard.turn))
        for square in listPieces:
            if thisBoard.turn == chess.WHITE:
                promotionPoints = 0.05*(chess.square_rank(square)**1.5) # 0 to 0.73 points
                kingPenalty = -0.15*math.dist(self.helper_numToSquare(square),self.helper_numToSquare(thisBoard.king(not thisBoard.turn)))
            else: # it's black's move.
                promotionPoints = 0.05*((-chess.square_rank(square)+7)**1.5) # 0 to 0.73 points
                kingPenalty = -0.15*math.dist(self.helper_numToSquare(square),self.helper_numToSquare(thisBoard.king(not thisBoard.turn)))
            promotionPoints *= (-abs(chess.square_file(square)-3.5)+3.5)*0.25+0.5 # Encourage center pawn development
            pushPoints += promotionPoints + kingPenalty
        thisBoard.pop()
        return pushPoints           
    
    def attackVulnerableSquares(self, thisBoard, color, move):
        # print("Considering move", move)
        chess.Board.push(thisBoard, move)
        thisBoard.turn = color # To fix whose turn it is
        listAttacking = list(chess.Board.attacks(thisBoard, thisBoard.king(not thisBoard.turn)))
        listNumAttacking = []
        # print(listAttacking)
        for square in listAttacking:
            if len(chess.Board.attackers(thisBoard, not thisBoard.turn, square)) == 1: # Must only be the king then
                listNumAttacking.append(len(chess.Board.attackers(thisBoard, thisBoard.turn, square)))
                # print("There are", len(chess.Board.attackers(thisBoard, thisBoard.turn, square)), "attackers on square", square)
            else:
                listNumAttacking.append(0)
        thisBoard.pop()
        # print("There are", listNumAttacking, "attackers.")
        # print()
        if max(listNumAttacking) == 0:
            return 0
        elif max(listNumAttacking) == 1:
            return 0.25
        else:
            return (0.5 + max(listNumAttacking) * 0.25)
        
    def check_SanityCheck(self, thisBoard, square, move): # TODO: Convert this to inputting a move.
        # print("Checking if this move is sane:", move)
        if isinstance(square, list):
            opSquare = self.helper_squareToNum(square)
        elif isinstance(square, int):
            opSquare = square
        else:
            # print("Illegal square input.")
            return False
        if self.move_Draws(thisBoard, move):
            return False
        chess.Board.push(thisBoard, move)
        if not(self.pieceIsEndangered(thisBoard, not thisBoard.turn, opSquare)):
            chess.Board.pop(thisBoard)
            return True
        chess.Board.pop(thisBoard)
        if list(chess.Board.attackers(thisBoard, not thisBoard.turn, square)) == [(thisBoard.king(not thisBoard.turn))]:
            if len(chess.Board.attackers(thisBoard, thisBoard.turn, square)) > 1:
                # print(chess.Board.attackers(thisBoard, thisBoard.turn, square))
                return True
        # print("Nope")
        return False
    
    def checkYourselfDontWreckYourself(self, thisBoard, color, move):
        # print("Checking sanity of move", move)
        chess.Board.push(thisBoard, move)
        thisBoard.turn = color # To fix whose turn it is    
        penalty = 0
        for piece in chess.PIECE_TYPES:
            listPieces = list(thisBoard.pieces(piece, thisBoard.turn))
            for square in listPieces:
                if chess.Board.piece_type_at(thisBoard, square) == chess.KING:
                    continue
                else:
                    if self.pieceIsEndangered(thisBoard, thisBoard.turn, square):
                        # print("The piece at", chess.square_name(square), "is endangered.")
                        # For each attacker, perform sanity check.
                        # If at least one can sanely capture, administer penalty.
                        thisBoard.turn = not color
                        for i in chess.Board.attackers(thisBoard, not color, square):
                            if not(chess.Board.is_legal(thisBoard, chess.Move(i, square))):
                                # print(chess.Board.is_legal(thisBoard, chess.Move(i, square)))
                                # print(chess.Move(i, square), "is illegal.")
                                continue
                            # print("Attacker id", i, "trying to take on", square)
                            if self.capture_SanityCheck(thisBoard, i, square, chess.Move(i, square)) or self.move_Draws(thisBoard, chess.Move(i, square)):
                                # print("Penalty applied, as a piece from square name", i, "can take.")
                                penalty = penalty + 0.5 + self.getPieceValue(thisBoard, square)
                                break
                        thisBoard.turn = color
        chess.Board.pop(thisBoard)
        return penalty
    
    def capture_SanityCheck(self, thisBoard, fromSquare, toSquare, move): # TODO: Convert this to inputting a move.
        if isinstance(fromSquare, list):
            opFromSquare = self.helper_squareToNum(fromSquare)
        elif isinstance(fromSquare, int):
            opFromSquare = fromSquare
        else:
            # print("Illegal from square input.")
            return False
        if isinstance(toSquare, list):
            opToSquare = self.helper_squareToNum(toSquare)
        elif isinstance(toSquare, int):
            opToSquare = toSquare
        else:
            # print("Illegal to square input.")
            return False
        if self.move_Draws(thisBoard, move):
            # print("This move is stupid.")
            return False
        chess.Board.push(thisBoard, move)
        if not(self.pieceIsEndangered(thisBoard, not thisBoard.turn, opToSquare)): # TODO: ugh
            # print(opToSquare, "is safe.")
            chess.Board.pop(thisBoard)
            return True
        else:
            chess.Board.pop(thisBoard)
            if self.getPieceValue(thisBoard, opFromSquare) <= self.getPieceValue(thisBoard, opToSquare):
                # print("Attacked > Attacker")
                return True
            else:
                # print("Attacker > Attacked")
                return False
        
    def pieceIsEndangered(self, thisBoard, color, square):
        thisBoard.turn = color # To fix whose turn it is
        # print(square)
        # print(color)
        if not(chess.Board.is_attacked_by(thisBoard, not thisBoard.turn, square)):
            return False
        candidates = list(chess.Board.attackers(thisBoard, not thisBoard.turn, square))
        # print(candidates)
        for i in candidates:
            if chess.Board.is_pinned(thisBoard, not thisBoard.turn, i):
                thisBoard.turn = not color
                if not(chess.Board.is_legal(thisBoard, chess.Move(i, square))):
                    candidates.remove(i)
                thisBoard.turn = color
        if len(candidates) == 0:
            return False
        if candidates == [(thisBoard.king(not thisBoard.turn))]:
            # print("It's the king!")
            if len(chess.Board.attackers(thisBoard, thisBoard.turn, square)) > 0:
                return False
        # print(candidates)
        return True

    def getPieceValue(self, thisBoard, square):
        if chess.Board.piece_type_at(thisBoard, square) == chess.PAWN:
            return self.PHO_PIECE_VALUES[0]
        elif chess.Board.piece_type_at(thisBoard, square) == chess.KNIGHT:
            return self.PHO_PIECE_VALUES[1]
        elif chess.Board.piece_type_at(thisBoard, square) == chess.BISHOP:
            return self.PHO_PIECE_VALUES[2]
        elif chess.Board.piece_type_at(thisBoard, square) == chess.ROOK:
            return self.PHO_PIECE_VALUES[3]
        elif chess.Board.piece_type_at(thisBoard, square) == chess.QUEEN:
            return self.PHO_PIECE_VALUES[4]
        elif chess.Board.piece_type_at(thisBoard, square) == chess.KING:
            return self.PHO_PIECE_VALUES[5]
        else:
            return 0

    def move_Draws(self, thisBoard, move):
        board_copy_HFD = copy.deepcopy(thisBoard)
        chess.Board.push(board_copy_HFD, move)
        if chess.Board.outcome(board_copy_HFD, claim_draw=True) != None and chess.Board.is_checkmate(board_copy_HFD) == False:
            return True
        else:
            return False
        
    def move_blundersMate(self, thisBoard, move):
        board_copy_HFD = copy.deepcopy(thisBoard)
        chess.Board.push(board_copy_HFD, move)
        for i in board_copy_HFD.legal_moves:
            chess.Board.push(board_copy_HFD, i)
            if chess.Board.is_checkmate(board_copy_HFD):
                chess.Board.pop(board_copy_HFD)
                chess.Board.pop(board_copy_HFD)                
                return True
            chess.Board.pop(board_copy_HFD)
        return False

class RobertoBot(ChessBot):
	name = "roberto_bot"
	description = """A python version of my Roberto bot (https://github.com/lythd/RobertoChessBot) that placed 293/624 in Sebastians competition. Don't look at my code there please its genuinely embarassing."""
	creator = "Booby"

	HP = 1.2
	ATK = 4.0
	DEF = 1.0
	SPD = 0.4
	DEX = 0.3

	def turn(
			self: typing.Self,
			board: chess.Board,
			depth = 2
		) -> chess.Move:
		
		best_move = None
		best_value = -float('inf') if board.turn else float('inf')

		for move in board.legal_moves:
			board.push(move)
			board_value = self.search(board, depth, -float('inf'), float('inf'), not board.turn)
			board.pop()

			if board.turn and board_value > best_value:
				best_value = board_value
				best_move = move
			elif not board.turn and board_value < best_value:
				best_value = board_value
				best_move = move

		return best_move
		
		
	def evaluate_board(self, board):
		if board.is_checkmate():
			if board.turn:
				return -9999
			else:
				return 9999
		elif board.is_stalemate() or board.is_insufficient_material() or board.is_seventyfive_moves():
			return 0

		return self.base_eval(board, board.turn) + self.base_eval(board, not board.turn) # one would be negative from being black so we do want to add them here
		#material = sum([self.piece_value(piece) for piece in board.piece_map().values()])
		#return material

	#def piece_value(self, piece):
	#	values = {
	#	chess.PAWN: 100,
	#	chess.KNIGHT: 320,
	#	chess.BISHOP: 330,
	#	chess.ROOK: 500,
	#	chess.QUEEN: 900,
	#	chess.KING: 20000
	#	}
	#	return values[piece.piece_type] if piece.color == chess.WHITE else -values[piece.piece_type]

	def search(self, board, depth, alpha, beta, maximizing_player):
		if depth == 0 or board.is_game_over():
			return self.evaluate_board(board)

		legal_moves = list(board.legal_moves)
		
		if maximizing_player:
			max_eval = -float('inf')
			for move in legal_moves:
				board.push(move)
				eval = self.search(board, depth - 1, alpha, beta, False)
				board.pop()
				max_eval = max(max_eval, eval)
				alpha = max(alpha, eval)
				if beta <= alpha:
					break
			return max_eval
		else:
			min_eval = float('inf')
			for move in legal_moves:
				board.push(move)
				eval = self.search(board, depth - 1, alpha, beta, True)
				board.pop()
				min_eval = min(min_eval, eval)
				beta = min(beta, eval)
				if beta <= alpha:
					break
		return min_eval
	
	def base_eval(self, board, white):
		"""
		 * Eval Explained
		 * 
		 * Pretty much everyone is going to have the same minimax searching and stuff, so in order to win I need to focus on the
		 * eval. You can just do the trivial thing of using the known average material values, but that is kind of lame, and also
		 * just ignores a lot of things that can make positions better or worse. You can do what you did and have like tables of
		 * good squares and such. But I thought this skips the most obvious thing, why not just see how good the pieces are for
		 * myself? So yeah I'm not putting on any of my values for pieces, here we will just see how valuable they are. Also
		 * with some slight modifications I imagine this will let you calculate how good pieces are in a game which is cool.
		 * 
		 * Anyways so on to what I ended up doing. I calculated 5 stats, hp is the amount of pieces you have, honestly not really
		 * important I just thought it fit the theme and its short enough to add, attack is the amount of squares you attack
		 * (this includes squares you attack multiple times), defense is the amount of squares you defend, speed is the amount
		 * of squares you can move without capture to (useful for seeing squares you control, or have the potential to capture on),
		 * and finally dexterity is the amount of squares you could move to if there were no other pieces on the board (useful
		 * to see if it's a useful piece, and if it's in a useful spot).
		 * 
		 * Then I just did a bit of trial and error to find the best weights for combining them. And then well combined them.
		 * Also you will see when I use this function I calculate both black and white and subtract them. As a move might give you
		 * a good position but your opponent an even better one. And just a general note this isn't normalised, so the eval this
		 * gives is not directly comparable to a typical eval, I guess you'd have to take the average eval difference of a bunch
		 * of positions with and without a random pawn and use that to scale it.
		 *
		 * Yes I just copied this message I am not even gonna bother reading this message again.
		 * 
		"""
		
		boardturn = board.turn # not sure if it clones or not but just resetting just incase, and not sure if this even matters but idcccc i just want this to work
		board.turn = white
		
		hp = 0
		attack = 0
		defense = 0
		speed = 0
		dexterity = 0

		friendly_squares = board.occupied_co[white]
		#print("friendly_squares:", bin(friendly_squares)[2:])
		enemy_squares = board.occupied_co[not white]
		#print("enemy_squares:", bin(enemy_squares)[2:])

		pieces = {
			chess.PAWN: list(board.pieces(chess.PAWN, white)),
			chess.KNIGHT: list(board.pieces(chess.KNIGHT, white)),
			chess.BISHOP: list(board.pieces(chess.BISHOP, white)),
			chess.ROOK: list(board.pieces(chess.ROOK, white)),
			chess.QUEEN: list(board.pieces(chess.QUEEN, white)),
			chess.KING: list(board.pieces(chess.KING, white))[0]
		}


		hp = (len(pieces[chess.PAWN]) +
			  3 * len(pieces[chess.KNIGHT]) +
			  3 * len(pieces[chess.BISHOP]) +
			  5 * len(pieces[chess.ROOK]) +
			  9 * len(pieces[chess.QUEEN]))

		for square in pieces[chess.PAWN]:
			pawn_attacks = board.attacks(square)
			#print(f"pawn, attack: {bin(pawn_attacks & enemy_squares).count('1')}, defense: {bin(pawn_attacks & friendly_squares).count('1')}, speed: {bin(pawn_attacks & ~enemy_squares & ~friendly_squares).count('1')}, dexterity: {bin(pawn_attacks).count('1')}")
			attack += bin(pawn_attacks & enemy_squares).count('1')
			defense += bin(pawn_attacks & friendly_squares).count('1')
			speed += bin(pawn_attacks & ~enemy_squares & ~friendly_squares).count('1')
			dexterity += bin(pawn_attacks).count('1')

		for square in pieces[chess.KNIGHT]:
			knight_attacks = board.attacks(square)
			#print(f"knight, attack: {bin(knight_attacks & enemy_squares).count('1')}, defense: {bin(knight_attacks & friendly_squares).count('1')}, speed: {bin(knight_attacks & ~enemy_squares & ~friendly_squares).count('1')}, dexterity: {bin(knight_attacks).count('1')}")
			attack += bin(knight_attacks & enemy_squares).count('1')
			defense += bin(knight_attacks & friendly_squares).count('1')
			speed += bin(knight_attacks & ~enemy_squares & ~friendly_squares).count('1')
			dexterity += bin(knight_attacks).count('1')

		for square in pieces[chess.BISHOP]:
			bishop_attacks = board.attacks(square)
			#print(f"bishop, attack: {bin(bishop_attacks & enemy_squares).count('1')}, defense: {bin(bishop_attacks & friendly_squares).count('1')}, speed: {bin(bishop_attacks & ~enemy_squares & ~friendly_squares).count('1')}, dexterity: {bin(bishop_attacks).count('1')}")
			attack += bin(bishop_attacks & enemy_squares).count('1')
			defense += bin(bishop_attacks & friendly_squares).count('1')
			speed += bin(bishop_attacks & ~enemy_squares & ~friendly_squares).count('1')
			dexterity += bin(bishop_attacks).count('1')

		for square in pieces[chess.ROOK]:
			rook_attacks = board.attacks(square)
			#print(f"rook, attack: {bin(rook_attacks & enemy_squares).count('1')}, defense: {bin(rook_attacks & friendly_squares).count('1')}, speed: {bin(rook_attacks & ~enemy_squares & ~friendly_squares).count('1')}, dexterity: {bin(rook_attacks).count('1')}")
			attack += bin(rook_attacks & enemy_squares).count('1')
			defense += bin(rook_attacks & friendly_squares).count('1')
			speed += bin(rook_attacks & ~enemy_squares & ~friendly_squares).count('1')
			dexterity += bin(rook_attacks).count('1')

		for square in pieces[chess.QUEEN]:
			queen_attacks = board.attacks(square)
			#print(f"queen, attack: {bin(queen_attacks & enemy_squares).count('1')}, defense: {bin(queen_attacks & friendly_squares).count('1')}, speed: {bin(queen_attacks & ~enemy_squares & ~friendly_squares).count('1')}, dexterity: {bin(queen_attacks).count('1')}")
			attack += bin(queen_attacks & enemy_squares).count('1')
			defense += bin(queen_attacks & friendly_squares).count('1')
			speed += bin(queen_attacks & ~enemy_squares & ~friendly_squares).count('1')
			dexterity += bin(queen_attacks).count('1')

		king_square = pieces[chess.KING]
		king_attacks = board.attacks(king_square)
		#print(f"king, attack: {bin(king_attacks & enemy_squares).count('1')}, defense: {bin(king_attacks & friendly_squares).count('1')}, speed: {bin(king_attacks & ~enemy_squares & ~friendly_squares).count('1')}, dexterity: {bin(king_attacks).count('1')}")
		attack += bin(king_attacks & enemy_squares).count('1')
		defense += bin(king_attacks & friendly_squares).count('1')
		speed += bin(king_attacks & ~enemy_squares & ~friendly_squares).count('1')
		dexterity += bin(king_attacks).count('1')

		eval_score = (hp * RobertoBot.HP +
					  attack * RobertoBot.ATK +
					  defense * RobertoBot.DEF +
					  speed * RobertoBot.SPD +
					  dexterity * RobertoBot.DEX)

		#print(f"hp: {hp*RobertoBot.HP}, attack: {attack*RobertoBot.ATK}, defense: {defense*RobertoBot.DEF}, speed: {speed*RobertoBot.SPD}, dexterity: {dexterity*RobertoBot.DEX}")

		if board.fullmove_number < 5:
			eval_score *= random.uniform(0.95, 1.05)  # for opening spice

		board.turn = boardturn

		return eval_score * (1.0 if white else -1.0)

class OwObot_v1(ChessBot):
    name = "owobot_v1"
    description = """Duck's failed attempt at dethroning NyaaBot, but the first version."""
    creator = "Duck"
    color = 0xee362e

    PIECE_VALUE = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 3
    }
    
    def get_attacks(
            self: typing.Self,
            board: chess.Board,
            square: chess.Square
        ) -> chess.Bitboard:
        """Returns a bitboard for the squares that the piece on the given square attacks."""
        return int(board.attacks(square))
    
    def get_attacks_filtered(
            self: typing.Self,
            board: chess.Board,
            color: chess.Color,
            square: chess.Square
        ) -> chess.Bitboard:
        attacks = self.get_attacks(board, square)

        return attacks - (attacks & self.get_all_pieces(board, color))
    
    def get_defense(
            self: typing.Self,
            board: chess.Board,
            color: chess.Color,
            square: chess.Square
        ) -> chess.Bitboard:
        attacks = self.get_attacks(board, square)

        return attacks & self.get_all_pieces(board, color)
    
    def get_defended_squares(
            self: typing.Self,
            board: chess.Board,
            color: chess.Color
        ) -> chess.Bitboard:
        total = chess.BB_EMPTY

        for square in board.piece_map(mask=self.get_all_pieces(board, color)):
            total |= self.get_defense(board, color, square)
        
        return total
    
    def get_attacked_squares(
            self: typing.Self,
            board: chess.Board,
            color: chess.Color
        ) -> chess.Bitboard:
        total = chess.BB_EMPTY

        for square in board.piece_map(mask=self.get_all_pieces(board, color)):
            total |= self.get_attacks(board, square)
        
        return total
    
    def get_all_pieces(
            self: typing.Self,
            board: chess.Board,
            color: chess.Color
        ) -> chess.Bitboard:
        return board.occupied_co[color]

    def get_undefended_pieces(
            self: typing.Self,
            board: chess.Board,
            color: chess.Color
        ) -> chess.Bitboard:
        return self.get_all_pieces(board, color) - self.get_defended_squares(board, color)


    def turn(
            self: typing.Self,
            board: chess.Board
        ) -> chess.Move:
        self.side = board.turn

        move_rankings = {}

        for move in board.legal_moves:
            score = 0

            if self.move_blunders_piece(board, move):
                score -= 10

            move_rankings[move] = score
        
        move = self.get_move(move_rankings)

        return move
    
    def get_move(
            self: typing.Self,
            rankings: dict[chess.Move, float]
        ) -> chess.Move:
        highest_score = max(rankings.values())

        try:
            return random.choice([m for m, v in rankings.items() if v == highest_score])
        except:
            return max(rankings, key=rankings.get)
    
    ##### RANKING CRITERIA #####
    
    def move_blunders_piece(
            self: typing.Self,
            board: chess.Board,
            move: chess.Move
        ) -> bool:
        board.push(move)

        undefended_pieces = self.get_undefended_pieces(board, self.side)
        attacked = self.get_attacked_squares(board, not self.side)

        attacked_pieces = undefended_pieces & attacked

        board.pop()

        return attacked_pieces > 0

class OwObot_v2(ChessBot):
    name = "owobot_v2"
    description = """Duck's failed attempt at dethroning NyaaBot, but the second version."""
    creator = "Duck"
    color = 0xb200ff

    PIECE_VALUE = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 3
    }
    
    def get_attacks(
            self: typing.Self,
            board: chess.Board,
            square: chess.Square
        ) -> chess.Bitboard:
        """Returns a bitboard for the squares that the piece on the given square attacks."""
        return int(board.attacks(square))
    
    def get_attacks_filtered(
            self: typing.Self,
            board: chess.Board,
            color: chess.Color,
            square: chess.Square
        ) -> chess.Bitboard:
        attacks = self.get_attacks(board, square)

        return attacks - (attacks & self.get_all_pieces(board, color))
    
    def get_defense(
            self: typing.Self,
            board: chess.Board,
            color: chess.Color,
            square: chess.Square
        ) -> chess.Bitboard:
        attacks = self.get_attacks(board, square)

        return attacks & self.get_all_pieces(board, color)
    
    def get_defended_squares(
            self: typing.Self,
            board: chess.Board,
            color: chess.Color
        ) -> chess.Bitboard:
        total = chess.BB_EMPTY

        for square in board.piece_map(mask=self.get_all_pieces(board, color)):
            total |= self.get_defense(board, color, square)
        
        return total
    
    def get_attacked_squares(
            self: typing.Self,
            board: chess.Board,
            color: chess.Color
        ) -> chess.Bitboard:
        total = chess.BB_EMPTY

        for square in board.piece_map(mask=self.get_all_pieces(board, color)):
            total |= self.get_attacks(board, square)
        
        return total
    
    def get_all_pieces(
            self: typing.Self,
            board: chess.Board,
            color: chess.Color
        ) -> chess.Bitboard:
        return board.occupied_co[color]

    def get_undefended_pieces(
            self: typing.Self,
            board: chess.Board,
            color: chess.Color
        ) -> chess.Bitboard:
        return self.get_all_pieces(board, color) - self.get_defended_squares(board, color)


    def turn(
            self: typing.Self,
            board: chess.Board
        ) -> chess.Move:
        self.side = board.turn

        move_rankings = {}

        for move in board.legal_moves:
            score = 0

            ################################
            # Check for checks.
            if board.gives_check(move):
                score += 1

                # Check if it's checkmate...
                board.push(move)
                if board.is_checkmate():
                    board.pop()
                    return move
                board.pop()

            ################################
            # Check for captures.
            if board.is_capture(move):
                score += 1

            ################################
            # Check for piece blunders.
            if self.move_blunders_piece(board, move):
                score -= 10

            move_rankings[move] = score
        
        initial_move = self.get_move(move_rankings)
        move = initial_move

        while True:
            board.push(move)
            if self.final_check(board, move):
                board.pop()
                break
            board.pop()
            
            move_rankings.pop(move)

            if len(move_rankings) == 0:
                return initial_move
            
            move = self.get_move(move_rankings)

        return move
    
    def get_move(
            self: typing.Self,
            rankings: dict[chess.Move, float]
        ) -> chess.Move:
        highest_score = max(rankings.values())

        try:
            return random.choice([m for m, v in rankings.items() if v == highest_score])
        except:
            return max(rankings, key=rankings.get)
    
    ##### RANKING CRITERIA #####

    def final_check(
            self: typing.Self,
            board: chess.Board,
            move: chess.Move
        ) -> bool:

        for opponent_move in board.legal_moves:
            if board.gives_check(opponent_move):
                board.push(opponent_move)
                if board.is_checkmate():
                    board.pop()
                    return False
                board.pop()
        
        if board.outcome(claim_draw=True) and not board.is_checkmate():
            return False

        return True
    
    def move_blunders_piece(
            self: typing.Self,
            board: chess.Board,
            move: chess.Move
        ) -> bool:
        board.push(move)

        undefended_pieces = self.get_undefended_pieces(board, self.side)
        attacked = self.get_attacked_squares(board, not self.side)

        attacked_pieces = undefended_pieces & attacked

        board.pop()

        return attacked_pieces > 0

class OwObot_v3(ChessBot):
    name = "owobot_v3"
    description = """Duck's failed attempt at dethroning NyaaBot, but the third version."""
    creator = "Duck"
    color = 0x0a6564

    PIECE_VALUE = {
        chess.KING: 3,
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3.2,
        chess.ROOK: 5,
        chess.QUEEN: 9
    }
    PIECE_VALUE_ITEMS = list(PIECE_VALUE.items())

    # King move rankings.

    KING_MOVE_RANKINGS_START = {
        0: -1,
        1: 1,
        2: 0.5,
        3: 0,
        4: -0.25,
        5: -0.5,
        6: -0.5,
        7: -0.5,
        8: -0.5,
        9: -0.5
    }

    KING_MOVE_RANKINGS_END = {
        0: -4,
        1: -3,
        2: -2,
        3: -1,
        4: 0,
        5: 1,
        6: 2,
        7: 3,
        8: 4,
        9: 5
    }

    # Piece tables.

    PIECE_TABLE_PAWN_START = list(reversed([
        0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5,  5, 10, 25, 25, 10,  5,  5,
        0,  0,  0, 20, 20,  0,  0,  0,
        5, -5,-10,  0,  0,-10, -5,  5,
        5, 10, 10,-20,-20, 10, 10,  5,
        0,  0,  0,  0,  0,  0,  0,  0
    ]))

    PIECE_TABLE_PAWN_END = list(reversed([
        100, 100, 100, 100, 100, 100, 100, 100,
         75,  75,  75,  75,  75,  75,  75,  75,
         50,  50,  50,  50,  50,  50,  50,  50,
         25,  25,  25,  25,  25,  25,  25,  25,
         20,  20,  20,  20,  20,  20,  20,  20,
         10,  10,  10,  10,  10,  10,  10,  10,
          0,   0,   0,   0,   0,   0,   0,   0,
          0,   0,   0,   0,   0,   0,   0,   0
    ]))

    PIECE_TABLE_KNIGHT = list(reversed([
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50,
    ]))

    PIECE_TABLE_BISHOP = list(reversed([
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5, 10, 10,  5,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  5,  0,  0,  0,  0,  5,-10,
        -20,-10,-10,-10,-10,-10,-10,-20,
    ]))
    
    PIECE_TABLE_ROOK = list(reversed([
        0,  0,  0,  0,  0,  0,  0,  0,
        5, 10, 10, 10, 10, 10, 10,  5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        0,  0,  0,  5,  5,  0,  0,  0
    ]))

    PIECE_TABLE_QUEEN = list(reversed([
        -20,-10,-10, -5, -5,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5,  5,  5,  5,  0,-10,
        -5,  0,  5,  5,  5,  5,  0, -5,
        0,  0,  5,  5,  5,  5,  0, -5,
        -10,  5,  5,  5,  5,  5,  0,-10,
        -10,  0,  5,  0,  0,  0,  0,-10,
        -20,-10,-10, -5, -5,-10,-10,-20
    ]))

    PIECE_TABLE_KING_START =list(reversed([
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -10,-20,-20,-20,-20,-20,-20,-10,
        20, 20,  0,  0,  0,  0, 20, 20,
        20, 30, 10,  0,  0, 10, 30, 20
    ]))

    PIECE_TABLE_KING_END = list(reversed([
        -50,-40,-30,-20,-20,-30,-40,-50,
        -30,-20,-10,  0,  0,-10,-20,-30,
        -30,-10, 20, 30, 30, 20,-10,-30,
        -30,-10, 30, 40, 40, 30,-10,-30,
        -30,-10, 30, 40, 40, 30,-10,-30,
        -30,-10, 20, 30, 30, 20,-10,-30,
        -30,-30,  0,  0,  0,  0,-30,-30,
        -50,-30,-30,-30,-30,-30,-30,-50
    ]))

    # Utility methods.

    def iterate_through_bitboard(
            self: typing.Self,
            bitboard: chess.Bitboard
        ) -> typing.Generator[int, None, None]:
        while bitboard:
            b = bitboard & (~bitboard + 1)
            yield int(math.log2(b))
            bitboard ^= b
    
    def get_attacks(
            self: typing.Self,
            board: chess.Board,
            square: chess.Square
        ) -> chess.Bitboard:
        """Returns a bitboard for the squares that the piece on the given square attacks."""
        return int(board.attacks(square))
    
    def get_attacks_filtered(
            self: typing.Self,
            board: chess.Board,
            color: chess.Color,
            square: chess.Square
        ) -> chess.Bitboard:
        """Same as .get_attacks, but removes the tiles that the given color's pieces are on."""
        attacks = self.get_attacks(board, square)

        return attacks - (attacks & self.get_all_pieces(board, color))
    
    def get_defense(
            self: typing.Self,
            board: chess.Board,
            color: chess.Color,
            square: chess.Square
        ) -> chess.Bitboard:
        """Gives a bitboard of squares defended by the given square that the given color has a piece on."""
        attacks = self.get_attacks(board, square)

        return attacks & self.get_all_pieces(board, color)
    
    def get_defended_squares(
            self: typing.Self,
            board: chess.Board,
            color: chess.Color
        ) -> chess.Bitboard:
        """Gives a bitboard of every square the given color has a piece on which is defended."""
        total = chess.BB_EMPTY

        for square in board.piece_map(mask=self.get_all_pieces(board, color)):
            total |= self.get_defense(board, color, square)
        
        return total
    
    def get_attacked_squares(
            self: typing.Self,
            board: chess.Board,
            color: chess.Color
        ) -> chess.Bitboard:
        """Gives a bitboard of every square the given color attacks."""
        total = chess.BB_EMPTY

        for square in board.piece_map(mask=self.get_all_pieces(board, color)):
            total |= self.get_attacks(board, square)
        
        return total
    
    def get_attacked_squares_no_king(
            self: typing.Self,
            board: chess.Board,
            color: chess.Color
        ) -> chess.Bitboard:
        """Gives a bitboard of every square the given color attacks, not including the king."""
        total = chess.BB_EMPTY

        for square in board.piece_map(mask=self.get_all_pieces(board, color)):
            if board.piece_at(square).piece_type == chess.KING:
                continue

            total |= self.get_attacks(board, square)
        
        return total
    
    def get_squares_attacked_by_king(
            self: typing.Self,
            board: chess.Board,
            color: chess.Color
        ) -> chess.Bitboard:
        return self.get_attacks(board, board.king(color))
    
    def get_all_pieces(
            self: typing.Self,
            board: chess.Board,
            color: chess.Color
        ) -> chess.Bitboard:
        """Gives a bitboard of every square the given color occupies."""
        return board.occupied_co[color]

    def get_all_other_than_panws(
            self: typing.Self,
            board: chess.Board,
            color: chess.Color
        ) -> chess.Bitboard:
        """Same as get_all_pieces, but removes pawns."""
        return self.get_all_pieces(board, color) - board.pieces_mask(chess.PAWN, color)

    def get_undefended_pieces(
            self: typing.Self,
            board: chess.Board,
            color: chess.Color
        ) -> chess.Bitboard:
        """Gives a bitboard of every square that has a piece of the given color which that color does not defend."""
        return self.get_all_pieces(board, color) - self.get_defended_squares(board, color)

    def get_square_attackers(
            self: typing.Self,
            board: chess.Board,
            color: chess.Color,
            square: chess.Square
        ) -> chess.Bitboard:
        """Gives a bitboard of each square that the given color occupies that attacks the given square."""
        shift = 1 << square
        total = chess.BB_EMPTY

        for piece_square in board.piece_map(mask=self.get_all_pieces(board, color)):
            if shift & self.get_attacks(board, piece_square):
                total |= 1 << piece_square
        
        return total

    def get_attacked_pieces(
            self: typing.Self,
            board: chess.Board,
            color: chess.Color
        ) -> chess.Bitboard:
        """Gives a bitboard for every piece of the given color that is attacked by the opposing side."""
        return self.get_all_pieces(board, color) & self.get_attacked_squares(board, not color)
    
    def get_piece_value_from_square(
            self: typing.Self,
            board: chess.Board,
            square: chess.Square
        ) -> int:
        return self.PIECE_VALUE.get(board.piece_type_at(square), 0)

    def convert_square_index(
            self: typing.Self,
            square: chess.Square
        ) -> tuple[int, int]:
        return (square % 8, square // 8)

    def find_hanging_pieces(
            self: typing.Self,
            board: chess.Board,
            color: chess.Color
        ) -> chess.Bitboard:
        """Finds hanging pieces that `not color` has."""
        output = 0

        color_pieces = self.get_all_pieces(board, color)
        opposite_pieces = self.get_all_pieces(board, not color)

        for piece_square in self.iterate_through_bitboard(color_pieces):
            piece_value = self.get_piece_value_from_square(board, piece_square)

            attacks = self.get_attacks_filtered(board, color, piece_square)

            for attack_square in self.iterate_through_bitboard(attacks & opposite_pieces):
                attack_value = self.get_piece_value_from_square(board, attack_square)

                if attack_value > piece_value:
                    output |= 1 << attack_square
        
        return output
                

    ###################################################################################

    def turn(
            self: typing.Self,
            board: chess.Board
        ) -> chess.Move:
        self.side = board.turn


        move_rankings = {}

        for move in board.legal_moves:

            score = 0

            ################################
            # Check for checks.
            if board.gives_check(move):
                score += self.check_value(board, move)

                # Check if it's checkmate...
                board.push(move)
                if board.is_checkmate():
                    board.pop()
                    return move
                board.pop()

            ################################
            # Check for captures.
            if board.is_capture(move):
                score += self.capture_value(board, move)
            
            ################################
            # Check for piece blunders.
            if self.move_blunders_piece(board, move):
                score -= 10

            ################################
            # Check for piece hangs.
            score += self.move_hangs_any_piece(board, move) * -7.5
                
            ################################
            # Account for king safety.
            score += self.king_safety(board, move)

            ################################
            # Account for distance to enemy king.
            score += self.rate_distance(board, move)

            ################################
            # Account for the number of enemy king moves.
            score += self.enemy_king_moves(board, move)

            ################################
            # Account for the piece table scores.
            score += self.rank_ending_piece_location(board, move)

            ################################
            # Account for attacking vulnerable squares
            score += self.vulnerable_squares(board, move)

            ################################
            # Check for trapped pieces.
            score += self.check_trapped_pieces(board, move)

            move_rankings[move] = score
        
        initial_move = self.get_move(move_rankings)
        move = initial_move

        while not self.final_check(board, move, move_rankings.get(move)):            
            move_rankings.pop(move)

            # If the length of move_rankings is 0 that means that
            # every possible move fails the final check, which
            # means we're screwed. In that case, just return 
            # whatever was the first move chosen.
            if len(move_rankings) == 0:
                return initial_move
            
            move = self.get_move(move_rankings)

        return move
    
    def get_move(
            self: typing.Self,
            rankings: dict[chess.Move, float]
        ) -> chess.Move:
        highest_score = max(rankings.values())

        try:
            return random.choice([m for m, v in rankings.items() if v == highest_score])
        except:
            return max(rankings, key=rankings.get)
    
    ##### RANKING CRITERIA #####

    def final_check(
            self: typing.Self,
            board: chess.Board,
            move: chess.Move,
            ranking: float
        ) -> bool:
        """Final check, if the best move fails this it is thrown out."""
        board.push(move)

        for opponent_move in board.legal_moves:
            if board.gives_check(opponent_move):
                board.push(opponent_move)
                if board.is_checkmate():
                    board.pop()
                    board.pop()
                    return False
                board.pop()
        
        if board.outcome(claim_draw=True) and not board.is_checkmate():
            board.pop()
            return False
        
        board.pop()

        #########################

        return True
    
    def move_blunders_piece(
            self: typing.Self,
            board: chess.Board,
            move: chess.Move
        ) -> bool:
        """If any attacked piece is left undefended after the move is complete.
        This has the exception for if the move is a capture and the captured piece is of equal or higher value than what is doing the capturing."""
        if board.is_capture(move):
            if self.get_piece_value_from_square(board, move.from_square) <= self.get_piece_value_from_square(board, move.to_square):
                return False

        board.push(move)

        undefended_pieces = self.get_undefended_pieces(board, self.side)
        attacked = self.get_attacked_squares(board, not self.side)

        attacked_pieces = undefended_pieces & attacked

        board.pop()

        return attacked_pieces > 0
    
    def move_hangs_moved_piece(
            self: typing.Self,
            board: chess.Board,
            move: chess.Move
        ) -> bool:
        """If the piece being moved will be hanging after being moved."""

        board.push(move)

        attacks = self.get_square_attackers(board, board.turn, move.to_square)
        piece_value = self.get_piece_value_from_square(board, move.to_square)

        for piece_type, value in self.PIECE_VALUE_ITEMS:
            if value == piece_value:
                break

            mask = board.pieces_mask(piece_type, board.turn)

            if mask & attacks > 0:
                board.pop()
                return True

        board.pop()

        return False
    
    def move_hangs_any_piece(
            self: typing.Self,
            board: chess.Board,
            move: chess.Move
        ) -> bool:
        board.push(move)

        attacked_pieces = self.get_attacked_pieces(board, self.side)

        if attacked_pieces == 0:
            board.pop()
            return False
        
        hanging = self.find_hanging_pieces(board, not self.side)
        if hanging:
            board.pop()
            return hanging.bit_count() 
        
        # for hang_square in self.iterate_through_bitboard(attacked_pieces):
        #     # hang_square = int(math.log2(hang_square_raw))
        #     hang_value = self.get_piece_value_from_square(board, hang_square)

        #     attackers = self.get_square_attackers(board, not self.side, hang_square)
        #     for attack_square in self.iterate_through_bitboard(attackers):
        #         # attack_square = int(math.log2(attack_square_raw))
        #         attack_value = self.get_piece_value_from_square(board, attack_square)

        #         if attack_value < hang_value:
        #             board.pop()
        #             if board.fullmove_number == 47 and move.from_square == chess.C4:
        #                 # print(att)
        #                 print(board.san(move), hang_square, hang_value, attack_square, attack_value)
        #             return True
        
        board.pop()
        return False

    
    def capture_value(
            self: typing.Self,
            board: chess.Board,
            move: chess.Move
        ) -> float:
        """Assigns a score to a capture."""
        if board.is_capture(move):
            opponent_attackers = self.get_square_attackers(board, not self.side, move.to_square)
            defenders = self.get_square_attackers(board, self.side, move.to_square)
            
            captured_value = self.get_piece_value_from_square(board, move.to_square)
            capturing_value = self.get_piece_value_from_square(board, move.from_square)

            if captured_value > capturing_value:
                return (2 + max((captured_value - capturing_value), 0)) * 3
            elif capturing_value == captured_value:
                if opponent_attackers <= defenders:
                    return 2
                
            if opponent_attackers >= defenders:
                return -2

        return 1
    
    def rate_distance(
            self: typing.Self,
            board: chess.Board,
            move: chess.Move
        ) -> float:
        """Rates the updated distance to the enemy king."""
        board.push(move)
        king = board.king(not self.side)

        distance_sum = []

        for piece_type in chess.PIECE_TYPES:
            for square in board.pieces(piece_type, self.side):
                if board.piece_type_at(square) == chess.KING:
                    continue

                distance = math.dist(
                    self.convert_square_index(square),
                    self.convert_square_index(king)
                )
                distance_sum.append(distance)
        
        board.pop()

        if len(distance_sum) == 0:
            return -1
        
        return 10 - (sum(distance_sum) / len(distance_sum))
    
    def enemy_king_moves(
            self: typing.Self,
            board: chess.Board,
            move: chess.Move
        ) -> float:
        """Rates the number of moves the enemy king has."""
        board.push(move)
        king_mask = board.pieces_mask(chess.KING, not self.side)
        king_moves = len(list(board.generate_legal_moves(from_mask=king_mask)))

        remaining_pieces = (self.get_all_pieces(board, True) | self.get_all_pieces(board, False)).bit_count() - 2 # Subtract the 2 kings. Max is now 30.

        board.pop()
        ranking = max(min((25 - remaining_pieces), 25), 0) * ((9 - king_moves) / math.pi)

        return ranking

    
    def king_safety(
            self: typing.Self,
            board: chess.Board,
            move: chess.Move
        ) -> float:
        board.push(move)
        board.push(chess.Move.null())

        king_mask = board.pieces_mask(chess.KING, self.side)
        
        king_moves = len(list(board.generate_legal_moves(from_mask=king_mask)))

        rank_start = self.KING_MOVE_RANKINGS_START[king_moves]
        rank_end = self.KING_MOVE_RANKINGS_END[king_moves]

        remaining_pieces = (self.get_all_pieces(board, True) | self.get_all_pieces(board, False)).bit_count() - 2 # Subtract the 2 kings. Max is now 30.

        rank_start_apply = (remaining_pieces / 30) * rank_start
        rank_end_apply = ((30 - remaining_pieces) / 30) * rank_end

        ranking = rank_start_apply + rank_end_apply
    
        board.pop()
        board.pop()

        return ranking
    
    def rank_ending_piece_location(
            self: typing.Self,
            board: chess.Board,
            move: chess.Move
        ) -> float:
        piece = board.piece_at(move.from_square)

        score = 0

        if piece.piece_type == chess.PAWN:
            remaining_pieces = (self.get_all_other_than_panws(board, True) | self.get_all_other_than_panws(board, False)).bit_count() - 2 # Subtract the 2 kings. Max is now 14.

            score_start = (remaining_pieces / 14) * self.PIECE_TABLE_PAWN_START[move.to_square]
            score_end = ((14 - remaining_pieces) / 14) * self.PIECE_TABLE_PAWN_START[move.to_square]

            score = score_start + score_end
        elif piece.piece_type == chess.KING:
            remaining_pieces = (self.get_all_other_than_panws(board, True) | self.get_all_other_than_panws(board, False)).bit_count() - 2 # Subtract the 2 kings. Max is now 14.

            score_start = (remaining_pieces / 14) * self.PIECE_TABLE_KING_START[move.to_square]
            score_end = ((14 - remaining_pieces) / 14) * self.PIECE_TABLE_KING_START[move.to_square]

            score = score_start + score_end
        elif piece.piece_type == chess.BISHOP:
            score = self.PIECE_TABLE_BISHOP[move.to_square]
        elif piece.piece_type == chess.KNIGHT:
            score = self.PIECE_TABLE_KNIGHT[move.to_square]
        elif piece.piece_type == chess.ROOK:
            score = self.PIECE_TABLE_ROOK[move.to_square]
        elif piece.piece_type == chess.QUEEN:
            score = self.PIECE_TABLE_QUEEN[move.to_square]
        
        return score / 10

    def vulnerable_squares(
            self: typing.Self,
            board: chess.Board,
            move: chess.Move
        ) -> float:
        king = self.get_squares_attacked_by_king(board, not self.side)
        attacked = self.get_attacked_squares_no_king(board, not self.side)

        king_vulernable = king - (king & attacked)

        board.push(move)

        self_attacking = self.get_attacks(board, move.to_square)

        board.pop()

        if king_vulernable & self_attacking:
            # Attacking a vulnerable square!
            return 1.5

        return 0

    def check_value(
            self: typing.Self,
            board: chess.Board,
            move: chess.Move
        ) -> float:
        value = 1

        fork_pre = self.find_hanging_pieces(board, self.side)

        board.push(move)

        ### Number of king moves. ###

        king_mask = board.pieces_mask(chess.KING, not self.side)
        king_moves = len(list(board.generate_legal_moves(from_mask=king_mask)))
        value += (9 - king_moves) / 3

        ### Potential forks. ###
        
        fork_post = self.find_hanging_pieces(board, self.side)
        post_count = fork_post.bit_count()

        if post_count > fork_pre.bit_count():
            value += post_count * 7.5

        ########################        

        board.pop()

        return value
    
    def check_trapped_pieces(
            self: typing.Self,
            board: chess.Board,
            move: chess.Move
        ) -> float:
        board.push(move)

        attack_pieces = self.get_attacked_pieces(board, not self.side)

        if not attack_pieces:
            board.pop()
            return 0
        
        out = 0
        
        all_attacks = self.get_attacked_squares(board, self.side)

        for square in self.iterate_through_bitboard(attack_pieces):
            square_attacks = self.get_attacks_filtered(board, not self.side, square)

            if square_attacks & all_attacks == square_attacks:
                attacked = self.get_piece_value_from_square(board, square)
                attackers = self.get_square_attackers(board, self.side, square)

                for potential in self.iterate_through_bitboard(attackers):
                    if self.get_piece_value_from_square(board, potential) < attacked:
                        out += 10
                        break

        board.pop()

        return out

class AlphaMove(ChessBot):
    name = "alphamove"
    creator = "Randall Munroe"
    description = "Sorts the legal moves alphabetically, and plays the middle one."
    color = 0x7f7f7f

    def turn(
            self: typing.Self,
            board: chess.Board
        ) -> chess.Move:
        moves = list(board.legal_moves)

        sorted_moves = sorted(moves, key=lambda move: board.san(move))
        
        return sorted_moves[math.ceil(len(sorted_moves)) - 1]

class colon_three(ChessBot):
    name = ":3"
    description = """:3"""
    creator = "Duck"
    color = 0xffa8ff

    bot_turn = None
    
    PIECE_TABLE_VARIATION = {
        n: 1 if n < 10 else (
            0 if n > 20 else (
                math.cos((math.pi / 10) * n - math.pi) / 2 + 0.5
            )
        )
        for n in range(33)
    }
    
    # The point at which to award the maximum amount of points for the piece sum.
    # If the piece sum goes above this then it will award a higher than normal amount of points.
    # That should really only occur if it promotes a ton of queens, though.
    MAX_PIECE_SUM = 3940 # Starting position.
    
    DISTANCE_MULTIPLIER = {
        chess.PAWN: 1,
        chess.KNIGHT: 1.5,
        chess.BISHOP: 1.5,
        chess.ROOK: 1.25,
        chess.QUEEN: 1.33,
        chess.KING: 0.2   
    }
    
    PIECE_VALUES = {
        chess.PAWN: 100,
        chess.KNIGHT: 300,
        chess.BISHOP: 320,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 300
    }
    
    WHITE_PIECE_TABLE_PAWN_START = list(reversed([
        0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5,  5, 10, 25, 25, 10,  5,  5,
        0,  0,  0, 20, 20,  0,  0,  0,
        5, -5,-10,  0,  0,-10, -5,  5,
        5, 10, 10,-20,-20, 10, 10,  5,
        0,  0,  0,  0,  0,  0,  0,  0
    ]))

    WHITE_PIECE_TABLE_PAWN_END = list(reversed([
        100, 100, 100, 100, 100, 100, 100, 100,
         75,  75,  75,  75,  75,  75,  75,  75,
         50,  50,  50,  50,  50,  50,  50,  50,
         25,  25,  25,  25,  25,  25,  25,  25,
         20,  20,  20,  20,  20,  20,  20,  20,
         10,  10,  10,  10,  10,  10,  10,  10,
          0,   0,   0,   0,   0,   0,   0,   0,
          0,   0,   0,   0,   0,   0,   0,   0
    ]))

    WHITE_PIECE_TABLE_KNIGHT = list(reversed([
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50,
    ]))

    WHITE_PIECE_TABLE_BISHOP = list(reversed([
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5, 10, 10,  5,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  5,  0,  0,  0,  0,  5,-10,
        -20,-10,-10,-10,-10,-10,-10,-20,
    ]))
    
    WHITE_PIECE_TABLE_ROOK = list(reversed([
        0,  0,  0,  0,  0,  0,  0,  0,
        5, 10, 10, 10, 10, 10, 10,  5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        0,  0,  0,  5,  5,  0,  0,  0
    ]))

    WHITE_PIECE_TABLE_QUEEN = list(reversed([
        -20,-10,-10, -5, -5,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5,  5,  5,  5,  0,-10,
        -5,  0,  5,  5,  5,  5,  0, -5,
        -5,  0,  5,  5,  5,  5,  0, -5,
        -10,  5,  5,  5,  5,  5,  0,-10,
        -10,  0,  5,  0,  0,  0,  0,-10,
        -20,-10,-10, -5, -5,-10,-10,-20
    ]))

    WHITE_PIECE_TABLE_KING_START =list(reversed([
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -10,-20,-20,-20,-20,-20,-20,-10,
        20, 20,  0,  0,  0,  0, 20, 20,
        20, 30, 10,  0,  0, 10, 30, 20
    ]))

    WHITE_PIECE_TABLE_KING_END = list(reversed([
        -50,-40,-30,-20,-20,-30,-40,-50,
        -30,-20,-10,  0,  0,-10,-20,-30,
        -30,-10, 20, 30, 30, 20,-10,-30,
        -30,-10, 30, 40, 40, 30,-10,-30,
        -30,-10, 30, 40, 40, 30,-10,-30,
        -30,-10, 20, 30, 30, 20,-10,-30,
        -30,-30,  0,  0,  0,  0,-30,-30,
        -50,-30,-30,-30,-30,-30,-30,-50
    ]))
    
    # The black piece tables are the white ones but reversed.
    BLACK_PIECE_TABLE_PAWN_START = list(reversed(WHITE_PIECE_TABLE_PAWN_START))
    BLACK_PIECE_TABLE_PAWN_END = list(reversed(WHITE_PIECE_TABLE_PAWN_END))
    BLACK_PIECE_TABLE_KNIGHT = list(reversed(WHITE_PIECE_TABLE_KNIGHT))
    BLACK_PIECE_TABLE_BISHOP = list(reversed(WHITE_PIECE_TABLE_BISHOP))
    BLACK_PIECE_TABLE_ROOK = list(reversed(WHITE_PIECE_TABLE_ROOK))
    BLACK_PIECE_TABLE_QUEEN = list(reversed(WHITE_PIECE_TABLE_QUEEN))
    BLACK_PIECE_TABLE_KING_START = list(reversed(WHITE_PIECE_TABLE_KING_START))
    BLACK_PIECE_TABLE_KING_END = list(reversed(WHITE_PIECE_TABLE_KING_END))

    #######################################################################################################################
    ##### UTILITIES #######################################################################################################
    #######################################################################################################################
    
    def get_attacks(
            self: typing.Self,
            board: chess.Board,
            square: chess.Square
        ) -> chess.Bitboard:
        """Returns a bitboard for the squares that the piece on the given square attacks."""
        return int(board.attacks(square))

    def get_attacked_squares(
            self: typing.Self,
            board: chess.Board,
            side: chess.Color
        ) -> chess.Bitboard:
        """Returns a bitboard of squares attacked by the given side."""
        total = chess.BB_EMPTY

        for square in board.piece_map(mask=self.get_occupied_bitboard(board, side)):
            total |= self.get_attacks(board, square)

        return total
    
    def get_piece_bitboard(
            self: typing.Self,
            board: chess.Board,
            piece: chess.Piece
        ) -> chess.Bitboard:
        """Returns a bitboard of all the squares with the given piece."""
        return board.pieces_mask(piece)

    def get_occupied_bitboard(
            self: typing.Self,
            board: chess.Board,
            side: chess.Color
        ) -> chess.Bitboard:
        """Returns a bitboard of all the squares occupied by the given side."""
        return board.occupied_co[side]
    
    def get_undefended_pieces(
            self: typing.Self,
            board: chess.Board,
            side: chess.Color
        ) -> chess.Bitboard:
        """Returns a bitboard of all the pieces for the given side that are not defended."""
        return self.get_occupied_bitboard(board, side) - (self.get_occupied_bitboard(board, side) & self.get_attacked_squares(board, side))

    def get_hanging_pieces(
            self: typing.Self,
            board: chess.Board,
            side: chess.Color
        ) -> chess.Bitboard:
        """Returns a bitboard of the pieces for the given side that are attacked by the other side but not defended."""
        return self.get_undefended_pieces(board, side) & self.get_attacked_squares(board, not side)
    
    def is_passed_pawn(
            self: typing.Self,
            board: chess.Board,
            square: chess.Square,
            side: chess.Color
        ) -> bool:
        """Returns a boolean for whether the pawn on the given square is a passed pawn."""
        cover_bitboard = 0
        
        pawn_file = chess.square_file(square)
        
        # Get a bitboard covering the file the pawn is on, as well as the files next to it.
        cover_bitboard |= chess.BB_FILES[pawn_file]
        
        if pawn_file != 0:
            cover_bitboard |= chess.BB_FILES[pawn_file - 1]
        if pawn_file != 7:
            cover_bitboard |= chess.BB_FILES[pawn_file + 1]
        
        # Shift the bitboard by 8 per row the pawn is away from the end of the board.
        # If it's a white pawn, shift right, if it's a black pawn, shift left.
        # Add 1 to the shift multiplier to disregard pawns on the same rank as the passed pawn.
        if side == chess.WHITE:
            cover_bitboard <<= 8 * (chess.square_rank(square) + 1)
        else:
            cover_bitboard >>= 8 * (8 - chess.square_rank(square))
        
        # Bitwise and the other side's pieces with the overall pawn bitboard to get the other side's pawns in a bitboard.
        # Then, by bitwise anding that with the cover bitboard any bits that are 1 are opposing pawns that are able to stop this pawn.
        # If that's the case, then this pawn is not a passed pawn, so invert the result to return True for actual passed pawns.
        return not bool(board.pawns & board.occupied_co[not side] & cover_bitboard)

    def find_passed_pawns(
            self: typing.Self,
            board: chess.Board,
            side: chess.Color
        ) -> chess.Bitboard:
        """Returns a bitboard of the passed pawns for the given side."""
        result = 0
        
        for pawn in board.pieces(chess.PAWN, side):
            if self.is_passed_pawn(board, pawn, side):
                result |= chess.BB_SQUARES[pawn]
        
        return result

    def occupied_value(
            self: typing.Self,
            board: chess.Board,
            side: chess.Color,
            value: chess.PieceType,
            condition: typing.Callable[[int, int], bool],
            exclude_king: bool = True
        ) -> chess.Bitboard:
        """Returns a bitboard for every occupied square with a piece value that satisfies the given condition."""
        check_value = self.PIECE_VALUES[value]
        
        out = 0
        
        for piece_type, piece_value in self.PIECE_VALUES.items():
            if not condition(piece_value, check_value):
                continue
            
            if piece_type == chess.KING and exclude_king:
                continue
            
            for piece in board.pieces(piece_type, side):
                out |= chess.BB_SQUARES[piece]
        
        return out

    #######################################################################################################################
    #######################################################################################################################
    #######################################################################################################################

    def turn(
            self: typing.Self,
            board: chess.Board
        ) -> chess.Move:
        self.bot_turn = board.turn
        pre_check_board = board.copy()
        
        moves = []

        for move in board.legal_moves:
            # Push the move to the board and get the ranking of the move.
            board.push(move)

            ranking = self.rate_board_state(
                pre_board = pre_check_board,
                post_board = board,
                move = move
            )
            
            if ranking == math.inf:
                board.pop()
                return move

            # Append the move and its ranking to the list of moves and pop the move from the board.
            moves.append((move, ranking))
            board.pop()
        
        # Get a dictionary with the keys being the ranks
        # and the values being a list of moves with that rank.
        move_brackets = {}
        
        for move, rank in moves:
            if rank not in move_brackets:
                move_brackets[rank] = [move]
            else:
                move_brackets[rank].append(move)
        
        
        sort = sorted(list(move_brackets.items()), key=lambda x: x[0], reverse=True)
        
        for rank, sorted_moves in copy.deepcopy(sort):
            while len(sorted_moves) > 0:
                chosen = random.choice(sorted_moves)
                
                if not self.sanity_check(board, chosen):
                    sorted_moves.remove(chosen)
                    continue
                
                return chosen
            
            # If it gets here then all the moves resulted in the sanity check failing, that's not good.
        
        # If the `for` loop didn't return anything then every single possible move fails the sanity check,
        # in which case we should just return a random one in the highest bracket.
        highest = max(move_brackets.keys())
        
        return random.choice(move_brackets[highest])
    
    def sanity_check(
            self: typing.Self,
            board: chess.Board,
            move: chess.Move
        ) -> bool:
        """Final sanity check for good moves. This makes sure nothing is really wrong with the move.
        Blundering checkmate, for example, would flag this and the move would be ignored.
        
        Returns a boolean for whether the move is okay to play."""
        board.push(move)

        # Check for checkmate.
        # Check the opponent's legal moves to see if they have mate in 1.
        for move_check in board.legal_moves:
            board.push(move_check)
            if board.is_checkmate():
                board.pop()
                board.pop()
                return False
            
            if self.check_mate_in_two(board):
                board.pop()
                board.pop()
                return False
            
            board.pop()
        
        board.pop()
        
        # If nothing else fires, the move is probably okay.
        return True

    def rate_board_state(
            self: typing.Self,
            pre_board: chess.Board,
            post_board: chess.Board,
            move: chess.Move
        ) -> float:
        """Ranks a board state based on the some criteria.""" 
        # If it's checkmate, that's pretty good. Return infinity.
        if post_board.is_checkmate():
            return math.inf
        
        # We want to avoid draws, so if it's a draw, return negative infinity.
        if post_board.is_game_over(claim_draw=True):
            return -math.inf
        
        # Check for mate in 2.
        if self.check_mate_in_two(post_board):
            return 1e200 # Not math.inf in case there's mate in 1 and we haven't checked it yet.

        # Base score of 0.
        out = 0

        # If it's a capture, reward that by adding the value of the captured piece to the score.
        if pre_board.is_capture(move):
            captured_piece = pre_board.piece_at(move.to_square)
            try:
                captured_piece_value = self.PIECE_VALUES[captured_piece.piece_type]
            except AttributeError:
                # En passant.
                captured_piece_value = self.PIECE_VALUES[chess.PAWN]
            out += captured_piece_value
        
        # If it's a check, reward that by adding 1 to the score.
        if post_board.is_check():
            out += self.check_value(pre_board, post_board, move)
            # out += 100
        
        # For every hanging piece, subtract 5 from the score.
        out -= self.hanging_pieces_penalty(post_board)
        # hanging = self.get_hanging_pieces(post_board, self.bot_turn)
        # out -= hanging.bit_count() * 500
        
        # If this move is moving a passed pawn, we should reward that.
        out += self.moving_passed_pawn(pre_board, move)
        
        # Use the piece square tables to rate the ending location of the played move.
        out += self.rate_ending_location(pre_board, move)
        
        # Apply a bonus based on the average distance of the pieces to the opposing king.
        out += self.average_distance_bonus(post_board, move)
        
        # Apply a bonus based on the sum of piece values for the bot.
        # This really only makes a difference in regards to pawn promotion.
        out += self.piece_sum(post_board)
        
        # Attempt to keep castling rights by applying a 50 point
        # penalty to moves that would lose castling rights.
        out -= self.castling_rights(pre_board, post_board, move)
        
        # Apply a bonus or penalty based on how safe our
        # king is and how safe the opposing king is.
        out += self.rate_king_safety(post_board)
        
        return out
    
    #######################################################################################################################
    ##### RANKING CRITERIA ################################################################################################
    #######################################################################################################################
    
    def check_value(
            self: typing.Self,
            pre_board: chess.Board,
            post_board: chess.Board,
            move: chess.Move
        ) -> int:
        """Gives a rating for a move that puts the opponent in check."""
        
        # By default give checks a bonus of 100 to incentivise them
        out = 100
        
        # Check for forks!
        # If the piece moved is also attacking an undefended piece or a 
        # defended piece of higher value add a larger bonus for the move
        # based on what exactly is the case.
        attacked = self.get_attacks(post_board, move.to_square)
        opposing_undefended = self.get_undefended_pieces(post_board, not self.bot_turn)
        
        # We want to make sure the king isn't in the bitboard of undefended pieces, since that could mess things up.
        opposing_king = chess.BB_SQUARES[post_board.king(not self.bot_turn)]
        if opposing_king & opposing_undefended:
            opposing_undefended -= opposing_king
        
        # If the bitwise AND returns something other than 0 that means we're forking an undefended piece.
        undefended_attacked = attacked & opposing_undefended
        if undefended_attacked:
            # We're assuming we'll capture the highest value piece if there's multiple,
            # so iterate through the bits in the bitboard and find the one with the highest piece value.
            pieces = []
            for forked_square in chess.scan_forward(undefended_attacked):
                forked_piece = post_board.piece_at(forked_square).piece_type
                pieces.append(self.PIECE_VALUES[forked_piece])
            
            out += max(pieces)
        
        # Time to check for defended pieces we're attacking that are worth more than what we're attacking with.
        attacking_value = self.PIECE_VALUES[post_board.piece_at(move.to_square).piece_type]
        defended_squares = self.get_attacked_squares(post_board, not self.bot_turn)
        opposing_pieces = self.get_occupied_bitboard(post_board, not self.bot_turn)
        
        defended_pieces = defended_squares & opposing_pieces
        attacked_pieces = defended_pieces & attacked
        
        if attacked_pieces:
            pieces = []
            for forked_square in chess.scan_forward(undefended_attacked):
                forked_piece_value = self.PIECE_VALUES[post_board.piece_at(forked_square).piece_type]
                
                if forked_piece_value > attacking_value:
                    pieces.append(forked_piece_value)
            
            # An empty list will return False, so this checks if the list has any pieces in it.
            if pieces:
                out += max(pieces) * (2/3)
        
        return out

    def moving_passed_pawn(
            self: typing.Self,
            board: chess.Board,
            move: chess.Move
        ) -> int:
        """Returns a boolean for whether the given move is moving a passed pawn."""
        if board.piece_at(move.from_square).piece_type == chess.PAWN:
            rank_multiplier = chess.square_rank(move.to_square) if self.bot_turn == chess.WHITE else 7 - chess.square_rank(move.to_square)
            
            return self.is_passed_pawn(board, move.from_square, board.turn) * (rank_multiplier * 50)
        
        return 0
    
    def rate_ending_location(
            self: typing.Self,
            board: chess.Board,
            move: chess.Move
        ) -> int:
        piece_type = board.piece_at(move.from_square).piece_type
        
        # Pawns and kings are a bit special since they have two different ones that are interpolated between based on the number of remaining pieces.
        if piece_type == chess.PAWN:
            return self.rate_ending_location_pawn(board, move)
        elif piece_type == chess.KING:
            return self.rate_ending_location_king(board, move)
        
        # Knights.
        elif piece_type == chess.KNIGHT:
            if self.bot_turn == chess.WHITE:
                return self.WHITE_PIECE_TABLE_KNIGHT[move.to_square]
            else:
                return self.BLACK_PIECE_TABLE_KNIGHT[move.to_square]
        
        # Bishops:
        elif piece_type == chess.BISHOP:
            if self.bot_turn == chess.WHITE:
                return self.WHITE_PIECE_TABLE_BISHOP[move.to_square]
            else:
                return self.BLACK_PIECE_TABLE_BISHOP[move.to_square]
        
        # Rooks:
        elif piece_type == chess.ROOK:
            if self.bot_turn == chess.WHITE:
                return self.WHITE_PIECE_TABLE_ROOK[move.to_square]
            else:
                return self.BLACK_PIECE_TABLE_ROOK[move.to_square]
        
        # Queens:
        elif piece_type == chess.QUEEN:
            if self.bot_turn == chess.WHITE:
                return self.WHITE_PIECE_TABLE_QUEEN[move.to_square]
            else:
                return self.BLACK_PIECE_TABLE_QUEEN[move.to_square]

        # This should be unreachable.
        return 0

    def rate_ending_location_pawn(
            self: typing.Self,
            board: chess.Board,
            move: chess.Move
        ) -> int:
        """Gives a score based on the location of a pawn if it's being moved."""
        remaining_pieces = board.occupied.bit_count()
        
        ending_contribution = self.PIECE_TABLE_VARIATION[remaining_pieces]
        
        if self.bot_turn == chess.WHITE:
            start = self.WHITE_PIECE_TABLE_PAWN_START[move.to_square]
            end = self.WHITE_PIECE_TABLE_PAWN_END[move.to_square]
        else:
            start = self.BLACK_PIECE_TABLE_PAWN_START[move.to_square]
            end = self.BLACK_PIECE_TABLE_PAWN_END[move.to_square]
        
        return ending_contribution * (end - start) + start

    def rate_ending_location_king(
            self: typing.Self,
            board: chess.Board,
            move: chess.Move
        ) -> int:
        """Gives a score based on the location of the king if it's being moved."""
        remaining_pieces = board.occupied.bit_count()
        
        ending_contribution = self.PIECE_TABLE_VARIATION[remaining_pieces]
        
        if self.bot_turn == chess.WHITE:
            start = self.WHITE_PIECE_TABLE_KING_START[move.to_square]
            end = self.WHITE_PIECE_TABLE_KING_END[move.to_square]
        else:
            start = self.BLACK_PIECE_TABLE_KING_START[move.to_square]
            end = self.BLACK_PIECE_TABLE_KING_END[move.to_square]
        
        return ending_contribution * (end - start) + start
    
    # Unused, but should still theoretically work.
    def full_hanging_pieces_penalty(
            self: typing.Self,
            post_board: chess.Board
        ) -> int:
        """Applies a negative penalty based on hanging pieces, this only accounts for undefended pieces, however."""
        hanging_pieces = self.get_hanging_pieces(post_board, self.bot_turn)
        
        if not hanging_pieces:
            return 0
        
        out_score = 0
        
        for hanging_square in chess.scan_forward(hanging_pieces):
            # Get the piece on the given square.
            piece_type = post_board.piece_at(hanging_square).piece_type
            out_score -= self.PIECE_VALUES[piece_type]
        
        return out_score
    
    def hanging_pieces_penalty(
            self: typing.Self,
            post_board: chess.Board
        ) -> int:
        """Applies a negative penalty based on hanging pieces, accounting for piece value."""
        self_occupied = self.get_occupied_bitboard(post_board, self.bot_turn)
        self_attacking = self.get_attacked_squares(post_board, self.bot_turn)
        
        penalty_value = 0
        
        for square in chess.scan_forward(self.get_occupied_bitboard(post_board, not self.bot_turn)):
            piece_type = post_board.piece_at(square).piece_type
            
            attacking = self.get_attacks(post_board, square)
            
            for attacked_square in chess.scan_forward(attacking & self_occupied):
                attacked_type = post_board.piece_at(attacked_square).piece_type
                
                attacking_amount = post_board.attackers_mask(not self.bot_turn, attacked_square).bit_count()
                defending_amount = post_board.attackers_mask(self.bot_turn, attacked_square).bit_count()
                
                if attacking_amount > defending_amount:
                    penalty_value += self.PIECE_VALUES[attacked_type] * 1.5
                
                if not chess.BB_SQUARES[attacked_square] & self_attacking:
                    penalty_value += self.PIECE_VALUES[attacked_type] * 1.5
                
                # If it's worth the same assume it's a fair trade.
                elif self.PIECE_VALUES[attacked_type] > self.PIECE_VALUES[piece_type]:
                    penalty_value += self.PIECE_VALUES[attacked_type] / 2
                    
        return penalty_value

    def average_distance_bonus(
            self: typing.Self,
            post_board: chess.Board,
            move: chess.Move
        ) -> int:
        opposing_king = post_board.king(not self.bot_turn)
        opposing_rank = chess.square_rank(opposing_king)
        opposing_file = chess.square_file(opposing_king)
        
        distances = []
        for piece_square in chess.scan_forward(self.get_occupied_bitboard(post_board, self.bot_turn)):
            square_rank = chess.square_rank(piece_square) - opposing_rank
            square_file = chess.square_file(piece_square) - opposing_file
            
            square_rank **= 2
            square_file **= 2
            
            distances.append(square_rank + square_file)
        
        out = int((128 - (sum(distances) / len(distances)) / 128 * 300))
        
        piece_type = post_board.piece_at(move.to_square).piece_type
        out *= self.DISTANCE_MULTIPLIER[piece_type]
        
        return out

    def check_mate_in_two(
            self: typing.Self,
            post_board: chess.Board
        ) -> bool:
        """Attempts to find mate in two. Returns a boolean for whether it found mate in two."""
        
        for opponent_move in post_board.legal_moves:
            post_board.push(opponent_move)

            for self_move in post_board.legal_moves:
                post_board.push(self_move)

                if post_board.is_checkmate():
                    post_board.pop()
                    break

                post_board.pop()
            else:
                post_board.pop()
                break

            post_board.pop()
        else:
            return True

        return False
    
    def piece_sum(
            self: typing.Self,
            board: chess.Board
        ) -> int:
        amount = 0
        
        for piece_type in chess.PIECE_TYPES:
            # Ignore the king.
            if piece_type == chess.KING:
                continue
            
            amount += board.pieces_mask(piece_type, self.bot_turn).bit_count() * self.PIECE_VALUES[piece_type]
        
        return amount / self.MAX_PIECE_SUM * 100
    
    def castling_rights(
            self: typing.Self,
            pre_board: chess.Board,
            post_board: chess.Board,
            move: chess.Move
        ) -> int:
        if pre_board.is_castling(move):
            return -75 # Apply a bonus to castling.
        
        if pre_board.has_castling_rights(self.bot_turn) and not post_board.has_castling_rights(self.bot_turn):
            return 100

        return 0
    
    def rate_king_safety(
            self: typing.Self,
            post_board: chess.Board
        ) -> int:
        """Rates the position based on the king safety of both sides."""
        self_safety = self.king_safety_single(post_board, self.bot_turn)
        opposing_safety = self.king_safety_single(post_board, not self.bot_turn)
        
        return self_safety - opposing_safety
    
    def king_safety_single(
            self: typing.Self,
            board: chess.Board,
            side: chess.Color
        ) -> int:
        """Rates king safety for the given side."""
        king = board.king(side)
        
        check = chess.BB_KING_ATTACKS[king]
        
        if board.turn == side:
            moves = list(board.generate_legal_moves(chess.BB_SQUARES[king]))
        else:
            board.push(chess.Move.null())
            moves = list(board.generate_legal_moves(chess.BB_SQUARES[king]))
            board.pop()
        
        return 300 - (check & self.get_attacks(board, not side)).bit_count() * 33 - len(moves) * 50

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

def get_random_moves(amount: int) -> list[str]:
    """Gets a list of random moves from `data/Games.txt` and returns a random list of opening moves from it.
    
    If you want to force a set of opening moves have this return the output from `parse_san`."""
    return random.choice(copy.deepcopy(game_lines)).split(" ")[:amount + 1]

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
    
    # Get 6 random moves from the list of Chess games, 3 for each side.
    starting_moves = get_random_moves(amount=6)

    # Play the moves.
    for move in starting_moves:
        board.push_san(move)
        moves.append(move)
    
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

def determine_matches(database: u_files.DatabaseInterface) -> list[tuple[typing.Type[ChessBot], typing.Type[ChessBot] | None]]:
    """Generates a set of bot matchups in a way that hopefully means bots of similar ratings will be paired with each other.
    I cannot provide any reference to the method used to do this as I made it up.

    Args:
        database (u_files.DatabaseInterface): The database.

    Returns:
        list[tuple[typing.Type[ChessBot], typing.Type[ChessBot] | None]]: List of the generated matchups, with 2 item tuples containing the bot classes. If there is a bot that has a bye it will be at the end with the other tuple element being `None`.
    """
    standard_deviation = 128 # Higher standard deviation means it's more likely to be paired with a bot with a larger elo difference.

    def equation(
            current: int,
            check: int
        ) -> float:
        return 1/(math.sqrt(2 * math.pi * standard_deviation)) * (math.e ** (-(((check - current) ** 2) / (2 * standard_deviation ** 2))))

    def random(
            weights_dict: dict[str, float],
            remove: list[str]
        ) -> str:
        weights = {n: v for n, v in weights_dict.items() if n not in remove}

        weight_sum = sum(weights.values())
        
        weights = {n: v / weight_sum for n, v in weights.items()}

        return str(np.random.choice(
            a = list(weights.keys()),
            p = list(weights.values()),
            size = 1
        )[0])

    elos = {bot: instance.get_elo(database) for bot, instance in get_bot_list().items()}

    weights = {}

    for name, elo in elos.items():
        weight = {}
        
        for c_name, c_elo in elos.items():
            if c_name == name:
                continue
            
            weight[c_name] = equation(elo, c_elo)
        
        weights[name] = weight

    removed = []
    order = list(elos.keys())
    np.random.shuffle(order)

    matches = []

    for bot in order:
        if bot in removed:
            continue

        if len(order) - len(removed) == 1:
            matches.append((get_bot(bot), None))
            break

        chosen = random(weights[bot], removed)

        removed.append(bot)
        removed.append(chosen)

        matches.append((
            get_bot(bot),
            get_bot(chosen)
        ))

    return matches

def get_rating_history(database: u_files.DatabaseInterface) -> list[dict[str, float]]:
    return database.load("chess", "rating_history", default = [])

def get_all_elos(
        database: u_files.DatabaseInterface,
        return_classes: bool = True
    ) -> dict[typing.Type[ChessBot], float]:
    out = {}

    for name, bot in get_bot_list().items():
        out[bot if return_classes else name] = bot.get_elo(database)


    return out