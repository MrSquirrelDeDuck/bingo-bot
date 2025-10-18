"""This cog is for the commands that allow for playing Chess against bots."""

from discord.ext import commands
import discord
import typing
import time
import random
import copy
import traceback
import io
import asyncio
import threading
import requests

# pip install chess
import chess

import sys

import utility.bread as u_bread
import utility.files as u_files
import utility.custom as u_custom
import utility.chess_utils as u_chess
import utility.converters as u_converters
import utility.interface as u_interface
import utility.images as u_images
import utility.text as u_text

database = None # type: u_files.DatabaseInterface

PING_LISTS_CHANNEL = 1196865786489344120 # 1060344552818483230

class Chess_cog(
        u_custom.CustomCog,
        name="Chess",
        description="You can play Chess here against various bots!\nTo play Chess against other humans, use Machine-Mind."
    ):
    
    def run_in_thread(func: typing.Callable):
        """Decorator to run the function in a thread automatically when it is run."""
        def wrapped(self: typing.Self, *args, **kwargs):
            thread = threading.Thread(
                target = func,
                args = (self,) + args,
                kwargs = kwargs
            )
            thread.start()
        
        return wrapped

    async def hourly_task(self: typing.Self):
        """Code that runs for every hour."""
        bread_time = u_bread.bst_time()

        # If it's not the correct time (noon in EDT,) then stop here.
        if bread_time == 18:
            try:
                await self.announce_matches()
            except Exception as e:
                await u_interface.output_error(ctx=None, error=e)
            try:
                await self.announce_puzzles()
            except Exception as e:
                await u_interface.output_error(ctx=None, error=e)
            return
        
        if bread_time == 16:
            self.run_computations()
            return
        
    @run_in_thread
    def run_computations(self: typing.Self) -> None:
        database.save("chess", "daily", data={})
        self.compute_matches()
        self.compute_puzzles()
        database.save("chess", "daily", "last_updated", data=time.time())
    
    def compute_matches(self: typing.Self) -> None:
        # Clear the data so the announce code can easily spot if something went wrong.
        database.save("chess", "daily", "matches", data=None)
        
        game_data = u_chess.determine_matches(database)

        if game_data[-1][1] is None:
            bye_bot = game_data.pop(-1)[0].name
        else:
            bye_bot = None
        
        games = [
            {
                "white": white.name,
                "black": black.name
            }
            for white, black in game_data
        ]
        
        # Now actaully run the games.
        
        game_outcomes = []
        
        print("Running chess matches.")
        for index, data in enumerate(games):
            game_white = u_chess.get_bot(data["white"])
            game_black = u_chess.get_bot(data["black"])

            print(f"{index+1}/{len(games)}: {game_white.name} vs {game_black.name}")
            game_data = u_chess.run_match(
                white = game_white,
                black = game_black
            )
            print("Done.")
            
            game_data["white"] = data["white"]
            game_data["black"] = data["black"]
            
            game_outcomes.append(game_data)
            
        save_data = {
            "bye": bye_bot,
            "games": game_outcomes
        }
            
        database.save("chess", "daily", "matches", data=save_data)
        
        print("-- Finished computing matches. --")
        
    def compute_puzzles(self: typing.Self) -> None:
        database.save("chess", "daily", "puzzles", data=None)
        
        # It must use `requests` instead of `aiohttp` since this isn't an async function.
        print("Fetching puzzles.")
        with requests.Session() as session:
            try:
                print("Getting daily puzzle.")
                daily = session.get("https://lichess.org/api/puzzle/daily").json()
                # daily = {'game': {'id': 'w1ANEdKC', 'perf': {'key': 'rapid', 'name': 'Rapid'}, 'rated': True, 'players': [{'name': 'Klasa16', 'id': 'klasa16', 'color': 'white', 'rating': 2144}, {'name': 'gukfjycjtdtjdthdtue', 'id': 'gukfjycjtdtjdthdtue', 'color': 'black', 'rating': 2312}], 'pgn': 'e4 c6 Nf3 d5 Nc3 dxe4 Nxe4 Nf6 Qe2 Nxe4 Qxe4 Nd7 d4 Nf6 Qh4 e6 Bd3 Be7 Bd2 h6 O-O-O Nd5 Qe4 Bf6 Ne5 a5 Rhe1 b5 Nxc6 Qd6 Ne5 Rb8 Kb1 Nb4 Bxb4 axb4 Qc6+ Qxc6 Nxc6 Rb6 Nxb4 O-O c3 Bb7 Be4 Bxe4+ Rxe4 Rc8 d5 Rd6 Kc2 Rcd8 Rde1 exd5 Re8+ Kh7 Rxd8 Rxd8 Rd1 d4 cxd4 Rxd4 Rxd4 Bxd4 f3 Kg6 Nc6 Bc5 Ne5+ Kf5 Nxf7 Be7 f4 Kf6 Ne5 Bd6 Nd3 Kf5 b3 b4 Kd2 Ke4 Ke2 Be7 g3 Bd6 Ne5 Bxe5 fxe5 Kxe5 Ke3 h5 h3 g5 g4', 'clock': '10+0'}, 'puzzle': {'id': 'R6Wj6', 'rating': 1873, 'plays': 41060, 'solution': ['h5h4', 'e3e2', 'e5e4'], 'themes': ['endgame', 'short', 'zugzwang', 'advantage', 'quietMove', 'pawnEndgame', 'defensiveMove'], 'initialPly': 94}}
                time.sleep(1)
                print("Getting bulk puzzles.")
                bulk = session.get("https://lichess.org/api/puzzle/batch/mix?nb=4").json()
                # bulk = {'puzzles': [{'game': {'id': 'DGH0ph8k', 'perf': {'key': 'blitz', 'name': 'Blitz'}, 'rated': True, 'players': [{'name': 'Loup_Blanc', 'flair': 'nature.wolf', 'id': 'loup_blanc', 'color': 'white', 'rating': 1939}, {'name': 'nirmalraj628', 'id': 'nirmalraj628', 'color': 'black', 'rating': 1923}], 'pgn': 'e4 c6 d4 d5 e5 Bf5 Nf3 e6 c3 Nd7 Bd3 Bg6 a3 Ne7 O-O Bxd3 Qxd3 Nf5 g4 Ne7 h4 h5 g5 Ng6 Kg2 a6 Kh3 c5 b4 c4 Qe3 a5 Bb2 axb4 axb4 b5 Nbd2 Nb6 Nh2 Na4 Bc1 Be7 f4 Qb8 Nhf3 Bd8 Ne1 Ne7 Ndf3 Nf5 Qd2 g6 Bb2 O-O Ra3 Be7 Ng2 Qb7 Rfa1 Qd7 Qc2 Qb7 Qc1 Nxb2 Qxb2 Rxa3 Rxa3 Ra8 Qa2 Rxa3 Qxa3 Kg7 Qa5 Kg8 Nd2 Kg7 Nb1 Qb8 Na3 Bd8 Qxb5 Qxb5 Nxb5 Bb6 Na3 Ne7 Nc2 Nc6 Kg3 Na7 Kf3 Nb5 Nce3 Nxc3 Nc2 Ne4 Nge1 Nd2+ Ke2 Nb3 Kf3 Nxd4+ Nxd4 Bxd4 b5 Bc5 Nc2 d4 Ke4 d3 Ne3 Bxe3', 'clock': '3+0'}, 'puzzle': {'id': 'Fknvu', 'rating': 1286, 'plays': 994, 'solution': ['e4e3', 'g7f8', 'b5b6', 'f8e7', 'b6b7'], 'themes': ['long', 'advancedPawn', 'crushing', 'endgame'], 'initialPly': 111}}, {'game': {'id': 'aDBSJek7', 'perf': {'key': 'blitz', 'name': 'Blitz'}, 'rated': True, 'players': [{'name': 'shlumpa', 'title': 'CM', 'id': 'shlumpa', 'color': 'white', 'rating': 2586}, {'name': 'Donald666Trump', 'id': 'donald666trump', 'color': 'black', 'rating': 2431}], 'pgn': 'd4 d5 c4 dxc4 e3 c5 Nf3 cxd4 Qxd4 Qxd4 Nxd4 Bd7 Bxc4 Nc6 Nxc6 Bxc6 O-O e6 Nc3 O-O-O e4 Nf6 Bg5 h6 Bh4 Rd4 Bxf6 gxf6 Bb5 Bxb5 Nxb5 Rxe4 Nxa7+ Kb8 Nb5 Bc5 a3 Re2 b4 Bb6 Rae1', 'clock': '3+0'}, 'puzzle': {'id': 'fq3rM', 'rating': 1268, 'plays': 578, 'solution': ['b6f2', 'f1f2', 'e2e1'], 'themes': ['deflection', 'endgame', 'master', 'short', 'advantage', 'fork'], 'initialPly': 40}}, {'game': {'id': '7Ojr62NT', 'perf': {'key': 'blitz', 'name': 'Blitz'}, 'rated': True, 'players': [{'name': 'alemon25', 'id': 'alemon25', 'color': 'white', 'rating': 2409}, {'name': 'Ranaroek66', 'title': 'GM', 'id': 'ranaroek66', 'color': 'black', 'rating': 2658}], 'pgn': 'd4 d5 c4 Nc6 Nc3 dxc4 d5 Ne5 e4 e6 f4 Nd3+ Bxd3 cxd3 Qxd3 exd5 exd5 Nf6 Nf3 Bd6 O-O O-O Ne5 Re8 Nc4 Bc5+ Kh1 Ng4 Qf3 Qh4 h3 Nf2+ Kh2 Ng4+ Kh1 Re1 Bd2 Rxa1 Rxa1 Bf5 Re1 h6 Ne5 Re8 Rf1 Nxe5 fxe5 Rxe5 Bf4 Re1 Bxc7 Rxf1+ Qxf1 Bd7 Bh2 Bd4 Qd1 Bc5 Bg1 Bd6 Bh2 Bxh2 Kxh2 Qf4+ Kh1 Qb4 Qd2 Qc4 Qe2 Qc5 Qe4 b5 a3 a5 Qe5 b4 axb4 axb4 Ne4 Qe3', 'clock': '3+0'}, 'puzzle': {'id': 'vtcpD', 'rating': 1298, 'plays': 10831, 'solution': ['e4f6', 'g7f6', 'e5e3'], 'themes': ['endgame', 'master', 'short', 'crushing', 'discoveredAttack'], 'initialPly': 79}}, {'game': {'id': 'mYVoZIhg', 'perf': {'key': 'rapid', 'name': 'Rapid'}, 'rated': True, 'players': [{'name': 'rraj_1411', 'id': 'rraj_1411', 'color': 'white', 'rating': 1933}, {'name': 'alexbes26', 'id': 'alexbes26', 'color': 'black', 'rating': 1861}], 'pgn': 'e4 c5 Bc4 d6 Nf3 Nf6 b3 e6 Bb2 a6 Nc3 b5 Bd3 Bb7 O-O g6 Re1 Bg7 Ng5 O-O e5 dxe5 Rxe5 Nd5 Nf3 Bxe5 Nxe5 Qg5 Ne4 Qe7 Ng4 f5', 'clock': '10+0'}, 'puzzle': {'id': 'qCE4T', 'rating': 1318, 'plays': 2850, 'solution': ['g4h6'], 'themes': ['oneMove', 'mateIn1', 'middlegame'], 'initialPly': 31}}]}
            except requests.JSONDecodeError:
                print("Failed to parse puzzles.")
                print(traceback.format_exc())
                return
        print("Finished getting puzzles.")
        output_puzzles = []
        
        ####################
        # Daily puzzle.
        
        puzzle_board = u_chess.get_board_from_pgn(daily["game"]["pgn"])
        daily_data = {
            "puzzle": {
                "id": "daily",
                "rating": daily["puzzle"]["rating"],
                "themes": daily["puzzle"]["themes"],
                "fen": puzzle_board.fen(),
                "last_move": puzzle_board.move_stack[-1].uci()
            },
            "bots": {}
        }
        print("Daily puzzle:")
        for bot_name, bot in u_chess.get_bot_list().items():
            print(f"Running {bot_name}...")
            daily_data["bots"][bot_name] = u_chess.run_puzzle(
                bot = bot,
                pgn = daily["game"]["pgn"],
                solution = daily["puzzle"]["solution"]
            )
            print("Done.")
        output_puzzles.append(daily_data)
            
        ####################
        # Bulk puzzles.
        
        for index, puzzle in enumerate(bulk["puzzles"]):
            puzzle_board = u_chess.get_board_from_pgn(puzzle["game"]["pgn"])
            puzzle_results = {
                "puzzle": {
                    "id": puzzle["puzzle"]["id"],
                    "rating": puzzle["puzzle"]["rating"],
                    "themes": puzzle["puzzle"]["themes"],
                    "fen": puzzle_board.fen(),
                    "last_move": puzzle_board.move_stack[-1].uci()
                },
                "bots": {}
            }
            print(f"{index+1}/{len(bulk['puzzles'])} | Puzzle {puzzle['puzzle']['id']}:")
            for bot_name, bot in u_chess.get_bot_list().items():
                print(f"Running {bot_name}...")
                puzzle_results["bots"][bot_name] = u_chess.run_puzzle(
                    bot = bot,
                    pgn = puzzle["game"]["pgn"],
                    solution = puzzle["puzzle"]["solution"]
                )
                print("Done.")
            output_puzzles.append(puzzle_results)
            
        database.save("chess", "daily", "puzzles", data=output_puzzles)
        
        print("-- Finished computing puzzles. --")
    
    ##########################################################
    
    async def announce_matches(self: typing.Self) -> None:
        ping_list_channel = await self.bot.fetch_channel(PING_LISTS_CHANNEL) # type: discord.TextChannel

        ping_list = database.get_ping_list("daily_chess_match")
        try:
            ping_list = list(filter(u_interface.Filter_Member_In_Guild(ping_list_channel.guild), ping_list))
        except:
            pass

        # For funzies, shuffle the pinglist order.
        random.shuffle(ping_list)

        pings = "".join(["<@{}>".format(user_id) for user_id in ping_list])

        ###############
        history = u_chess.get_rating_history(database)

        # Account for the fact that the history doesn't have the current elo values.
        history.append(u_chess.get_all_elos(database, return_classes=False))

        current_match = len(history)
        ###############
        
        match_data = database.load("chess", "daily", "matches", default=None)
        
        if match_data is None:
            await ping_list_channel.send(f"{pings}\n\nNo Chess matches today, unfortunately.\nSomething went wrong when computing the matches earlier so I don't have any results to post :(")
            raise ValueError("Match data is None when it should be populated.")
        
        games = match_data["games"]
        bye_bot = match_data["bye"]

        # content = "{pings}\n\nA new series of Chess matches are starting!\nMatch lineup:\n{matches}\n{bye_bot}\n\nYou can use `%chess ping` to join or leave the pinglist!".format(
        content = "{pings}\n\n# Chess match #{number} is starting!\nMatch lineup:\n{matches}\n{bye_bot}\n\nYou can use `%chess ping` to join or leave the pinglist!".format(
            pings = pings,
            number = current_match + 1,
            matches = "\n".join(
                ["- {bot1} vs {bot2}".format(
                    bot1 = u_chess.get_bot(data["white"]).get_name(database),
                    bot2 = u_chess.get_bot(data["black"]).get_name(database)
                ) for data in games]
            ),
            bye_bot = f"Bot that has a bye this round: {u_chess.get_bot(bye_bot).get_name(database)}" if bye_bot is not None else ""
        )

        header_message = await ping_list_channel.send(content) # type: discord.Message

        thread = await header_message.create_thread(
            name = f"{u_chess.get_date()}: Daily Chess matches",
            reason = "Auto-thread creation for the daily Chess game."
        )

        # Copy current ratings to the history.

        history = u_chess.get_rating_history(database)
        ratings = u_chess.get_all_elos(database, return_classes=False)

        history.append(ratings)

        database.save("chess", "rating_history", data = history)

        ######################################

        elo_delta = {}

        for game_data in games:
            game_white = u_chess.get_bot(game_data["white"])
            game_black = u_chess.get_bot(game_data["black"])

            white_elo = game_white.get_elo(database)
            black_elo = game_black.get_elo(database)

            if game_data["winner"] is None:
                outcome = 3
            elif game_data["winner"]:
                outcome = 1
            else:
                outcome = 2

            new_white_elo, new_black_elo = u_chess.handle_match_outcome(
                database = database,
                bot_1 = game_white,
                bot_2 = game_black,
                outcome = outcome
            )

            white_elo_difference = new_white_elo - white_elo
            black_elo_difference = new_black_elo - black_elo

            game_data["white_elo"] = round(new_white_elo)
            game_data["black_elo"] = round(new_black_elo)
            game_data["delta_white_elo"] = round(white_elo_difference)
            game_data["delta_black_elo"] = round(black_elo_difference)

            elo_delta[game_white.name] = round(white_elo_difference)
            elo_delta[game_black.name] = round(black_elo_difference)

            try:
                u_images.chess_match(
                    bot_white = game_white.name,
                    bot_black = game_black.name,
                    game_data = game_data
                )
                send_file = discord.File("images/generated/chess_match.png")
                send_file_link = "attachment://chess_match.png"
            except:
                # Oh no! :(
                print(traceback.format_exc())
                send_file = None
                send_file_link = None

            ending_pgn = f"[Event \"{thread.guild.name}\"]\n[Date \"{u_chess.get_date()}\"]\n{game_data['pgn']}"

            embed = u_interface.gen_embed(
                title = "{} ({}) vs. {} ({})".format(
                    game_white.formatted_name(),
                    round(white_elo),
                    game_black.formatted_name(),
                    round(black_elo)
                ),
                description = f"Ending PGN:```{ending_pgn}```",
                image_link = send_file_link
            )

            if send_file is not None:
                send_files = [send_file]
            else:
                send_files = []

            if len(embed.description) > 4000:
                # Uh oh.
                embed.description = "*Game lasted too long, see attached file.*"

                add = io.StringIO(ending_pgn)

                send_files.append(discord.File(add, filename="chess_game.pgn"))

            await thread.send(embed=embed, files=send_files)
            await asyncio.sleep(0.5)
        
        ##### Sending the leaderboard and graph. #####
        
        ### Generating the leaderboard. ###
        def get_elo_delta(name):
            if name in elo_delta:
                return ("+" if round(elo_delta[name]) >= 0 else "") + u_text.smart_number(round(elo_delta[name]))

            return "*No game played.*"
            
        
        values = [(bot, elo, get_elo_delta(bot.name)) for bot, elo in u_chess.get_all_elos(database).items()]

        sorted_list = sorted(values, key=lambda g: g[1], reverse=True)

        ### Generating the graph. ###
        history = u_chess.get_rating_history(database)

        # Account for the fact that the history doesn't have the current elo values.
        history.append(u_chess.get_all_elos(database, return_classes=False))

        current_match = len(history)
        
        start_match = 0
        end_match = current_match
        bot_list = list(u_chess.get_bot_list().keys())

        lines = []

        for bot in bot_list:
            values = []

            for match_number, match in enumerate(history[start_match:end_match + 1]):
                if bot not in match:
                    continue

                values.append((match_number + start_match, match[bot]))
            
            if len(values) == 0:
                continue

            bot_class = u_chess.get_bot(bot)

            lines.append({
                "label": bot_class.formatted_name(),
                "color": bot_class.get_color_rgb(),
                "values": values
            })
        
        file_name = u_images.generate_graph(
            lines = lines,
            x_label = "Match number",
            y_label = "Bot elo"
        )
        send_file = discord.File(file_name, filename="graph.png")
        send_file_link = "attachment://graph.png"
        
        ### Generating the embed. ###

        embed = u_interface.gen_embed(
            title = "Post-match leaderboard and graph:",
            description = "\n".join(
                [
                    "{place}. {name}: {elo} ({delta})".format(
                        place = placement,
                        name = data[0].name.replace("_", " ").title(),
                        elo = u_text.smart_number(round(data[1])),
                        delta = data[2]
                    )
                    for placement, data in enumerate(sorted_list, start=1)
                ]
            ),
            image_link = send_file_link
        )

        await thread.send(embed=embed, file=send_file)
    
    async def announce_puzzles(self: typing.Self) -> None:
        ping_list_channel = await self.bot.fetch_channel(PING_LISTS_CHANNEL) # type: discord.TextChannel
        
        history = u_chess.get_puzzle_rating_history(database)

        # Account for the fact that the history doesn't have the current elo values.
        history.append(u_chess.get_all_puzzle_elos(database, return_classes=False))

        database.save("chess", "puzzles", "history", data=history)

        current_day = len(history)
        
        ###############
        
        puzzle_data = database.load("chess", "daily", "puzzles", default=None)
        
        if puzzle_data is None:
            await ping_list_channel.send("No puzzle solving today, unfortunately.\nSomething went wrong when running the puzzles earlier so I don't have any results to post :(")
            raise ValueError("Puzzle data is None when it should be populated.")

        content = "# Daily puzzles #{number} is starting!\nToday's puzzles:\n- [Lichess's daily puzzle](<https://lichess.org/training/daily>)\n{other_puzzles}".format(
            number = current_day + 1,
            other_puzzles = "\n".join(
                ["- <https://lichess.org/training/{id}>".format(
                    id = puzzle["puzzle"]["id"]
                ) for puzzle in puzzle_data[1:]]
            )
        )

        header_message = await ping_list_channel.send(content) # type: discord.Message

        thread = await header_message.create_thread(
            name = f"{u_chess.get_date()}: Daily Puzzles",
            reason = "Auto-thread creation for the daily chess puzzle solving."
        )
        
        bot_elos = u_chess.get_all_puzzle_elos(database, return_classes=False)
        pre_puzzle_elos = bot_elos.copy()
        
        bool_to_emoji = ["<:x_:1189696918645907598>", "<:check:1189696905077325894>"]
        
        by_bot_results = {
            bot: []
            for bot in bot_elos
        }
        
        theme_data = u_chess.get_puzzle_theme_data(database)
        overall_data = u_chess.get_puzzle_overall_data(database)
        
        for puzzle in puzzle_data:
            puzzle_elo_data = {}
            
            correct = 0
            
            for bot, data in puzzle["bots"].items():
                if bot in overall_data:
                    overall_data[bot]["total"] += 1
                else:
                    overall_data[bot] = {"total": 1}
                
                new_bot_puzzle_rating = u_chess.new_elo_ratings(bot_elos[bot], puzzle["puzzle"]["rating"], 1 if data["correct"] else 2)[0]
                puzzle_elo_data[bot] = {
                    "elo": round(new_bot_puzzle_rating),
                    "delta": round(new_bot_puzzle_rating - bot_elos[bot])
                }
                bot_elos[bot] = new_bot_puzzle_rating
                
                if data["correct"]:
                    correct += 1
                    
                    if "correct" in overall_data[bot]:
                        overall_data[bot]["correct"] += 1
                    else:
                        overall_data[bot]["correct"] = 1
                    
                for theme in puzzle["puzzle"]["themes"]:
                    if bot not in theme_data:
                        theme_data[bot] = {}
                        
                    if theme in theme_data[bot]:
                        theme_data[bot][theme]["total"] += 1
                        if correct:
                            theme_data[bot][theme]["correct"] += 1
                    else:
                        theme_data[bot][theme] = {
                            "total": 1,
                            "correct": int(data["correct"])
                        }
                    
                by_bot_results[bot].append(bool_to_emoji[data["correct"]])
            
            u_images.chess_puzzle(puzzle, puzzle_elo_data)
            send_file = discord.File("images/generated/chess_puzzle.png")
            send_file_link = "attachment://chess_puzzle.png"
            
            embed = u_interface.gen_embed(
                title = f"Puzzle {puzzle['puzzle']['id']:}",
                description = f"Puzzle rating: ||{u_text.smart_number(puzzle['puzzle']['rating'])}||\nSuccess rate: ||{correct}/{len(puzzle['bots'])} ({round(correct/len(puzzle['bots']) * 100, 2)}%)||" \
                    + f"\nThemes: ||\n- " + "\n- ".join(puzzle["puzzle"]["themes"]) + "||",
                image_link = send_file_link,
                title_link = f"https://lichess.org/training/{puzzle['puzzle']['id']}"
            )

            await thread.send(embed=embed, file=send_file)
            await asyncio.sleep(0.5)
            
        database.save("chess", "puzzles", "themes", data=theme_data)
        database.save("chess", "puzzles", "overall", data=overall_data)
        
        for bot, elo in bot_elos.items():
            u_chess.set_bot_puzzle_elo(database, bot, elo)
        
        # Leaderboard and graph time!
        
        graph_data = {
            name: {
                "label": u_chess.get_bot(name).formatted_name(),
                "color": u_chess.get_bot(name).get_color_rgb(),
                "values": []
            }
            for name in bot_elos
        }
        
        history = u_chess.get_puzzle_rating_history(database)
        history.append(bot_elos)
        for day_number, data in enumerate(history):
            for bot, elo in data.items():
                graph_data[bot]["values"].append((day_number, elo))
        
        file_name = u_images.generate_graph(
            lines = list(graph_data.values()),
            x_label = "Day number",
            y_label = "Bot puzzle elo"
        )
        send_file = discord.File(file_name, filename="graph.png")
        send_file_link = "attachment://graph.png"
        
        def make_bot_line(bot: type[u_chess.ChessBot]) -> str:
            return f"1. {u_chess.format_name(bot)}: {u_text.smart_number(round(bot_elos[bot]))} ({'+' if bot_elos[bot] - pre_puzzle_elos[bot] >= 0 else ''}{u_text.smart_number(round(bot_elos[bot] - pre_puzzle_elos[bot]))}. {' '.join(by_bot_results[bot])})"
        
        def _get_elo(bot):
            return u_chess.get_bot_puzzle_elo(database, bot)
        
        embed = u_interface.gen_embed(
            title = "Post-puzzles leaderboard and graph",
            description = "\n".join(map(make_bot_line, sorted(u_chess.get_bot_list(), key=_get_elo, reverse=True))),
            image_link = send_file_link
        )
        
        await thread.send(embed=embed, file=send_file)



        
        
            

        
    ######################################################################################################################################################
    ##### UTILITIES ######################################################################################################################################
    ######################################################################################################################################################

    async def send_board(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            data: dict,
            do_reply: bool = False,
            custom_content: str | None = None
        ) -> discord.Message:
        render_path = u_chess.render_data(data)

        image = "attachment://chess_position.png"
        image_file = discord.File(render_path, filename="chess_position.png")

        board = u_chess.get_board_from_dict(data)
        outcome_text = ""
        if board.is_checkmate():
            outcome_text = "# Checkmate!"
        elif board.is_stalemate():
            outcome_text = "# Stalemate."
        elif board.is_insufficient_material():
            outcome_text = "# Draw by insufficient material."
        elif board.is_fifty_moves():
            outcome_text = "# Draw by the fifty move rule."
        elif board.is_fivefold_repetition():
            outcome_text = "# Draw by fivefold repitition."

        embed = u_interface.gen_embed(
            title = "Chess game",
            description = f"{outcome_text}\n```{u_chess.get_pgn(ctx.guild, data)}```",
            image_link = image
        )

        if do_reply:
            return await ctx.reply(custom_content, embed=embed, file=image_file)
        else:
            return await ctx.send(custom_content, embed=embed, file=image_file)
    
    def make_bot_move(
            self: typing.Self,
            data: dict
        ) -> dict:
        board = u_chess.get_board_from_dict(data)

        if board.outcome() is not None:
            return data
        
        player = data["player_side"] == "white"

        # If it's currently the player's turn, just skip it.
        if player == board.turn:
            return data
        
        bot_class = u_chess.get_bot(data["bot_name"])

        bot_data = data.get("bot_data", {})
        bot = bot_class(bot_data)

        save_data = bot.save()

        if isinstance(save_data, dict):
            data["bot_data"] = save_data

        move = bot.turn(board=copy.deepcopy(board))
        san = board.san_and_push(move)

        data["moves"].append(san)

        return data

        



        
        
            

        
    ######################################################################################################################################################
    ##### CHESS ##########################################################################################################################################
    ######################################################################################################################################################
        
    @commands.group(
        name = "chess",
        brief = "Play Chess against bots!",
        description = "You can play Chess against bots!\n\nUse `%chess setup` to make a new game in the channel you're in."
    )
    async def chess(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        if ctx.invoked_subcommand is not None:
            return
        
        await ctx.send_help(self.chess)


        
        
            

        
    ######################################################################################################################################################
    ##### CHESS BOARD ####################################################################################################################################
    ######################################################################################################################################################
        
    @chess.command(
        name = "board",
        brief = "View the current board.",
        description = "View the current board."
    )
    async def chess_board(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        if ctx.invoked_subcommand is not None:
            return
        
        current_data = u_chess.get_game(database, ctx.channel)

        if current_data is None:
            await ctx.reply("There's no game here!\nUse `%chess setup` to make a new game!")
            return
        
        await self.send_board(
            ctx = ctx,
            data = current_data,
            do_reply = True
        )

        


        
        
            

        
    ######################################################################################################################################################
    ##### CHESS SETUP ####################################################################################################################################
    ######################################################################################################################################################
        
    @chess.command(
        name = "setup",
        brief = "Setup a new Chess game.",
        description = "Setup a new Chess game."
    )
    async def chess_setup(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            bot_name: typing.Optional[str] = commands.parameter(description = "The name of the bot to play against."),
            side: typing.Optional[typing.Literal['white', 'black']] = commands.parameter(description = "Optional side to play as, 'white' or 'black'. Defaults to random."),
            *, fen: typing.Optional[str] = commands.parameter(description = "Optional custom FEN string.")
        ):
        bot_class = u_chess.get_bot(bot_name)

        if bot_class is None:
            bot_list = u_chess.get_bot_list()

            embed = u_interface.gen_embed(
                title = "Chess setup",
                description = "To play against a bot, use `%chess setup <bot name> <side> <fen>` (the side and fen string are optional.)\n\nAvailable bot list: {}".format(
                    ", ".join([f'`{b}`' for b in bot_list.keys()])
                )
            )
            await ctx.reply(embed=embed)
            return
        
        if str(side).lower() in ["white", "black"]:
            side = side.lower()
        else:
            side = random.choice(["white", "black"])

        if fen is None:
            fen = chess.STARTING_FEN
        else:
            try:
                chess.Board(fen)
            except ValueError:
                await ctx.reply("That FEN string doesn't appear to work.")
                return
            
        new_data = u_chess.make_game(
            initial_player = ctx.author,
            player_side = side,
            bot = bot_class,
            starting_fen = fen
        )

        new_data = self.make_bot_move(new_data)

        # Setup the new game.
        u_chess.update_game(
            database=database,
            channel=ctx.channel,
            data = new_data
        )  
        
        await self.send_board(
            ctx = ctx,
            data = new_data,
            do_reply = True
        )

        


        
        
            

        
    ######################################################################################################################################################
    ##### CHESS MOVE #####################################################################################################################################
    ######################################################################################################################################################
        
    @chess.command(
        name = "move",
        brief = "Make a move in the Chess game.",
        description = "Make a move in the Chess game."
    )
    async def chess_move(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            move: typing.Optional[str] = commands.parameter(description = "The move you want to make in algebraic Chess notation.")
        ):
        current_data = u_chess.get_game(database, ctx.channel)

        if current_data is None:
            await ctx.reply("There's no game here!\nUse `%chess setup` to make a new game!")
            return
        
        board = u_chess.get_board_from_dict(current_data)

        if board.outcome() is not None:
            await ctx.reply("This game has already ended. Use `%chess setup` to make a new game.")
            return
        
        try:
            move = board.parse_san(move)
            move = board.san_and_push(move)
        except chess.InvalidMoveError:
            await ctx.reply("I am sorry, but that is an invalid move.")
            return
        except chess.IllegalMoveError:
            await ctx.reply("I am sorry, but that is an illegal move.")
            return
        except chess.AmbiguousMoveError:
            await ctx.reply("Multiple pieces can go there, please specify which one.")
            return
        
        current_data["moves"].append(move)
        current_data["last_move"] = int(time.time())

        if ctx.author.id not in current_data["players"]:
            current_data["players"].append(ctx.author.id)
        
        try:
            await ctx.message.add_reaction("✅")
        except:
            pass

        current_data = self.make_bot_move(current_data)
        
        u_chess.update_game(
            database = database,
            channel = ctx.channel,
            data = current_data
        )
        
        await self.send_board(
            ctx = ctx,
            data = current_data,
            do_reply = False
        )


        


        
        
            

        
    ######################################################################################################################################################
    ##### CHESS STATS ####################################################################################################################################
    ######################################################################################################################################################
        
    @chess.command(
        name = "stats",
        brief = "Get a bot's stats.",
        description = "Get a bot's stats."
    )
    async def chess_stats(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            bot_name: typing.Optional[str] = commands.parameter(description = "The bot name to get the stats for.")
        ):
        bot_list = u_chess.get_bot_list()

        if bot_name not in bot_list.keys():
            embed = u_interface.gen_embed(
                title = "Chess bot stats",
                description = "To get a bot's stats, use `%chess stats <bot name>`.\n\nAvailable bot list: {}".format(
                    ", ".join([f'`{b}`' for b in bot_list.keys()])
                )
            )
            await ctx.reply(embed=embed)
            return

        func = bot_list[bot_name]

        bot_rating = round(u_chess.get_bot_elo(database, bot_name))
        puzzle_rating = round(u_chess.get_bot_puzzle_elo(database, bot_name))
        
        embed = u_interface.gen_embed(
            title = f"Chess bot {func.name.title()}",
            description = f"*Created by {func.creator}*\nRating: {u_text.smart_number(bot_rating)}\nPuzzle rating: {u_text.smart_number(puzzle_rating)}\n\n{func.description}",
            footer_text = f"Use '{ctx.prefix}chess puzzle stats {bot_name}' to get the bot's puzzle stats!"
        )

        await ctx.reply(embed=embed)


        


        
        
            

        
    ######################################################################################################################################################
    ##### CHESS PING #####################################################################################################################################
    ######################################################################################################################################################
        
    @chess.command(
        name = "ping",
        brief = "Join or leave the Chess game ping list.",
        description = "Join or leave the Chess game ping list."
    )
    async def chess_ping(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            state: typing.Optional[str] = commands.parameter(description = "'on' to join the ping list, 'off' to leave.")
        ):
        new_state = False

        if state in ["on", "off"]:
            new_state = state == "on"
        else:
            on_pinglist = database.user_on_ping_list("daily_chess_match", ctx.author.id)

            new_state = not on_pinglist

        database.update_ping_list("daily_chess_match", ctx.author.id, new_state)

        embed = u_interface.gen_embed(
            title = "Daily Chess match ping list",
            description = "You will {} be pinged for future daily chess matches.".format("now" if new_state else "no longer")
        )
        await ctx.reply(embed=embed)


        


        
        
            

        
    ######################################################################################################################################################
    ##### CHESS LEADERBOARD ##############################################################################################################################
    ######################################################################################################################################################
        
    @chess.command(
        name = "leaderboard",
        brief = "Chess bot leaderboard.",
        description = "Chess bot leaderboard.",
        aliases = ["lb"]
    )
    async def chess_leaderboard(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            highlight: typing.Optional[u_chess.ChessBotConverter] = commands.parameter(description = "Optional name of a bot to highlight.")
        ):
        values = tuple(u_chess.get_all_elos(database).items())

        sorted_list = sorted(values, key=lambda g: g[1], reverse=True)

        highlight_point = -5

        if highlight is not None:
            highlight = highlight.name
            highlight_point = [index for index, item in enumerate(sorted_list) if item[0].name == highlight][0]
        
        lines = []
        
        previous = -1
        bots_shown = 0
        for index, data in enumerate(sorted_list):
            if not(index <= 9 or abs(index - highlight_point) <= 2):
                continue

            if abs(index - previous) >= 2:
                lines.append("")

            previous = index

            name, value = data

            highlight_text = ""
            if name.name == highlight:
                highlight_text = "**"
            
            title = name.name.replace("_", " ").title()

            lines.append("{}. {}{}: {}{}".format(index + 1, highlight_text, title, u_text.smart_number(round(value)), highlight_text))

            bots_shown += 1
        
        embed = u_interface.gen_embed(
            title = f"Chess bot leaderboard:",
            description = "*Showing {} of {} bots.*".format(bots_shown, len(sorted_list)),
            fields = [
                ("", "\n".join(lines), False)
            ],
            footer_text = "You can use '%chess lb <name>' to highlight a specific bot."
        )
        await ctx.reply(embed=embed)


        


        
        
            

        
    ######################################################################################################################################################
    ##### CHESS GRAPH ####################################################################################################################################
    ######################################################################################################################################################
        
    @chess.command(
        name = "graph",
        brief = "Graph the bot elos.",
        description = """Graph the bot elos.
        
Parameters:
- The bots you want to use, replace any spaces with underscores. You can also use 'all' to use all the bots. Putting an exclamation mark before a bot name will remove it. If none are provided it will use them all.
- To mark the start of the graph, use '-start <start point>'. If none is provided it will use 0.
- To mark the end, '-end <end point>'. If none is provided it will use the latest ratings.
- '-puzzle' can be used to get the puzzle elo graph instead of the regular elo one.
- '-log' can be used to set the Y axis to a log scale.
- `-min <minimum>` can be used to set a minimum elo, so bots with a lower elo won't be displayed. This is the bot's *current* elo, so the bot's elo may have been outside this range at some point.
- Likewise, `-max <maximum>` is the opposite, and will set a maximum elo for displayed bots.
- `-around <center> <size>` will display only bots with an elo within `size` from `center`. For example, `-around 800 20` will display only bots within 20 elo points of 800, this would be the same as `-min 780 -max 820`. Using `-min` or `-max` after this in the command will overwrite it."""
    )
    async def chess_graph(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            *, parameters: typing.Optional[str] = commands.parameter(description = "The parameters to use. See above for more information.")
        ):
        history = u_chess.get_rating_history(database)

        # Account for the fact that the history doesn't have the current elo values.
        history.append(u_chess.get_all_elos(database, return_classes=False))

        current_match = len(history)
        all_bots = list(u_chess.get_bot_list().keys())

        log_scale = False
        start_match = 0
        end_match = current_match
        use_puzzles = False
        bot_list = []

        elo_min = float("-inf")
        elo_max = float("inf")
        
        if parameters is None:
            bot_list = all_bots
        else:
            parameters = parameters.split(" ")

            negated = []

            for param_id, param in enumerate(parameters):
                if param == "all":
                    bot_list = all_bots
                    continue

                if param == "-puzzle" or param == "-puzzles":
                    use_puzzles = True
                    continue
                
                if param == "-log":
                    log_scale = True
                    continue

                if param == "-start":
                    if param_id == len(parameters) - 1:
                        continue
                    
                    if u_converters.is_digit(parameters[param_id + 1]):
                        start_match = u_converters.parse_int(parameters[param_id + 1])

                    continue

                if param == "-end":
                    if param_id == len(parameters) - 1:
                        continue
                    
                    if u_converters.is_digit(parameters[param_id + 1]):
                        end_match = u_converters.parse_int(parameters[param_id + 1])

                    continue

                if param == "-min":
                    if param_id == len(parameters) - 1:
                        continue 
                    
                    if u_converters.is_digit(parameters[param_id + 1]):
                        elo_min = u_converters.parse_int(parameters[param_id + 1])

                    continue

                if param == "-max":
                    if param_id == len(parameters) - 1:
                        continue 
                    
                    if u_converters.is_digit(parameters[param_id + 1]):
                        elo_max = u_converters.parse_int(parameters[param_id + 1])

                    continue

                if param == "-around":
                    if param_id >= len(parameters) - 2:
                        continue 
                    
                    if u_converters.is_digit(parameters[param_id + 1]) and u_converters.is_digit(parameters[param_id + 2]):
                        center = u_converters.parse_int(parameters[param_id + 1])
                        size = u_converters.parse_int(parameters[param_id + 2])

                        elo_max = center + size
                        elo_min = center - size

                    continue
                
                if param.startswith("!"):
                    param = param.replace("!", "", 1)
                    modify = negated # Set "modify" to a reference to "negated".
                else:
                    modify = bot_list # Set "modify" to a reference to "bot_list".

                get_item = u_chess.get_bot(param)

                if get_item:
                    if get_item not in modify:
                        modify.append(get_item.name)
                    continue
            
            if len(bot_list) == 0:
                bot_list = all_bots
            
            for bot in negated:
                if bot in bot_list:
                    bot_list.remove(bot)
        
        if use_puzzles:
            history = u_chess.get_puzzle_rating_history(database)

            # Account for the fact that the history doesn't have the current elo values.
            history.append(u_chess.get_all_puzzle_elos(database, return_classes=False))
            
            if end_match == current_match:
                current_match = len(history)
                end_match = current_match
            else:
                current_match = len(history)
            
        
        if end_match <= start_match:
            await ctx.reply("The start must be before the end.")
            return
        
        start_match = max(start_match, 0)
        end_match = min(end_match, current_match)

        lines = []

        for bot in bot_list:
            bot_class = u_chess.get_bot(bot)

            # If the elo is outside the given range skip this bot.
            if not (elo_min <= bot_class.get_elo(database) <= elo_max):
                continue

            values = []

            for match_number, match in enumerate(history[start_match:end_match + 1]):
                if bot not in match:
                    continue

                values.append((match_number + start_match, match[bot]))
            
            if len(values) == 0:
                continue


            lines.append({
                "label": bot_class.formatted_name(),
                "color": bot_class.get_color_rgb(),
                "values": values
            })
        
        # If lines is empty this will trigger.
        if not lines:
            await ctx.reply("The given constraints result in no bots on the graph.")
            return
        
        file_name = u_images.generate_graph(
            lines = lines,
            x_label = "Day number" if use_puzzles else "Match number",
            y_label = "Bot puzzle elo" if use_puzzles else "Bot elo",
            log_scale = log_scale
        )

        await ctx.reply(file=discord.File(file_name))


        


        
        
            

        
    ######################################################################################################################################################
    ##### CHESS PUZZLE ###################################################################################################################################
    ######################################################################################################################################################
        
    @chess.group(
        name = "puzzle",
        brief = "Chess bot puzzle solving.",
        description = "Chess bot puzzle solving.",
        aliases = ["puzzles"]
    )
    async def chess_puzzle(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
        ):
        if ctx.invoked_subcommand is not None:
            return
        
        await ctx.send_help(self.chess_puzzle)


        


        
        
            

        
    ######################################################################################################################################################
    ##### CHESS PUZZLE GRAPH #############################################################################################################################
    ######################################################################################################################################################
        
    @chess_puzzle.command(
        name = "graph",
        brief = "Graph the bot puzzle elos.",
        description = """Graph the bot elos.
        
Parameters:
- The bots you want to use, replace any spaces with underscores. You can also use 'all' to use all the bots. Putting an exclamation mark before a bot name will remove it. If none are provided it will use them all.
- To mark the start of the graph, use '-start <start point>'. If none is provided it will use 0.
- To mark the end, '-end <end point>'. If none is provided it will use the latest ratings.
- '-log' can be used to set the Y axis to a log scale.
- `-min <minimum>` can be used to set a minimum elo, so bots with a lower elo won't be displayed. This is the bot's *current* elo, so the bot's elo may have been outside this range at some point.
- Likewise, `-max <maximum>` is the opposite, and will set a maximum elo for displayed bots.
- `-around <center> <size>` will display only bots with an elo within `size` from `center`. For example, `-around 800 20` will display only bots within 20 elo points of 800, this would be the same as `-min 780 -max 820`. Using `-min` or `-max` after this in the command will overwrite it."""
    )
    async def chess_puzzle_graph(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            *, parameters: typing.Optional[str] = commands.parameter(description = "The parameters to use. See above for more information.")
        ):
        if parameters is None:
            parameters = ""
        await self.chess_graph(
            ctx,
            parameters = parameters + " -puzzles"
        )


        


        
        
            

        
    ######################################################################################################################################################
    ##### CHESS PUZZLE STATS #############################################################################################################################
    ######################################################################################################################################################
        
    @chess_puzzle.command(
        name = "stats",
        brief = "Get a bot's puzzle stats.",
        description = "Get a bot's puzzle stats."
    )
    async def chess_puzzle_stats(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            bot_name: typing.Optional[str] = commands.parameter(description = "The bot name to get the stats for.")
        ):
        bot_list = u_chess.get_bot_list()

        if bot_name not in bot_list.keys():
            embed = u_interface.gen_embed(
                title = "Chess bot puzzle stats",
                description = "To get a bot's puzzle stats, use `{}chess puzzle stats <bot name>`.\n\nAvailable bot list: {}".format(
                    ctx.prefix,
                    ", ".join([f'`{b}`' for b in bot_list.keys()])
                )
            )
            await ctx.reply(embed=embed)
            return
        
        func = bot_list[bot_name]

        bot_rating = round(u_chess.get_bot_elo(database, bot_name))
        puzzle_rating = round(u_chess.get_bot_puzzle_elo(database, bot_name))
        
        overall_data = u_chess.get_puzzle_overall_data(database)
        overall_data = overall_data.get(func.name, {"total": 0, "correct": 0})
        
        total_attempted = overall_data["total"]
        solved_correctly = overall_data["correct"]
        
        if total_attempted == 0:
            percentage_text = "???%"
        else:
            percentage_text = f"{round(solved_correctly / total_attempted * 100, 2)}%"
            
        raw_theme_info = u_chess.get_puzzle_theme_data(database)
        theme_info = []
        
        for theme, data in raw_theme_info.get(func.name).items():
            theme_info.append((theme, data.get("total", 0), data.get("correct", 0)))
            
        theme_info.sort(key=lambda d: d[2]/d[1], reverse=True)
        
        embed = u_interface.gen_embed(
            title = f"{func.formatted_name()}'s puzzle stats:",
            description = f"*Created by {func.creator}*\nRating: {u_text.smart_number(bot_rating)}\nPuzzle rating: {u_text.smart_number(puzzle_rating)}\n\nTotal puzzles attempted: {total_attempted}\nCorrectly solved: {solved_correctly}\nSuccess rate: {percentage_text}",
            fields = [(
                "Theme performance:",
                "\n".join(f"- {name} {correct}/{total} ({round(correct/total*100, 2)}%)" for name, total, correct in theme_info),
                False
            )],
            footer_text = f"Use '{ctx.prefix}chess stats {func.name}' to get the bot's overall Chess stats!"
        )
        
        await ctx.reply(embed=embed)


        


        
        
            

        
    ######################################################################################################################################################
    ##### CHESS COMPUTE ALL ##############################################################################################################################
    ######################################################################################################################################################
        
    @chess.command(
        name = "compute_all",
        brief = "Computes all the daily chess things and saves them.",
        description = "Computes all the daily chess things and saves them.\nUse `%chess announce_all` to announce the results."
    )
    @commands.is_owner()
    async def chess_compute_all(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        self.run_computations()
            
        await ctx.reply("Done.")


        


        
        
            

        
    ######################################################################################################################################################
    ##### CHESS COMPUTE MATCHES ##########################################################################################################################
    ######################################################################################################################################################
        
    @chess.command(
        name = "compute_matches",
        brief = "Computes the daily Chess matches and saves them.",
        description = "Computes the daily Chess matches and saves them.\nUse `%chess announce_matches` to announce the results."
    )
    @commands.is_owner()
    async def chess_compute_matches(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        self.compute_matches()
        await ctx.reply("Done.")


        


        
        
            

        
    ######################################################################################################################################################
    ##### CHESS COMPUTE PUZZLES ##########################################################################################################################
    ######################################################################################################################################################
        
    @chess.command(
        name = "compute_puzzles",
        brief = "Computes the daily Chess puzzles and saves them.",
        description = "Computes the daily Chess puzzles and saves them.\nUse `%chess announce_puzzles` to announce the results."
    )
    @commands.is_owner()
    async def chess_compute_puzzles(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        self.compute_puzzles()
        await ctx.reply("Computing...")


        


        
        
            

        
    ######################################################################################################################################################
    ##### CHESS ANNOUNCE ALL #############################################################################################################################
    ######################################################################################################################################################
        
    @chess.command(
        name = "announce_all",
        brief = "Announces all the daily Chess results.",
        description = "Announces all the daily Chess results.\nUse `%chess compute_all` to compute the data."
    )
    @commands.is_owner()
    async def chess_announce_all(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        await self.announce_matches()
        await self.announce_puzzles()
            
        await ctx.reply("Done.")


        


        
        
            

        
    ######################################################################################################################################################
    ##### CHESS ANNOUNCE MATCHES #########################################################################################################################
    ######################################################################################################################################################
        
    @chess.command(
        name = "announce_matches",
        brief = "Announces the daily Chess matches results.",
        description = "Announces the daily Chess matches results.\nUse `%chess compute_matches` to compute the games."
    )
    @commands.is_owner()
    async def chess_announce_matches(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        await self.announce_matches()
        await ctx.reply("Done.")


        


        
        
            

        
    ######################################################################################################################################################
    ##### CHESS ANNOUNCE PUZZLES #########################################################################################################################
    ######################################################################################################################################################
        
    @chess.command(
        name = "announce_puzzles",
        brief = "Announces the daily Chess puzzle results.",
        description = "Announces the daily Chess puzzle results.\nUse `%chess compute_puzzles` to compute the games."
    )
    @commands.is_owner()
    async def chess_announce_puzzles(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        await self.announce_puzzles()
        await ctx.reply("Done.")


        


        
        
            

        
    ######################################################################################################################################################
    ##### CHESS STATUS ###################################################################################################################################
    ######################################################################################################################################################
        
    @chess.command(
        name = "status",
        brief = "Internal status data regarding the matches and puzzles.",
        description = "Internal status data regarding the matches and puzzles."
    )
    @commands.is_owner()
    async def chess_status(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        daily_data = database.load("chess", "daily", default={})
        
        matches = daily_data.get("matches") is not None
        puzzles = daily_data.get("puzzles") is not None
        
        last_updated = daily_data.get("last_updated")
        
        if last_updated is not None:
            last_updated = f"<t:{int(last_updated)}>"
        
        embed = u_interface.gen_embed(
            title = "Daily chess status",
            description = f"Matches exist: {matches}\nPuzzles exist: {puzzles}\nLast updated: {last_updated}"
        )
        
        await ctx.reply(embed=embed)

        

    
    

async def setup(bot: commands.Bot):
    global database
    database = bot.database
    
    cog = Chess_cog()
    cog.bot = bot

    # Add attributes for sys.modules and globals() so the _reload_module() function in utility.custom can read it and get the module objects.
    cog.modules = sys.modules
    cog.globals = globals()
    
    await bot.add_cog(cog)
