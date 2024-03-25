"""This cog is for game related utility commands, and commands that are games themselves."""
from __future__ import annotations

from discord.ext import commands
import discord
import typing
import random
import re
import time
import traceback
import asyncio
import copy
import os

import sys

import utility.files as u_files
import utility.custom as u_custom
import utility.interface as u_interface
import utility.checks as u_checks
import utility.text as u_text
import utility.images as u_images
import utility.converters as u_converters

database = None # type: u_files.DatabaseInterface

card_keys = {
    "back": "<:card_back:1122985559183335435>",
    'c1': '<a:ace_clubs:1122942670793363466>', 'd1': '<a:ace_diamonds:1122943540549386360>', 'h1': '<a:ace_hearts:1122943541379874838>', 's1': '<a:ace_spades:1122943543472820285>',
    'c2': '<:2_clubs:1122930420158312448>', 'd2': '<:2_diamonds:1122930421043318814>', 'h2': '<:2_hearts:1122930422934945932>', 's2': '<:2_spades:1122930424088379441>',
    'c3': '<:3_clubs:1122930451246481458>', 's3': '<:3_spades:1122930454878769283>', 'h3': '<:3_hearts:1122930454044094484>', 'd3': '<:3_diamonds:1122930452416700548>',
    's4': '<:4_spades:1122930475414065185>', 'h4': '<:4_hearts:1122930474214510703>', 'd4': '<:4_diamonds:1122930471878271198>', 'c4': '<:4_clubs:1122930470653526066>',
    'd5': '<:5_diamonds:1122930499887833160>', 'c5': '<:5_clubs:1122930498860220479>', 'h5': '<:5_hearts:1122930501230006302>', 's5': '<:5_spades:1122930502458953889>',
    'c6': '<:6_clubs:1122930520041455666>', 'd6': '<:6_diamonds:1122930521446567936>', 'h6': '<:6_hearts:1122930523145261167>', 's6': '<:6_spades:1122930524072198154>',
    'c7': '<:7_clubs:1122930541327560752>', 'd7': '<:7_diamonds:1122930543139487814>', 'h7': '<:7_hearts:1122930544087408660>', 's7': '<:7_spades:1122930545043722342>',
    's8': '<:8_spades:1122941690697748510>', 'h8': '<:8_hearts:1122941689271701664>', 'd8': '<:8_diamonds:1122930562777239674>', 'c8': '<:8_clubs:1122930561133072555>',
    's9': '<:9_spades:1122941711438589952>', 'h9': '<:9_hearts:1122941710473904168>', 'd9': '<:9_diamonds:1122941709169463387>', 'c9': '<:9_clubs:1122941708125081762>',
    'c10': '<:10_clubs:1122941731319582720>', 'd10': '<:10_diamonds:1122941732728873041>', 'h10': '<:10_hearts:1122941734461112320>', 's10': '<:10_spades:1122941735190925496>',
    'c11': '<:jack_clubs:1122941753759125525>', 'd11': '<:jack_diamonds:1122941755776569464>', 'h11': '<:jack_hearts:1122941756841926757>', 's11': '<:jack_spades:1122941757856952350>',
    's12': '<:queen_spades:1122941804036239553>', 'h12': '<:queen_hearts:1122941803272884334>', 'd12': '<:queen_diamonds:1122941802442407936>', 'c12': '<:queen_clubs:1122941800722726992>',
    's13': '<:king_spades:1122941784465608724>', 'h13': '<:king_hearts:1123679597188354208>', 'd13': '<:king_diamonds:1122941782028734484>', 'c13': '<:king_clubs:1122941779776381028>'
}
        
class PlayingCard:
    def __init__(
            self: typing.Self,
            card_code: str
        ):
        self.code = card_code
        self.suit = card_code[-1]
        self.value = int(card_code[1:])

        self.emoji = card_keys[card_code]

        if self.value <= 10:
            self.game_value = self.value
        else:
            self.game_value = 10
    
    def __str__(self: typing.Self) -> str:
        return self.emoji
    
    def __repr__(self: typing.Self) -> str:
        return self.emoji

class BlackjackPlayer:
    def __init__(
            self: typing.Self,
            member_id: int,
            wager: int
        ):
        self.member_id = member_id
        self.wager = wager

        self.stopped = False
        self.surrendered = False

        self.ping = f"<@{member_id}>"
        
        self.hand: list[PlayingCard] = []

    @property
    def hand_value(self: typing.Self) -> int:
        total = 0
        ace_count = 0

        for card in self.hand:
            # If it's not an ace.
            if card.value != 1:
                total += card.game_value
                continue # Comment this out to restore the hand summing to the broken state it was early in development lol.

            ace_count += 1
        
        if ace_count >= 1:
            for _ in range(ace_count):
                if total + 11 > 21:
                    total += 1
                else:
                    total += 11
        
        return total
    
    @property
    def hand_value_formatted(self: typing.Self) -> str:
        value = self.hand_value

        if value == 21:
            return "✨ Blackjack! ✨"
        
        return str(value)

    @property
    def soft_hand(self: typing.Self) -> bool:
        total = 0
        ace_count = 0

        for card in self.hand:
            # If it's not an ace.
            if card.value != 1:
                total += card.game_value
                continue # Comment this out to restore the hand summing to the broken state it was early in development lol.

            ace_count += 1
        
        if ace_count >= 1:
            for _ in range(ace_count):
                if total + 11 > 21:
                    total += 1
                else:
                    return True
        
        return False
    
    # double down, surrender, split
    @property
    def allowed(self: typing.Self) -> tuple[bool, bool, bool]:
        double = False
        surrender = False
        split = False

        if len(self.hand) == 2:
            double = True
            surrender = True

            if self.hand[0].game_value == self.hand[1].game_value:
                split = True
        
        return (double, surrender, split)

    @property
    def allowed_list(self: typing.Self) -> str:        
        options = ["hit", "stand"]

        allowed = self.allowed
        if allowed[0]:
            options.append("double")
        if allowed[1]:
            options.append("surrender")
        if allowed[2]:
            options.append("split")

        return options
    
    @property
    def formatted_allowed(self: typing.Self) -> str:
        if self.hand_value == 21:
            return "You have a blackjack, so you automatically stand!"

        if self.hand_value > 21:
            return "Your hand value is over 21 and you bust!"
        
        options = ["hit", "stand"]

        allowed = self.allowed
        if allowed[0]:
            options.append("double")
        if allowed[1]:
            options.append("surrender")
        if allowed[2]:
            options.append("split")

        return "Your options: " + ", ".join(options)

    @property
    def formatted_hand(self: typing.Self) -> str:
        return " ".join([str(card) for card in self.hand])

    def winnings(
        self: typing.Self,
        dealer: BlackjackPlayer
    ) -> int:
        if self.surrendered:
            return self.wager // 2
        
        if self.hand_value > 21:
            return 0
        
        if self.hand_value == 21:
            # Blackjack payout cowculations are confusing at times.
            # Blackjack pays 3 to 2.
            
            if dealer.hand_value != 21:
                return int(self.wager * 1.5)
            
            # If the dealer does have a blackjack.

            if len(self.hand) == 2:
                return int(self.wager * 1.5)

            # If the player does not have a natural blackjack.

            if len(dealer.hand) == 2:
                # If the dealer has a natural blackjack, but the player doesn't.
                return 0
            
            # When in doubt, push.
            return self.wager
        
        if self.hand_value != 21 and self.hand_value == dealer.hand_value:
            return self.wager
        
        if self.hand_value > dealer.hand_value or dealer.hand_value > 21:
            return self.wager * 2
        
        return 0
    
    def add_card(
            self: typing.Self,
            card: PlayingCard
        ) -> None:
        self.hand.append(card)

    def hit(
            self: typing.Self,
            deck: list[PlayingCard]
        ) -> tuple[PlayingCard, list[PlayingCard]]:
        card = deck.pop(0)

        self.add_card(card)

        if self.hand_value >= 21:
            self.stopped = True
        
        return (card, deck)
    
    def stand(
            self: typing.Self
        ) -> None:
        self.stopped = True
        return None
    
    def double_down(
            self: typing.Self,
            deck: list[PlayingCard]
        ) -> tuple[PlayingCard, list[PlayingCard]]:
        self.wager *= 2
        self.stopped = True

        out = self.hit(deck=deck)

        return out
    
    def surrender(
            self: typing.Self
        ) -> None:
        self.stopped = True
        self.surrendered = True
        return None
    
    def split(
            self: typing.Self,
            deck: list[PlayingCard]
        ) -> tuple[BlackjackPlayer, list[PlayingCard]]:

        additional = BlackjackPlayer(
            member_id = self.member_id,
            wager = self.wager
        )

        additional.add_card(self.hand.pop(-1))

        self_card, deck = self.hit(deck=deck)

        additional_card, deck = additional.hit(deck=deck)

        return (additional, deck)
    
    def handle_choice(
            self: typing.Self,
            choice: str,
            deck: list[PlayingCard]
        ) -> dict:
        if choice == "hit":
            card, deck = self.hit(deck=deck)

            return {
                "send": "# You got a {}!\nThat brings your hand's value to {}!\n{}".format(card, self.hand_value_formatted, self.formatted_allowed),
                "deck": deck
            }
        elif choice == "stand":
            self.stand()

            return {
                "send": "# You have chosen to stand.\nYour hand's value is {}!".format(self.hand_value_formatted),
                "deck": deck
            }
        elif choice == "double":
            card, deck = self.double_down(deck=deck)

            if self.hand_value > 21:
                text = self.formatted_allowed
            else:
                text = "As a result from the double down you are forced to stand."

            return {
                "send": "# You got a {}!\nThat brings your hand's value to {}!\n{}".format(card, self.hand_value_formatted, text),
                "deck": deck
            }
        elif choice == "surrender":
            self.surrender()
        
            return {
                "send": "# You have surrendered.",
                "deck": deck
            }
        elif choice == "split":
            add_player, deck = self.split(deck=deck)

            return {
                "add_player": add_player,
                "send": "# You have split your hand into two hands!\nYou also receieved a {}! This results in your hand being worth {}!\n{}".format(self.hand[-1], self.hand_value_formatted, self.formatted_allowed),
                "deck": deck
            }





######################################################################################
##### Truth or dare

class TruthOrDare_Buttons(discord.ui.View):

    def __init__(
            self: typing.Self,
            timeout: float = 3600.0
        ):
        super().__init__(timeout=timeout)
        self.state = None
        self.interaction = None

    @discord.ui.button(
        label='Truth',
        style=discord.ButtonStyle.green
    )
    async def truth(
            self: typing.Self,
            interaction: discord.Interaction,
            button: discord.ui.Button
        ):
        self.state = "truth"
        self.interaction = interaction
        self.stop()

    @discord.ui.button(
        label='Dare',
        style=discord.ButtonStyle.red
    )
    async def dare(
            self: typing.Self,
            interaction: discord.Interaction,
            button: discord.ui.Button
        ):
        self.state = "dare"
        self.interaction = interaction
        self.stop()
        
    @discord.ui.button(
        label='Random',
        style=discord.ButtonStyle.blurple
    )
    async def random(
            self: typing.Self,
            interaction: discord.Interaction,
            button: discord.ui.Button
        ):
        self.state = "random"
        self.interaction = interaction
        self.stop()

class TruthOrDare_Buttons_Disabled(discord.ui.View):
    def __init__(
            self: typing.Self,
            timeout: float = 3600.0
        ):
        super().__init__(timeout=timeout)
        self.state = None
        self.interaction = None

    @discord.ui.button(
        label='Truth',
        style=discord.ButtonStyle.green,
        disabled=True
    )
    async def truth(
            self: typing.Self,
            interaction: discord.Interaction,
            button: discord.ui.Button
        ):
        self.stop()

    @discord.ui.button(
        label='Dare',
        style=discord.ButtonStyle.red,
        disabled=True
    )
    async def dare(
            self: typing.Self,
            interaction: discord.Interaction,
            button: discord.ui.Button
        ):
        self.stop()
        
    @discord.ui.button(
        label='Random',
        style=discord.ButtonStyle.blurple,
        disabled=True
    )
    async def random(
            self: typing.Self,
            interaction: discord.Interaction,
            button: discord.ui.Button
        ):
        self.stop()

async def send_truth_or_dare(
        ctx: commands.Context | u_custom.CustomContext,
        type_input="truth",
        interaction=None
    ):
    prompt_type = None

    if type_input == "random":
        if random.randint(1, 2) == 1:
            type_input = "truth"
            prompt_type = "RANDOM: TRUTH"
        else:
            type_input = "dare"
            prompt_type = "RANDOM: DARE"

    prompts = database.load("truth_or_dare", default=None)

    if prompts is None:
        prompts = {
            "truth": ["What is a better question?"],
            "dare": ["Come up with a better dare."]
        }

        database.save("truth_or_dare", data=prompts)

    options = prompts[type_input]
    if prompt_type is None:
        prompt_type = type_input.upper()

    if interaction is None:
        author = ctx.author
    else:
        author = interaction.user

    embed = u_interface.gen_embed(
        title = random.choice(options),
        footer_text = f"Type: {prompt_type}",
        author_name = f"Requested by {u_interface.get_display_name(author)}",
        author_icon = author.display_avatar
    )

    buttons = TruthOrDare_Buttons()
    
    if interaction is not None:
        try:
            await interaction.response.send_message(embed=embed, view=buttons)
        except:
            await ctx.channel.send(embed=embed, view=buttons)
    else:
        await ctx.channel.send(embed=embed, view=buttons)

    async def clear(message):
        await message.edit(view = TruthOrDare_Buttons_Disabled())

    await buttons.wait()

    if buttons.state == "truth":
        await clear(buttons.interaction.message)
        await send_truth_or_dare(ctx, "truth", interaction=buttons.interaction)
    elif buttons.state == "dare":
        await clear(buttons.interaction.message)
        await send_truth_or_dare(ctx, "dare", interaction=buttons.interaction)
    elif buttons.state == "random":
        await clear(buttons.interaction.message)
        await send_truth_or_dare(ctx, "random", interaction=buttons.interaction)
            
class StoryWritingGamePlayer():
    def __init__(
            self: typing.Self,
            member: discord.Member,
            thread: discord.Thread
        ) -> None:
        self.member = member
        self.thread = thread

class StoryWritingGameBook():
    def __init__(
            self: typing.Self,
            player_order: list[StoryWritingGamePlayer]
        ) -> None:
        self.player_order = player_order

        self.text = []
        self.round_current = 0
        self.round_contributed = False
    
    @property
    def number_of_rounds(self: typing.Self) -> int:
        return len(self.player_order) + 1
    
    @property
    def current_player(self: typing.Self) -> int:
        if self.round_current < len(self.player_order):
            return self.player_order[self.round_current]

        return self.player_order[0]
    
    async def send_message(
            self: typing.Self,
            ending_time: int
        ) -> discord.Message:
        player = self.current_player

        message = player.member.mention
        if len(self.text) == 0:
            message += f"\nIt is time for you to start the story!\nThis round will end <t:{ending_time}:R>\nWhen you're ready, send the entire text of what you've written.\nMake sure to cut your story off mid sentence (with no period at the end), and make sure to use puctuation so I can determine where the sentence ends.\nI'll confirm when the message is recieved."
        elif self.round_current == self.number_of_rounds:
            message += f"\nIt is the final round!\nThis round will end <t:{ending_time}:R>.\nIt's time to end this story, and this is what you're given: ```{u_text.backtick_filter(self.text[-1])}```"
        else:
            message += f"\nNext round!\nThis round will end <t:{ending_time}:R>\nThis is round {self.round_current + 1} of {self.number_of_rounds}.\nYou do not need to cut off a sentence this time, you can bring the story to a close.\nI'll confirm when the message is recieved.\nDo not include the prompt in your message, here's your prompt: ```{u_text.backtick_filter(self.text[-1])}```"
        
        return await player.thread.send(message)




######################################################################################################################################################
##### COMMAND COG ####################################################################################################################################
######################################################################################################################################################

class Games_cog(
        u_custom.CustomCog,
        name="Games",
        description="Game related commands!\n\nSome of these commands are miscellaneous game related utility commands, and some commands are games themselves!"
    ):
    story_game_going = False
    blackjack_going = False

    traitor_game_going = False

    async def waiting_room(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            game_name: str
        ) -> list[typing.Any]:
        players = []
        try:
            
            players.append(ctx.author)

            seconds_to_wait = 60

            end_time = time.time() + seconds_to_wait

            def gen_message(
                    player_list: list[BlackjackPlayer],
                    end_time = int | float
                ) -> str:
                out = f"🟦🟦 {game_name} started! 🟦🟦\n    Current players:"

                for player in player_list:
                    out += "\n- {}".format(player.mention)
                
                out += "\n\nTo join, say \"join\"! The game will start <t:{}:R>.".format(int(end_time))

                return out
            
            announcement_message = await ctx.reply(
                gen_message(
                    player_list=players,
                    end_time = end_time
                )
            )
            
            def ping_list(players: list[discord.Member]) -> str:
                return ", ".join([player.mention for player in players])

            waiting_for_players = True

            def join_check(msg: discord.Message) -> bool:
                if msg.channel.id != ctx.channel.id:
                    return False
                
                if msg.author.id in [player.id for player in players]:
                    return False
                
                if msg.author.bot:
                    return False
                
                if msg.content != "join":
                    return False
                
                return True

            while waiting_for_players:
                try:
                    join_message = await self.bot.wait_for(
                        "message",
                        check = join_check,
                        timeout = end_time - time.time()
                    )

                    players.append(join_message.author)

                    end_time = time.time() + seconds_to_wait

                    await join_message.reply(f"You have joined!\nThe game will start <t:{int(end_time)}:R>")

                    await announcement_message.edit(
                        content = gen_message(
                            player_list=players,
                            end_time=end_time
                        )
                    )
                except asyncio.TimeoutError:
                    waiting_for_players = False
                    await ctx.send("{}\nThe time is up!\nLet the game commence!".format(ping_list(players)))
                    break
        except:
            print(traceback.format_exc())
            pass

        return players
            

    @commands.command(
        name = "games",
        brief = "Lists all the game commands!",
        description = "Would you rather have unlimited bacon but no more video games or games, unlimited games, but no more games?\n\nLists all the game commands!"
    )
    async def game_list(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        await ctx.send_help(self)
            

        
    ######################################################################################################################################################
    ##### TRUTH OR DARE ##################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "truth_or_dare",
        brief = "Truth or dare?",
        description = "Truth or dare?"
    )
    @commands.check(u_checks.hide_from_help)
    async def truth_or_dare(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        await send_truth_or_dare(ctx, "random")
    
    @commands.command(
        name = "truth",
        brief = "The truth part of Truth or Dare.",
        description = "The truth part of Truth or Dare."
    )
    @commands.check(u_checks.hide_from_help)
    async def truth(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        await send_truth_or_dare(ctx, "truth")

    @commands.command(
        name = "dare",
        brief = "The dare part of Truth or Dare.",
        description = "The dare part of Truth or Dare."
    )
    @commands.check(u_checks.hide_from_help)
    async def dare(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        await send_truth_or_dare(ctx, "dare")

        
            

        
    ######################################################################################################################################################
    ##### D&D ############################################################################################################################################
    ######################################################################################################################################################
    
    @commands.group(
        name = "dnd",
        aliases = ["d&d", "DnD", "D&D", "DND"],
        brief = "A few utility commands for D&D.",
        description = "A few utility commands for Dungeons and Dragons.",
        invoke_without_command = True,
        pass_context = True
    )
    @commands.check(u_checks.hide_from_help)
    async def dnd_command(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        if ctx.invoked_subcommand is not None:
            return
        
        await ctx.send_help(self.dnd_command)
    
    @dnd_command.command(
        name = "roll",
        brief = "Roll some dice.",
        description = "Roll some dice."
    )
    async def dnd_roll(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            dice: typing.Optional[str] = commands.parameter(description = "The number of dice and number of sides, like '2d6'.")
        ):
        if dice is None:
            await ctx.reply("You must provide some dice to roll, like `2d6` or `3d4`.")
            return
        
        matched = re.match(r"([\d,]+)d([\d,]+)", dice)

        if matched is None:
            await ctx.reply("You must provide some dice to roll, like `2d6` or `3d4`.")
            return
        
        dice_amount = int(matched.group(1))
        dice_sides = int(matched.group(2))

        if dice_amount == 0:
            await ctx.reply("Oddly enough, rolling 0 dice has a total of 0.")
            return
        
        if dice_sides == 0:
            await ctx.reply("How would a 0-sided die even work?")
            return

        if dice_amount > 1000:
            await ctx.reply("That is an unreasonable amount of dice to roll.")
            return
        
        if dice_sides > 100:
            await ctx.reply("That is an unreasonable amount of sides for a die.")
            return

        rolled = []

        for _ in range(dice_amount):
            rolled.append(random.randint(1, int(dice_sides)))

        roll_distribution = [(i, rolled.count(i)) for i in range(1, int(dice_sides) + 1)]

        image_path = u_images.generate_bar_graph(roll_distribution, x_label="Roll result", y_label="Number of rolls")
        
        embed = u_interface.gen_embed(
            title = "{}d{}".format(dice_amount, dice_sides),
            description = "Total: **{}**\n\n**Roll distribution:**\n{}".format(
                u_text.smart_number(sum(rolled)),
                " | ".join(["{}: {}".format(u_text.smart_number(i), u_text.smart_number(rolled.count(i))) for i in range(1, int(dice_sides) + 1) if i in rolled]),
            ),
            image_link = "attachment://graph.png"
        )
        await ctx.reply(embed=embed, file=discord.File(image_path, filename="graph.png"))
        


        
            

        
    ######################################################################################################################################################
    ##### TRAITOR #######################################################################################################################################
    ######################################################################################################################################################
        
    @commands.command(
        name = "traitor",
        brief = "Starts a game of Traitor.",
        description = "Starts a game of Traitor, a game where one player is the traitor and everyone else is innocent.\nThis will DM players involved whether they are the traitor or not 2 minutes after the game starts."
    )
    @commands.check(u_checks.hide_from_help)
    async def traitor(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        if self.traitor_game_going:
            await ctx.reply("I am sorry, but there is already a game going.")
            return
        
        # Everything is in a big try except to catch any errors and reset self.traitor_game_going so another game can be started.
        try:
            # So new games can't be started.
            self.traitor_game_going = True

            # Setup a few things that will be used later.
            players_participating = [ctx.author]
            last_join_timestamp = time.time()

            # Get the time of the start, so we know how long is 2 minutes after.
            start_time = time.time()

            # Check that's used for bot.wait_for.
            def player_check(message):
                return message.author not in players_participating and message.content == "join" and message.channel == ctx.channel and hasattr(message, "webhook_id") and message.webhook_id is None
            
            # Useful function that generates the initial message, since it's edited whenever a player joins.
            def generate_initial():
                return "You have started a game of Traitor.\nThe game will start 60 seconds after the last player joined.\n\nCurrent players:\n{}\n\nTo join, say \"join\".\nThe game will start <t:{}:R>.".format("\n".join([f"- {user.mention}" for user in players_participating]), round(last_join_timestamp + 60))
            
            # Send the "You've started a game" message.
            initial_message = await ctx.reply(generate_initial())
            
            # Main player join loop.
            print("Starting Tratior Company game.")
            print(f"- {ctx.author} has joined.")
            while True:
                # Catch any timeout errors, which are the indicator that the time is up.
                try:
                    # Wait for a message that passes the check in player_check().
                    message = await self.bot.wait_for('message', check = player_check, timeout = 60.0)

                    # Add the player that just joined to the list of players, and update the timestamp of the last join.
                    players_participating.append(message.author)
                    last_join_timestamp = time.time()
                    print(f"- {message.author} has joined.")
                    
                    # Edit the initial message using generate_initial(), and send a message saying you've joined.
                    await initial_message.edit(content=generate_initial())
                    await message.reply("You have joined the game of Traitor.\nThe game will start <t:{}:R>.".format(round(last_join_timestamp + 60)))
                except asyncio.TimeoutError:
                    # The wait time is up, so break out of the while loop.
                    break
            
            # Get the current time, so we can get
            current_time = time.time()

            # Get the time until 2 minutes after the start.
            time_wait = (start_time + 120) - current_time
            
            # Announce that the game has started, and wait for 120 seconds (2 minutes.)
            print(f"Announcing Traitor Company game, time to wait is {time_wait}.")
            print("Player list:\n- {}".format("\n- ".join([str(user) for user in players_participating])))
            await ctx.send("{}\nThe game is starting!\nYou will recieve your role <t:{}:R>.".format("".join([user.mention for user in players_participating]), round(time_wait + current_time)))
            await asyncio.sleep(round(time_wait))
            print("Time to wait is up.")

            # Setup the messages that will be sent. The index of each item here will line up with the indices of the players in players_participaring.
            # The first item is the message to send, the second item is what to print to the console.
            messages = [
                ("You are a great asset to the company.", "Normal")
            ]
            
            # List of extra roles, formatted as dicts, containing 'data', the tuples like in the `messages` list, and 'chance' which is the percent chance of it being included..
            all_roles = [
                {
                    "data": ("You are a super great asset the company.\nYou are required to make at least 2 trips to the base.", "Super"),
                    "chance": 25
                },
                {
                    "data": ("You are *not* a great asset to the company. <:shock:1026568812507701259>", "Traitor"),
                    "chance": 80
                }
            ]

            # Shuffle list of extra roles, so they'll be included in a random order.
            random.shuffle(all_roles)

            # Go through the roles.
            for role_data in all_roles:
                # If a random number between 1 and 100 is less than or equal to the chance, then it'll be added.
                if random.randint(1, 100) <= role_data["chance"]:
                    # Insert the item in slot 0 of the messages list.
                    messages.insert(0, role_data["data"])

            # 10% chance of shuffling the messages list.
            if random.randint(1, 10) == 1:
                random.shuffle(messages)
            
            # Shuffle players_participating, which will mean it will choose a random person to be the traitor due to the `messages` list.
            random.shuffle(players_participating)

            # Send the messages.
            print("Sending Traitor Company messages:")
            for user_id, user in enumerate(players_participating):
                # Send a message as listed in `messages`. The index of the item in `messages` is capped at the last one.
                message_id = min(user_id, len(messages) - 1)
                print(f"- {user}: {messages[message_id][1]}")
                await user.send(messages[message_id][0])
            
            # Allow another game to be started.
            self.traitor_game_going = False
            return
        except:
            # If something went wrong anywhere in the code, set traitor_game_going to False so another game can start.
            self.traitor_game_going = False
            await ctx.reply("Something went wrong, sorry.")
            print(f"Traitor went wrong :(.\n{traceback.format_exc()}")
    


        
        
            

        
    ######################################################################################################################################################
    ##### CARD ###########################################################################################################################################
    ######################################################################################################################################################
    
    @commands.group(
        name = "card",
        brief = "Pick a card, any card.",
        description = "Pick a card, any card.",
        invoke_without_command = True,
        pass_context = True
    )
    @commands.check(u_checks.hide_from_help)
    async def card_command(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            card: typing.Optional[str] = commands.parameter(description = "The key of the card.")
        ):
        if ctx.invoked_subcommand is not None:
            return
        
        if card not in card_keys:
            await ctx.reply("https://cdn.discordapp.com/attachments/1032117556154204180/1122750787588730890/image.png")
            return
        
        await ctx.reply(card_keys[card])
        
    @card_command.command(
        name = "random",
        brief = "A random card, because why not?",
        description = "A random card, because why not?"
    )
    async def card_random(self, ctx):
        await ctx.reply(card_keys[random.choice(list(card_keys.keys()))])

        
            

        
    ######################################################################################################################################################
    ##### BLACKJACK ######################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "blackjack",
        aliases = ["bradjack"],
        brief = "Blackjack.",
        description = "Blackjack.\n\nTime estimate: 1 to 2 minutes."
    )
    @commands.check(u_checks.hide_from_help)
    async def blackjack(
        self: typing.Self,
        ctx: commands.Context | u_custom.CustomContext,
        wager: typing.Optional[u_converters.parse_int]
    ):
        if self.blackjack_going:
            await ctx.reply("A game of blackjack is currently underway somewhere. Please wait until it's done to try again.")
            return
        
        wager_min = 4
        wager_max = 161660

        if wager is None:
            await ctx.reply("You need to wager at least {} and at most {}.".format(wager_min, u_text.smart_number(wager_max)))
            return
        
        if not (wager_min <= wager <= wager_max):
            await ctx.reply("You need to wager at least {} and at most {}.".format(wager_min, u_text.smart_number(wager_max)))
            return
        
        self.blackjack_going = True

        # The number of seconds to wait between messages.
        delay_time = 1.5

        try:
            players: list[BlackjackPlayer] = []
            
            players.append(BlackjackPlayer(
                member_id = ctx.author.id,
                wager = wager
            ))

            seconds_to_wait = 60

            end_time = time.time() + seconds_to_wait

            def gen_message(
                    player_list: list[BlackjackPlayer],
                    end_time = int | float
                ) -> str:
                out = "🟦🟦 Blackjack game started! 🟦🟦\n    Current players:"

                for player in player_list:
                    out += "\n- {}: wagering {}".format(player.ping, u_text.smart_number(player.wager))
                
                out += "\n\nTo join, say \"join <wager>\" where the wager is between {} and {}. The game will start <t:{}:R>.".format(wager_min, u_text.smart_number(wager_max), int(end_time))

                return out
            
            announcement_message = await ctx.reply(
                gen_message(
                    player_list=players,
                    end_time = end_time
                )
            )

            waiting_for_players = True

            join_pattern = re.compile("join ([\d,]+)$")

            def join_check(msg: discord.Message) -> bool:
                if msg.channel.id != ctx.channel.id:
                    return False
                
                if msg.author.id in [player.member_id for player in players]:
                    return False
                
                if msg.author.bot:
                    return False

                matched = join_pattern.match(msg.content)
                if matched is None:
                    return False
                
                wager = u_text.return_numeric(matched.group(1))

                if not (wager_min <= wager <= wager_max):
                    return False
                
                return True
            
            def ping_list(player_list: list[BlackjackPlayer]) -> str:
                return ", ".join([player.ping for player in player_list])

            while waiting_for_players:
                try:
                    join_message = await self.bot.wait_for(
                        "message",
                        check = join_check,
                        timeout = end_time - time.time()
                    )

                    wager = u_text.return_numeric(join_message.content)

                    players.append(BlackjackPlayer(
                        member_id = join_message.author.id,
                        wager = wager
                    ))

                    end_time = time.time() + seconds_to_wait

                    await join_message.reply(f"You have joined with a wager of {u_text.smart_number(wager)}!\nThe game will start <t:{int(end_time)}:R>")

                    await announcement_message.edit(
                        content = gen_message(
                            player_list=players,
                            end_time=end_time
                        )
                    )
                except asyncio.TimeoutError:
                    waiting_for_players = False
                    await ctx.send("{}\nThe time is up!\nLet the game commence!".format(ping_list(players)))
                    break
            
            ##### Setup the deck. #####
                
            deck = []

            deck_count = 6

            for _ in range(deck_count):
                for suit in ["s", "h", "d", "c"]:
                    for value in range(1, 14):
                        deck.append(PlayingCard(
                            card_code = f"{suit}{value}"
                        ))

            # Only eight of spades. Be careful, this can break it if enough people split.
            # for _ in range(deck_count * 52):
            #     deck.append(PlayingCard(
            #         card_code = "s8"
            #     ))
            
            random.shuffle(deck)

            ##### Deal the cards. #####

            dealer = BlackjackPlayer(
                member_id = self.bot.user.id,
                wager = 0
            )

            for _ in range(2):
                for player in players:
                    player.add_card(deck.pop(0))
                
                dealer.add_card(deck.pop(0))
            
            ##### Send initial hands message. #####
            
            await ctx.send("# __Initial hands__:\nDealer: {dealer_card} {card_back}\n{player_hands}".format(
                dealer_card = dealer.hand[0].emoji,
                card_back = card_keys.get("back", "\*the back of the card, there should be an emoji here.\*"),
                player_hands = "\n".join([
                    "{}: {} ({})".format(
                        player.ping,
                        player.formatted_hand,
                        player.hand_value_formatted
                    ) for player in players
                ])
            ))

            ##### PLayer turns. #####

            player_id = 0
            while player_id < len(players):
                await asyncio.sleep(delay_time)

                player = copy.deepcopy(players[player_id])

                if player.hand_value == 21:
                    await ctx.send("{}\nYour current hand:\n# {} ✨ Blackjack! ✨\nBecause you have a blackjack you automatically stand.".format(
                        player.ping,
                        player.formatted_hand
                    ))
                    player.stopped = True

                    players[player_id] = player
                    player_id += 1
                    continue

                await ctx.send("{}\nYour current hand:\n# {} ({})\n{}\nYou have 1 minute before stand is automatically chosen.".format(
                    player.ping,
                    player.formatted_hand,
                    player.hand_value_formatted,
                    player.formatted_allowed
                ))


                while not player.stopped:
                    options = player.allowed_list

                    def turn_check(msg: discord.Message) -> bool:
                        if msg.channel.id != ctx.channel.id:
                            return False
                        
                        if msg.author.id != player.member_id:
                            return False
                
                        if msg.author.bot:
                            return False
                        
                        if msg.content not in options:
                            return False
                        
                        return True
                    
                    try:
                        action_message = await self.bot.wait_for(
                            "message",
                            check = turn_check,
                            timeout = 60
                        )

                        action = action_message.content
                    except asyncio.TimeoutError:
                        action = "stand"
                    
                    choice_result = player.handle_choice(
                        choice = action,
                        deck = deck
                    )

                    send = choice_result["send"]

                    deck = choice_result["deck"]

                    if choice_result.get("add_player", None) is not None:
                        players.insert(player_id + 1, choice_result["add_player"])

                    await ctx.send(send)
                
                # Update player list
                players[player_id] = player

                # Increment player id and continue
                player_id += 1
        
            await asyncio.sleep(delay_time)
            
            await ctx.send("# __Current hands__:\nDealer: {dealer_card} {card_back}\n{player_hands}".format(
                dealer_card = dealer.hand[0].emoji,
                card_back = card_keys.get("back", "\*the back of the card, there should be an emoji here.\*"),
                player_hands = "\n".join([
                    "{}: {} ({})".format(
                        player.ping,
                        player.formatted_hand,
                        player.hand_value_formatted
                    ) for player in players
                ])
            ))
        
            await asyncio.sleep(delay_time)

            await ctx.send("# It is time for the Dealer to go!\n\n# The dealer's other card is a {}!\nThe dealer's hand: {}\nThis means the dealer's hand is worth {}!".format(
                dealer.hand[1].emoji,
                dealer.formatted_hand,
                dealer.hand_value
            ))
        
            await asyncio.sleep(delay_time)

            if dealer.hand_value < 17:
                while dealer.hand_value < 17:
                    card, deck = dealer.hit(deck=deck)

                    await ctx.send("# The dealer is forced to hit and got a {}!\nThat brings their hand's value to {}!".format(
                        card.emoji,
                        dealer.hand_value
                    ))
        
                    await asyncio.sleep(delay_time)
            
            if dealer.soft_hand and dealer.hand_value == 17:
                card, deck = dealer.hit(deck=deck)

                await ctx.send("# The dealer has a soft 17 and is forced to hit and got a {}!\nThat brings their hand's value to {}!".format(
                    card.emoji,
                    dealer.hand_value
                ))
        
                await asyncio.sleep(delay_time)
            
            if dealer.hand_value == 21:
                await ctx.send("# The dealer has a Blackjack!")

                await asyncio.sleep(delay_time)
            elif dealer.hand_value > 21:
                await ctx.send("# The dealer has busted!")

                await asyncio.sleep(delay_time)
            
            await ctx.send("# __Final hands and payouts__:\nDealer: {dealer_hand} ({dealer_hand_value})\n{player_hands}".format(
                dealer_hand = dealer.formatted_hand,
                dealer_hand_value = dealer.hand_value_formatted,
                player_hands = "\n".join([
                    "{}: {} ({}) | Wagered {} and won {}!".format(
                        player.ping,
                        player.formatted_hand,
                        player.hand_value_formatted,
                        u_text.smart_number(player.wager),
                        u_text.smart_number(player.winnings(dealer))
                    ) for player in players
                ])
            ))

            self.blackjack_going = False

        except:
            self.blackjack_going = False
            raise

        
            

        
    ######################################################################################################################################################
    ##### STORY GAME #####################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "story_game",
        brief = "Story writing game.",
        description = "Story writing game.\nEveryone starts writing a story, and then cuts it off mid sentence and the last sentence is given to the next player to continue.\n\nTime estimate: 10 to 20 minutes, it mostly depends on the number of players."
    )
    @commands.check(u_checks.hide_from_help)
    async def story_game(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        await ctx.reply("This is disabled due to many bugs.")
        return
    
        if self.story_game_going:
            await ctx.reply("I am sorry, but this is already going somewhere. Please wait until it finishes to start another game.")
            return
        
        if isinstance(ctx.channel, discord.ForumChannel) or \
            isinstance(ctx.channel, discord.Thread) or \
            isinstance(ctx.channel, discord.VoiceChannel) or \
            isinstance(ctx.channel, discord.StageChannel) or \
            isinstance(ctx.channel, discord.DMChannel) or \
            isinstance(ctx.channel, discord.GroupChannel) or \
            isinstance(ctx.channel, discord.WelcomeChannel) or \
            isinstance(ctx.channel, discord.WidgetChannel):
            await ctx.reply("This game cannot be started here.")
            return
        
        try:
            self.story_game_going = True

            player_members = await self.waiting_room(ctx, "Story Writing Game")
            
            player_count = len(player_members)

            if player_count <= 1:
                await ctx.reply("Unfortunately, this game cannot be played solo :(")
                self.story_game_going = False
                return

            players = []
            threads = []

            books: list[StoryWritingGameBook] = []

            player_order = [[None for _2 in range(player_count)] for _ in range(player_count)]

            for player_id, player in enumerate(player_members):
                thread = await ctx.channel.create_thread(
                    name = f"Story Writing Game Thread #{player_id + 1}",
                    invitable = False,
                    reason = "Story Writing Game auto-thread creation."
                )

                threads.append(thread)

                players.append(StoryWritingGamePlayer(
                    member = player,
                    thread = thread
                ))

            zero_position = [0] + list(range(1, player_count))
            random.shuffle(zero_position)

            for round_id in range(player_count):
                for player_id, player in enumerate(players):
                    player_order[round_id][zero_position[round_id] - player_id] = player
            

            for book_order in player_order:
                books.append(StoryWritingGameBook(
                    player_order = book_order
                ))
            
            #####################
                
            def get_book_from_member(member: discord.Member) -> StoryWritingGameBook | None:
                for book in books:
                    if book.current_player.member.id == member.id:
                        return book
                    
                return None
                
            def message_check(message: discord.Message) -> bool:
                if message.author not in player_members:
                    return False
                
                if message.channel not in threads:
                    return False

                return True
            
            # Round length in minutes.
            ROUND_LENGTH = 5
            
            for round_number in range(player_count + 1):
                ending_time = int(time.time()) + ROUND_LENGTH * 60
                for book in books:
                    book.round_current = round_number
                    book.round_contributed = False
                    await book.send_message(ending_time)

                finished = 0
                
                while time.time() < ending_time:
                    try:
                        msg = await self.bot.wait_for(
                            "message",
                            check = message_check,
                            timeout = ending_time - time.time() + 1
                        )
                    except asyncio.TimeoutError:
                        break

                    book = get_book_from_member(msg.author)

                    if book.round_contributed:
                        continue

                    content = msg.content

                    if "." not in content:
                        await msg.reply("You must complete at least one sentence.")
                        continue

                    # If it's the last round.
                    if round_number == player_count:
                        book.text.append(content)
                    else:
                        main, end = content.rsplit(".", 1)

                        book.text.append(main + ".")
                        book.text.append(end)

                    book.round_contributed = True

                    await msg.reply("Perfect! Time to wait for the next round to finish.")
                    finished += 1

                    if finished == player_count:
                        break

                await asyncio.sleep(1)
            
            await ctx.reply("{pings}\n\nThe game is over! Pretty soon I will be sending everyone's books!".format(pings=", ".join([m.mention for m in player_members])))
            
            file_path = os.path.join("data", "misc", "book.txt")
            for book in books:
                book_player = book.player_order[0]

                name = u_interface.get_display_name(book_player.member)
                
                with open(file_path, "w+") as file_write:
                    file_write.write(f"### {name}'s book: ###\n\n" + " ".join(book.text))
                

                await book_player.thread.delete()
                
                await ctx.send(f"{book_player.member.mention}, this is your book!", file=discord.File(file_path))

                await asyncio.sleep(1.2831853071) # τ - 5

            self.story_game_going = False
        except:
            self.story_game_going = False
            raise
        



async def setup(bot: commands.Bot):
    global database
    database = bot.database

    cog = Games_cog()
    cog.bot = bot
    
    # Add attributes for sys.modules and globals() so the _reload_module() function in utility.custom can read it and get the module objects.
    cog.modules = sys.modules
    cog.globals = globals()
    
    await bot.add_cog(cog)