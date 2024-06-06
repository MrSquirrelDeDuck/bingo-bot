"""This cog is for the commands that allow for playing Chess against bots."""

from discord.ext import commands
import discord
import typing
import time
import random
import copy
import traceback

# pip install chess
import chess

import sys

import utility.bread as u_bread
import utility.files as u_files
import utility.custom as u_custom
import utility.chess_utils as u_chess
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
        all_bots = list(u_chess.get_bot_list().values())

        games = []

        for game_index in range(len(all_bots) // 2):
            game_white = random.choice(all_bots)
            all_bots.remove(game_white)

            game_black = random.choice(all_bots)
            all_bots.remove(game_black)

            games.append({
                "white": game_white,
                "black": game_black
            })
        
        bye_bot = None
        if len(all_bots) != 0:
            bye_bot = all_bots[0]

        ping_list_channel = await self.bot.fetch_channel(PING_LISTS_CHANNEL)

        ping_list = database.get_ping_list("daily_chess_match")

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

            embed = u_interface.gen_embed(
                title = "{} ({}) vs. {} ({})".format(
                    data["white"].formatted_name(),
                    round(white_elo),
                    data["black"].formatted_name(),
                    round(black_elo)
                ),
                description = f"Ending PGN:```[Event \"{thread.guild.name}\"]\n[Date \"{u_chess.get_date()}\"]\n{game_data['pgn']}```",
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
        all_bots = u_chess.get_bot_list()

        values = []
        for bot in all_bots.values():
            values.append((bot, round(bot.get_elo(database))))

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

            lines.append("{}. {}{}: {}{}".format(index + 1, highlight_text, title, u_text.smart_number(value), highlight_text))

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

        

    
    

async def setup(bot: commands.Bot):
    global database
    database = bot.database
    
    cog = Chess_cog()
    cog.bot = bot

    # Add attributes for sys.modules and globals() so the _reload_module() function in utility.custom can read it and get the module objects.
    cog.modules = sys.modules
    cog.globals = globals()
    
    await bot.add_cog(cog)
