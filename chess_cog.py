"""This cog is for the commands that allow for playing Chess against bots."""

from discord.ext import commands
import discord
import typing
import time
import random
import copy
import traceback
import io

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

PING_LISTS_CHANNEL = 1060344552818483230

class Chess_cog(
        u_custom.CustomCog,
        name="Chess",
        description="You can play Chess here against various bots!\nTo play Chess against other humans, use Machine-Mind."
    ):

    async def hourly_task(self: typing.Self):
        """Code that runs for every hour."""
        bread_time = u_bread.bst_time()

        # If it's not the correct time (noon in EDT,) then stop here.
        if bread_time != 18:
            return
        
        # If it's here, then time to play a game of Chess!
        game_data = u_chess.determine_matches(database)

        if game_data[-1][1] is None:
            bye_bot = game_data.pop(-1)[0]
        else:
            bye_bot = None
        
        games = [
            {
                "white": white,
                "black": black
            }
            for white, black in game_data
        ]

        ping_list_channel = await self.bot.fetch_channel(PING_LISTS_CHANNEL) # type: discord.TextChannel

        ping_list = database.get_ping_list("daily_chess_match")
        try:
            ping_list = filter(u_interface.Filter_Member_In_Guild(ping_list_channel.guild), ping_list)
        except:
            pass

        # For funzies, shuffle the pinglist order.
        random.shuffle(ping_list)

        pings = "".join(["<@{}>".format(user_id) for user_id in ping_list])
        content = "{pings}\n\nA new series of Chess matches are starting!\nMatch lineup:\n{matches}\n{bye_bot}\n\nYou can use `%chess ping` to join or leave the pinglist!".format(
            pings = pings,
            matches = "\n".join(
                ["- {bot1} vs {bot2}".format(
                    bot1 = data["white"].get_name(database),
                    bot2 = data["black"].get_name(database)
                ) for data in games]
            ),
            bye_bot = f"Bot that has a bye this round: {bye_bot.get_name(database)}" if bye_bot is not None else ""
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


        for data in games:
            game_white = data["white"]
            game_black = data["black"]

            game_data = u_chess.run_match(
                white = game_white,
                black = game_black
            )
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
                    data["white"].formatted_name(),
                    round(white_elo),
                    data["black"].formatted_name(),
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
        
        ##### Sending the leaderboard and graph. #####
        
        ### Generating the leaderboard. ###
        values = tuple(u_chess.get_all_elos(database).items())

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
                    "{place}. {name}: {elo}".format(
                        place = placement,
                        name = data[0].name.replace("_", " ").title(),
                        elo = u_text.smart_number(round(data[1]))
                    )
                    for placement, data in enumerate(sorted_list, start=1)
                ]
            ),
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
        
        embed = u_interface.gen_embed(
            title = f"Chess bot {func.name.title()}",
            description = f"*Created by {func.creator}*\nRating: {bot_rating}\n\n{func.description}"
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
            x_label = "Match number",
            y_label = "Bot elo",
            log_scale = log_scale
        )

        await ctx.reply(file=discord.File(file_name))


        


        
        
            

        
    ######################################################################################################################################################
    ##### CHESS RUN MATCHES ##############################################################################################################################
    ######################################################################################################################################################
        
    @chess.command(
        name = "run_matches",
        brief = "Runs the daily Chess matches.",
        description = "Runs the daily Chess matches."
    )
    @commands.is_owner()
    async def chess_run_matches(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        await self.hourly_task()

        

    
    

async def setup(bot: commands.Bot):
    global database
    database = bot.database
    
    cog = Chess_cog()
    cog.bot = bot

    # Add attributes for sys.modules and globals() so the _reload_module() function in utility.custom can read it and get the module objects.
    cog.modules = sys.modules
    cog.globals = globals()
    
    await bot.add_cog(cog)
