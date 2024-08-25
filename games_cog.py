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
import aiohttp
import datetime
import collections

import sys

import utility.files as u_files
import utility.custom as u_custom
import utility.interface as u_interface
import utility.checks as u_checks
import utility.text as u_text
import utility.images as u_images
import utility.converters as u_converters
import utility.skyblock as u_skyblock

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
        
class BlackjackCard(PlayingCard):
    def __init__(
            self: typing.Self,
            card_code: str
        ):
        super().__init__(card_code)

        if self.value <= 10:
            self.game_value = self.value
        else:
            self.game_value = 10

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
        
        self.hand: list[BlackjackCard] = []

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
            card: BlackjackCard
        ) -> None:
        self.hand.append(card)

    def hit(
            self: typing.Self,
            deck: list[BlackjackCard]
        ) -> tuple[BlackjackCard, list[BlackjackCard]]:
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
            deck: list[BlackjackCard]
        ) -> tuple[BlackjackCard, list[BlackjackCard]]:
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
            deck: list[BlackjackCard]
        ) -> tuple[BlackjackPlayer, list[BlackjackCard]]:

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
            deck: list[BlackjackCard]
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
    skyblock_item_data = None
    skyblock_skill_data = None
    skyblock_collections_data = None

    story_game_going = False
    blackjack_going = False
    skyblock_wiki_searching = False

    traitor_game_going = False

    #########################################################################################################

    async def fetch_skyblock_items(self: typing.Self) -> list | None:
        """Returns the list of skyblock items via sending a request to the Hypixel API."""
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.hypixel.net/v2/resources/skyblock/items") as resp:
                if not resp.ok:
                    return None
                
                return (await resp.json())
    
    async def get_skyblock_items(self: typing.Self) -> list:
        """Returns the list of skyblock items as is stored in the `skyblock_item_data` attribute.
        If the attribute has not been loaded yet it will be loaded."""
        if self.skyblock_item_data is not None:
            return self.skyblock_item_data

        self.skyblock_item_data = await self.fetch_skyblock_items()
        return self.skyblock_item_data
    
    #########################################################################################################

    async def fetch_skyblock_skills(self: typing.Self) -> list | None:
        """Returns the list of skyblock skills via sending a request to the Hypixel API."""
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.hypixel.net/v2/resources/skyblock/skills") as resp:
                if not resp.ok:
                    return None
                
                return (await resp.json())
    
    async def get_skyblock_skills(self: typing.Self) -> list:
        """Returns the list of skyblock skills as is stored in the `skyblock_skill_data` attribute.
        If the attribute has not been loaded yet it will be loaded."""
        if self.skyblock_skill_data is not None:
            return self.skyblock_skill_data

        self.skyblock_skill_data = await self.fetch_skyblock_skills()
        return self.skyblock_skill_data
    
    #########################################################################################################

    async def fetch_skyblock_collections(self: typing.Self) -> list | None:
        """Returns the list of skyblock collections via sending a request to the Hypixel API."""
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.hypixel.net/v2/resources/skyblock/collections") as resp:
                if not resp.ok:
                    return None
                
                return (await resp.json())
    
    async def get_skyblock_collections(self: typing.Self) -> list:
        """Returns the list of skyblock collections as is stored in the `skyblock_collections_data` attribute.
        If the attribute has not been loaded yet it will be loaded."""
        if self.skyblock_collections_data is not None:
            return self.skyblock_collections_data

        self.skyblock_collections_data = await self.fetch_skyblock_collections()
        return self.skyblock_collections_data

    #########################################################################################################
    
    async def daily_task(self: typing.Self):
        """Code that runs for every hour."""
        self.skyblock_item_data = await self.fetch_skyblock_items()
        self.skyblock_skill_data = await self.fetch_skyblock_skills()
        self.skyblock_collection_data = await self.fetch_skyblock_collections()

    def time_next(
            self: typing.Self,
            timestamp: float,
            minute: int
        ) -> int:
        """Returns the timestamp for the next instance of that minute within an hour."""
        return int(timestamp + 3600 - ((timestamp - (minute * 60)) % 3600))

    #########################################################################################################

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
                
                if msg.contetn.lower() != "join":
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
                return message.author not in players_participating and message.content.lower() == "join" and message.channel == ctx.channel and hasattr(message, "webhook_id") and message.webhook_id is None
            
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
        
        if ctx.guild is None:
            await ctx.reply("This cannot be run in DMs.")
            return
        
        allowed_channels = [
            959229175229726760,
            967544442468843560,
            1063317762191147008
        ]
        if ctx.guild.id == 958392331671830579:
            if not (isinstance(ctx.channel, discord.Thread)) and ctx.channel.id not in allowed_channels:
                await ctx.reply("I am sorry, but Blackjack can only be started in the following channels or in any thread: {}".format(
                    ", ".join([f"<#{c}>" for c in allowed_channels])
                ))
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

                matched = join_pattern.match(msg.content.lower())
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
                        deck.append(BlackjackCard(
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
                        
                        if msg.content.lower() not in options:
                            return False
                        
                        return True
                    
                    try:
                        action_message = await self.bot.wait_for(
                            "message",
                            check = turn_check,
                            timeout = 60
                        )

                        action = action_message.content.lower()
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

        
            

        
    ######################################################################################################################################################
    ##### SKYBLOCK #######################################################################################################################################
    ######################################################################################################################################################
    
    @commands.group(
        name = "skyblock",
        brief = "Header command for Hypixel Skyblock commands.",
        description = "Header command for Hypixel Skyblock related utility commands.",
        invoke_without_command = True,
        pass_context = True
    )
    @commands.check(u_checks.hide_from_help)
    async def skyblock(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        if ctx.invoked_subcommand is not None:
            return
        
        await ctx.send_help(self.skyblock)

        
            

        
    ######################################################################################################################################################
    ##### SKYBLOCK WIKI ##################################################################################################################################
    ######################################################################################################################################################
    
    @skyblock.command(
        name = "wiki",
        brief = "Search the Skyblock Wiki.",
        description = "Search the Skyblock Wiki, which can be found here:\nhttps://wiki.hypixel.net/"
    )
    async def skyblock_wiki(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            *, search_term: typing.Optional[str] = commands.parameter(description = "The search term to search the wiki with.")
        ):
        if self.skyblock_wiki_searching:
            await ctx.reply("This commmand is currently being used somewhere, please wait until it's done to try again.")
            return
        
        try:
            self.skyblock_wiki_searching = True

            def manual_replacements(text: str) -> str:
                base = {
                    r"{{Unobtainable}}": "Admin",
                    r"{{Ultimate Rarity}}": "Ultimate",
                    r"{{Very Special}}": "Very Special",
                    r"{{Special}}": "Special",
                    r"{{Devine}}": "Devine",
                    r"{{Mythic}}": "Mythic",
                    r"{{Legendary}}": "Legenday",
                    r"{{Epic}}": "Epic",
                    r"{{Rare}}": "Rare",
                    r"{{Uncommon}}": "Uncommon",
                    r"{{Common}}": "Common",
                    r"{{Item\/([A-Z_0-9-]+)}}": r"[\1](https://wiki.hypixel.net/\1)",
                }

                for pattern, replacement in base.items():
                    text = re.sub(pattern, replacement, text)

                out = []

                patterns = [
                    r"\|summary ?= ?([\s\S]+?)\|[\w]+ ?= ?",
                    r"\|obtaining ?= ?([\s\S]+?)\|[\w]+ ?= ?",
                    r"\|usage ?= ?([\s\S]+?)\|[\w]+ ?= ?",
                    r"\|body ?= ?([\s\S]+?)\|[\w]+ ?= ?"
                ]
                for pattern in patterns:
                    searched = re.search(pattern, text)
                    if searched is None:
                        continue

                    searched = searched.group(1).strip()

                    out.append(searched)
                
                return "\n".join(out)

            await u_interface.handle_wiki_search(
                ctx = ctx,
                wiki_link = "https://wiki.hypixel.net/",
                wiki_main_page = "https://wiki.hypixel.net/Main_Page",
                wiki_name = "The Hypixel Skyblock Wiki",
                wiki_api_url = "https://wiki.hypixel.net/api.php",
                search_term = search_term,
                manual_replacements = manual_replacements
            )

            self.skyblock_wiki_searching = False
        except:
            self.skyblock_wiki_searching = False

            # After ensuring skyblock_wiki_searching has been reset, reraise the exception so the "Something went wrong processing that command." message is still sent.
            raise

        
            

        
    ######################################################################################################################################################
    ##### SKYBLOCK EVENTS ################################################################################################################################
    ######################################################################################################################################################
    
    @skyblock.group(
        name = "events",
        brief = "Provides information regarding future events.",
        description = "Provides information regarding future events.",
        invoke_without_command = True,
        pass_context = True
    )
    async def skyblock_events(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        if ctx.invoked_subcommand is not None:
            return
        
        timestamp = time.time()

        START_TIME = 1560275700

        SECONDS_IN_YEAR = 446400
        SECONDS_IN_MONTH = 37200
        SECONDS_IN_DAY = 1200

        EIGHT_YEARS = SECONDS_IN_YEAR * 8

        offset = timestamp - START_TIME

        in_year = offset % SECONDS_IN_YEAR
        year_start = timestamp - in_year

        def event_in_year(
                month: int,
                day: int,
                length: int,
                frequency: int = 1
            ) -> tuple[int, bool]:
            year_modified = SECONDS_IN_YEAR // frequency

            start_offset = month * SECONDS_IN_MONTH + day * SECONDS_IN_DAY
            end_offset = start_offset + length * SECONDS_IN_DAY

            year_start = timestamp - (in_year % year_modified)

            start = start_offset + year_start
            end = end_offset + year_start

            if timestamp >= end:
                start += year_modified
                end += year_modified

            active = start <= timestamp < end

            return (
                int(end if active else start),
                active
            )
        
        def event_in_year_wrapper(
                name: str,
                month: int,
                day: int,
                length: int,
                frequency: int = 1
            ) -> str:
            event_timestamp, active = event_in_year(month, day, length, frequency)

            return "{name}: {line} <t:{timestamp}:R>.".format(
                name = name,
                line = "Active! Ends" if active else "Starts",
                timestamp = event_timestamp
            )
        
        auction_timestamp = self.time_next(timestamp, -5)

        spooky = event_in_year_wrapper(
            name = "Spooky Festival",
            month = 7,
            day = 28,
            length = 3
        )

        zoo = event_in_year_wrapper(
            "Traveling Zoo",
            month = 3,
            day = 0,
            length = 3,
            frequency = 2
        )

        season_jerry = event_in_year_wrapper(
            name = "Season of the Jerry",
            month = 11,
            day = 23,
            length = 3
        )

        new_year = event_in_year_wrapper(
            name = "New Year Celebration",
            month = 11,
            day = 28,
            length = 3
        )

        hoppity = event_in_year_wrapper(
            name = "Hoppity's Hunt",
            month = 0,
            day = 0,
            length = 93
        )

        ##### Special mayors. ######

        raw_year = (timestamp - START_TIME) / SECONDS_IN_YEAR + 1

        mayor_names = [
            "Jerry",
            "Scorpius",
            "Derpy"
        ]

        derpy_example = 345

        raw_year_mod = raw_year - derpy_example
        year_mod = int(raw_year_mod) 
        next_mayor = (year_mod // 8) % 3

        year_timestamp = (8 - (year_mod % 8)) * SECONDS_IN_YEAR + year_start

        booth_offset = 5 * SECONDS_IN_MONTH + 26 * SECONDS_IN_DAY # Late Summer 27th is when the election booth opens.
        elected_offset = 2 * SECONDS_IN_MONTH + 26 * SECONDS_IN_DAY # Late Spring 27th is when the election booth closes.

        booth = year_timestamp - (SECONDS_IN_YEAR - booth_offset)
        elected = year_timestamp + elected_offset

        names = collections.deque(mayor_names)
        names.rotate(-next_mayor)

        mayors = "\n".join(
            "- {name}: Booth opens <t:{booth}:R>. Elected <t:{elected}:R>.".format(
                name = name,
                booth = int(booth + EIGHT_YEARS * index),
                elected = int(elected + EIGHT_YEARS * index)
            )
            for index, name in enumerate(names)
        )

        dante = '\n- Dante: Please no.' if random.randint(1, 10) == 1 else ''

        ############################
        
        embed = u_interface.gen_embed(
            title = "Skyblock Events",
            description = f"The next Dark Auction will occur <t:{auction_timestamp}:R>.\nMid-year events:\n{spooky}\n{zoo}\n{season_jerry}\n{new_year}\n{hoppity}\n\nSpecial mayors:\n{mayors}{dante}",
            footer_text = "Use '%help skyblock events' to view the list of subcommands.",
            timestamp = datetime.datetime.fromtimestamp(time.time())
        )

        await ctx.reply(embed=embed)

        
            

        
    ######################################################################################################################################################
    ##### SKYBLOCK EVENTS FARMING ########################################################################################################################
    ######################################################################################################################################################
    
    @skyblock_events.command(
        name = "farming",
        brief = "Gives information about Jacob's Farming Contests.",
        description = "Gives information about Jacob's Farming Contests.",
    )
    async def skyblock_events_farming(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            *, crop_name: typing.Optional[str] = commands.parameter(description = "Optional argument to search for the next contest with the given crop.")
        ):
        
        timestamp = time.time()
        
        contest_timestamp = self.time_next(timestamp, 15)
        contest_end = self.time_next(timestamp, -25)

        if (15 * 60) <= (timestamp % 3600) < (35 * 60):
            active = int(contest_timestamp - 3600)
        else:
            active = None


        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.elitebot.dev/contests/at/now") as resp:
                if resp.status != 200:
                    await ctx.reply("Something went wrong.")
                    return
                
                ret_json = await resp.json()
        
        if crop_name is not None:
            search = crop_name.title()
            
            if active is not None:
                active_data = ret_json.get("contests", {}).get(str(active), [])
                if search in active_data:
                    embed = u_interface.gen_embed(
                        title = "Skyblock Farming Contests",
                        description = f"The next time {search} is in a farming contest is right now!",
                        timestamp = datetime.datetime.fromtimestamp(time.time())
                    )
                    await ctx.reply(embed=embed)
                    return
                
            iterator = [(key, data) for key, data in ret_json.get("contests", {}).items() if int(key) > timestamp]

            next_timestamp = None

            for key, data in iterator:
                if search in data:
                    next_timestamp = key
                    break
        
            if next_timestamp is None:
                embed = u_interface.gen_embed(
                    title = "Skyblock Farming Contests",
                    description = f"Contest search for `{crop_name}` yielded no results.\nTry another crop.\nNote that multi-word crops require a space to be provided.",
                    timestamp = datetime.datetime.fromtimestamp(time.time())
                )
            else:
                embed = u_interface.gen_embed(
                    title = "Skyblock Farming Contests",
                    description = f"The next time {search} is in a farming contest is <t:{next_timestamp}:R>.",
                    timestamp = datetime.datetime.fromtimestamp(time.time())
                )

            await ctx.reply(embed=embed)
            return
        
        contest_key = next((x for x in ret_json.get("contests", {}).keys() if int(x) > timestamp), None)

        if contest_key is None:
            contest_lines = [f"The next farming contest will occur <t:{contest_timestamp}:R>.\nThe crops will be as follows:\n*Unknown.*"]
        else:
            contest_lines = [f"The next farming contest will occur <t:{contest_timestamp}:R>.\nThe crops will be as follows:"]
            contest_lines.extend([
                f"- {item}"
                for item in ret_json.get("contests", {}).get(contest_key, [])
            ])
        
        if active is None:
            active_lines = ["There is not currently a farming contest active."]
        else:
            active_lines = [f"The current farming contest will end <t:{contest_end}:R>.\nThe crops are as follows:"]
            active_lines.extend(
                [
                    f"- {item}"
                    for item in ret_json.get("contests", {}).get(str(active), [])
                ]
            )
        
        embed = u_interface.gen_embed(
            title = "Skyblock Farming Contests",
            description = "You can use `%skyblock events farming <crop>` to search for a future farming contest containing that crop.",
            fields = [
                (
                    "Current farming contest",
                    "\n".join(active_lines),
                    True
                ),
                (
                    "Next farming contest",
                    "\n".join(contest_lines),
                    True
                )
            ],
            timestamp = datetime.datetime.fromtimestamp(time.time())
        )

        await ctx.reply(embed=embed)
        


        
            

        
    ######################################################################################################################################################
    ##### SKYBLOCK EVENTS MINING #########################################################################################################################
    ######################################################################################################################################################
    
    @skyblock_events.command(
        name = "mining",
        brief = "Shows the mining events.",
        description = "Shows the current events in the Dwarven Mines, Crystal Hollows, and Glacite Mineshafts."
    )
    async def skyblock_events_mining(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        current_time = time.time()

        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.soopy.dev/skyblock/chevents/get") as resp:
                if resp.status != 200:
                    await ctx.reply("Something went wrong.")
                    return
                
                ret_json = await resp.json()
            
            if not ret_json.get("success", False):
                await ctx.reply("Something went wrong.")
                return
        
        fields = []

        ret_json = ret_json["data"]

        for key, name in [("DWARVEN_MINES", "Dwarven Mines"), ("CRYSTAL_HOLLOWS", "Crystal Hollows"), ("MINESHAFT", "Glacite Mineshafts")]:
            event_data = ret_json.get("event_data", {}).get(key, {})
            data = ret_json.get("running_events", {}).get(key, {})

            data = list(sorted(
                data,
                # key = lambda d: event_data.get(d.get("event"), {}).get("starts_at_min", 0)
                key = lambda d: event_data.get(d.get("event"), {}).get("lobby_count", 0)
            ))

            data = [d for d in data if (d.get("ends_at") / 1000) > current_time]

            total_lobby_count = ret_json.get("total_lobbys", {}).get(key, "*Unknown.*")

            if len(data) == 0:
                current = "*Unknown.*"
                future = "*Unknown.*"
            else:
                current = "Type: **{name}**\nEnds <t:{end}:R>\n*Lobby count: {lobby_count}*".format(
                    name = data[0].get("event", "Unknown.").lower().replace("_", " ").title(),
                    end = int(data[0].get("ends_at", 0) // 1000),
                    lobby_count = data[0].get("lobby_count", 0)
                )

                if len(data) >= 2:
                    future_events = []

                    for event in data[1:]:
                        # start_min = event_data.get(event.get("event"), {}).get("starts_at_min", 0) # this didnt work for some reason
                        # start_max = event_data.get(event.get("event"), {}).get("starts_at_max", 0)

                        future_events.append("- Type: **{name}**\n  Ends <t:{end}:R>\n  *Lobby count: {lobby_count}*".format(
                            name = event.get("event", "Unknown.").lower().replace("_", " ").title(),
                            # starts = int(((start_min + start_max) / 2) // 1000),
                            end = int(event.get("ends_at", 0) // 1000),
                            lobby_count = event.get("lobby_count", 0)
                        ))
                    
                    future = "\n\n".join(future_events)
                else:
                    future = "*Unknown.*"
            
            fields.append(
                (
                    name,
                    f"*Total lobby count: {total_lobby_count}*\n\n Current event:\n{current}\n\nFuture event{'s' if len(data) >= 3 else ''}:\n{future}",
                    True
                )
            )
        
        embed = u_interface.gen_embed(
            title = "Mining Events",
            fields = fields,
            footer_text = "Data sourced from soopy.dev.",
            timestamp = datetime.datetime.fromtimestamp(time.time())
        )

        await ctx.reply(embed = embed)

        
            

        
    ######################################################################################################################################################
    ##### SKYBLOCK HOTM ##################################################################################################################################
    ######################################################################################################################################################
    
    @skyblock.command(
        name = "hotm",
        brief = "Calculates HotM perk requirements.",
        description = "Calculates the required amount of powder to go from a level of a Heart of the Mountain perk to another."
    )
    async def skyblock_hotm(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            *, perk_name: typing.Optional[str] = commands.parameter(description = "The name of the perk."),
            start: typing.Optional[str] = commands.parameter(description = "The starting level."),
            end: typing.Optional[str] = commands.parameter(description = "The ending level.")
        ):
        if perk_name is None:
            await ctx.reply("Please provide the perk name, start level, and end level.")
            return
        
        perk_use = None
        
        check_split = perk_name.lower().split(" ")
        check_name = check_split[0]
        
        for perk in sorted(u_skyblock.all_hotm_perks, key=lambda p: len(p.name), reverse=True):
            if perk.name.split(" ")[0].lower() != check_name:
                continue

            perk_split = perk.name.lower().split(" ")

            if len(check_split) < len(perk_split):
                continue

            for arg_id, arg in enumerate(perk_split):
                if check_split[arg_id] != arg:
                    break
            else:
                perk_use = perk
                break
        else:
            await ctx.reply("Please provide the perk name, start level, and end level.")
            return
        
        if perk_use is None:
            await ctx.reply("Please provide the perk name, start level, and end level.")
            return
        
        start_index = len(perk_use.name.split(" "))

        if len(check_split) <= start_index + 1:
            await ctx.reply("Please provide the perk name, start level, and end level.")
            return
        
        try:
            start = u_converters.parse_int(check_split[start_index])
            end = u_converters.parse_int(check_split[start_index + 1])
        except ValueError:
            await ctx.reply("Please provide the perk name, start level, and end level.")
            return

        if start < 0:
            start = 0
        
        if end > perk_use.max_level:
            end = perk_use.max_level

        if end < start:
            await ctx.reply("The start must be before the end.")
            return
        
        if end == start:
            start -= 1

        cost = perk_use.get_cost_sum(
            start = 1 if start == 0 else start,
            end = end
        )

        cost_description = "**{} {}**{}".format(
            u_text.smart_number(round(cost)),
            perk_use.cost_type,
            " and 1 Token of the Mountain" if start == 0 else ""
        )

        embed = u_interface.gen_embed(
            title = f"{perk_use.name} cost calculation",
            description = f"Cost to go from level **{start}** to level **{end}** for {perk_use.name}:\n{cost_description}",
            timestamp = datetime.datetime.fromtimestamp(time.time())
        )

        await ctx.reply(embed=embed)

        
            

        
    ######################################################################################################################################################
    ##### SKYBLOCK MAYOR #################################################################################################################################
    ######################################################################################################################################################
    
    @skyblock.command(
        name = "mayor",
        aliases = ["election"],
        brief = "Provides information about the current mayor.",
        description = "Provides information about the current mayor and the next election."
    )
    async def skyblock_mayor(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.hypixel.net/v2/resources/skyblock/election") as resp:
                if resp.status != 200:
                    await ctx.reply("Something went wrong.")
                    return
                
                ret_json = await resp.json()
            
            if not ret_json.get("success", False):
                await ctx.reply("Something went wrong.")
                return
        
        def get_perks(data: dict) -> list[str]:
            out = []

            for perk in data:
                perk_name = perk.get("name", "*Unknown.*")
                perk_description = perk.get("description", "*Unknown.*")

                perk_description = re.sub(r"§.", "", perk_description)

                out.append(f"- {perk_name} - *{perk_description}*")
            
            return out
        
        mayor_data = ret_json.get("mayor", {})

        mayor_name = mayor_data.get("name", "*Unknown.*")

        mayor_perks = get_perks(mayor_data.get("perks", []))
        
        election_fields = []
        next_election_chosen = False

        if "current" in ret_json:
            next_election_chosen = True
            
            next_candidate_data = ret_json.get("current", {})

            total_votes = sum([candidate.get("votes", 0) for candidate in next_candidate_data.get("candidates", [])])

            for candidate in next_candidate_data.get("candidates", []):
                candidate_name = candidate.get("name", "*Unknown.*")

                candidate_perks = get_perks(candidate.get("perks", []))
                vote_count = candidate.get("votes", 0)

                if total_votes == 0:
                    vote_section = "*Votes hidden.*"
                else:
                    vote_section = "{vote_count} ({vote_percent}%)".format(
                            vote_count = u_text.smart_number(vote_count),
                            vote_percent = round(vote_count / total_votes * 100, 2)
                    )

                election_fields.append(
                    (
                        candidate_name,
                        "Votes: {votes}\nPerks:\n{perks}".format(
                            votes = vote_section,
                            perks = "\n".join(candidate_perks)
                        ),
                        True
                    )
                )
        
        embed = u_interface.gen_embed(
            title = "Skyblock Mayors",
            description = "Current mayor:\n# **{mayor_name}**\nPerks:\n{perks}\n\n**Year {next_year} candidates:**\n{next_election_chosen}".format(
                mayor_name = mayor_name,
                perks = "\n".join(mayor_perks),
                next_year = u_text.smart_number(mayor_data.get("election", {}).get("year", -1) + 1),
                next_election_chosen = "" if next_election_chosen else "*Candidates not selected yet. Election booth not open.*"
            ),
            fields = election_fields,
            timestamp = datetime.datetime.fromtimestamp(time.time())
        )

        await ctx.reply(embed=embed)

        
            

        
    ######################################################################################################################################################
    ##### SKYBLOCK BAZAAR ################################################################################################################################
    ######################################################################################################################################################
    
    @skyblock.command(
        name = "bazaar",
        brief = "Searches the Skyblock Bazaar.",
        description = "Searches the Skyblock Bazaar."
    )
    async def skyblock_bazaar(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            *, item_name: typing.Optional[str] = commands.parameter(description = "The name or id of the item to search for.")
        ):
        if item_name is None:
            await ctx.reply("Please provide the name or id of the item to search for.")
            return
        
        final_item_id = None
        bazaar_data = None
        
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.hypixel.net/v2/skyblock/bazaar") as resp:
                if not resp.ok:
                    await ctx.reply("Sorry, something went wrong making the request, please try again later.")
                    return
                
                bazaar_data = await resp.json()
            
            # If the given item name is an id, return it.
            if item_name.upper() in bazaar_data.get("products", {}):
                final_item_id = item_name.upper()
            else:
                items = await self.get_skyblock_items()

                for item in items.get("items", []):
                    if item.get("name").lower() == item_name.lower():
                        final_item_id = item.get("id")
        
        if final_item_id is None:
            await ctx.reply("Please provide the name or id of the item to search for.")
            return
        
        if bazaar_data is None:
            await ctx.reply("Sorry, something went wrong making the request, please try again later.")
            return

        if final_item_id not in bazaar_data.get("products", {}):
            await ctx.reply("That item is not in the Bazaar.")
            return
        
        fields = []

        def sell_buy_data(data: list) -> str:
            if len(data) == 0:
                return "Count: 0\nCurrent price: **?**"

            return f"Count: {data[0]['orders']}\nCurrent price: **{u_text.smart_number(data[0]['pricePerUnit'])}**"
        
        item_data = bazaar_data.get("products", {}).get(final_item_id, {})

        fields.append(
            (
                "Sell Summary",
                sell_buy_data(item_data.get("sell_summary", [])),
                False
            )
        )

        fields.append(
            (
                "Buy Summary",
                sell_buy_data(item_data.get("buy_summary", [])),
                False
            )
        )

        quick_data = item_data.get("quick_status", {})

        fields.append(
            (
                "Quick Buy/Sell",
                "Buy price: **{buy_price}**\nBuy orders: {buy_orders}\nBuy stock: {buy_stock}\n\nSell price: **{sell_price}**\nSell orders: {sell_orders}\nSell stock: {sell_stock}".format(
                    buy_price = u_text.smart_number(round(quick_data.get("buyPrice", 0), 1)),
                    sell_price = u_text.smart_number(round(quick_data.get("sellPrice", 0), 1)),
                    buy_orders = u_text.smart_number(quick_data.get("buyOrders", 0)),
                    sell_orders = u_text.smart_number(quick_data.get("sellOrders", 0)),
                    buy_stock = u_text.smart_number(quick_data.get("buyVolume", 0)),
                    sell_stock = u_text.smart_number(quick_data.get("sellVolume", 0))
                ),
                False
            )
        )

        embed = u_interface.gen_embed(
            title = "Hypixel Bazaar",
            description = f"*Last updated <t:{bazaar_data.get('lastUpdated') // 1000}:R>*\n\nSearching for item with id {final_item_id}:",
            fields = fields,
            timestamp = datetime.datetime.fromtimestamp(time.time())
        )

        await ctx.reply(embed=embed)

        
            

        
    ######################################################################################################################################################
    ##### SKYBLOCK TIME ##################################################################################################################################
    ######################################################################################################################################################
    
    @skyblock.command(
        name = "time",
        brief = "Provides the current time in Skyblock.",
        description = "Provides the current time in Skyblock."
    )
    async def skyblock_time(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        base_time = time.time()

        # The time at which Skyblock started,
        # used to offset the unix timestamp
        # when calculating the time in Skyblock.
        START_TIME = 1560275700

        SECONDS_IN_YEAR = 446400 # 60 * 20 * 31 * 3 * 4 | Seconds in a day, times 31 days, times 3 months in a season, times 4 seasons.
        SECONDS_IN_SEASON = 111600 # 60 * 20 * 31 * 3 | Seconds in a day, times 31 days, times 3 months in a season.
        SECONDS_IN_MONTH = 37200 # 60 * 20 * 31 | Seconds in a day, times 31 days.
        SECONDS_IN_DAY = 1200 # 60 * 20

        MONTH_NAMES = [
            "Early Spring",
            "Spring",
            "Late Spring",
            "Early Summer",
            "Summer",
            "Late Summer",
            "Early Autumn",
            "Autumn",
            "Late Autumn",
            "Early Winter",
            "Winter",
            "Late Winter"
        ]

        raw_year = (base_time - START_TIME) / (60 * 20) / 372
        raw_month = (raw_year % 1 * 372) / 31
        raw_day = raw_month % 1 * 31
        raw_hour = raw_day % 1 * 24
        raw_minute = raw_hour % 1 * 60
        
        year = int(raw_year + 1)
        month = int(raw_month)
        day = int(raw_day + 1)
        hour = int(raw_hour)
        minute = int(raw_minute)

        if str(day).endswith("1") and not str(day).endswith("11"):
            suffix = "st"
        elif str(day).endswith("2") and not str(day).endswith("12"):
            suffix = "nd"
        elif str(day).endswith("3") and not str(day).endswith("13"):
            suffix = "rd"
        else:
            suffix = "th"

        next_century = int((SECONDS_IN_YEAR * 100) - ((raw_year % 100) * SECONDS_IN_YEAR) + base_time)
        next_year = int(SECONDS_IN_YEAR - ((raw_year % 1) * SECONDS_IN_YEAR) + base_time)
        next_season = int(SECONDS_IN_SEASON - ((((raw_year % 1) / 0.25) % 1) * SECONDS_IN_SEASON) + base_time)
        next_month = int(SECONDS_IN_MONTH - ((raw_month % 1) * SECONDS_IN_MONTH) + base_time)
        next_day = int(SECONDS_IN_DAY - ((raw_day % 1) * SECONDS_IN_DAY) + base_time)

        embed = u_interface.gen_embed(
            title = "Time in Skyblock",
            description = "It is currently {hour}:{minute:02} {ampm} on the {day}{suffix} of {month} in the year {year}.\n\nThe next century is <t:{next_century}:R>.\nThe next year is <t:{next_year}:R>.\nThe next season is <t:{next_season}:R>.\nThe next month is <t:{next_month}:R>.\nThe next day is <t:{next_day}:R>.".format(
                hour = (hour + 11) % 12 + 1,
                minute = minute,
                ampm = "am" if hour < 12 else "pm",
                day = day,
                suffix = suffix,
                month = MONTH_NAMES[month],
                year = year,
                next_century = next_century,
                next_year = next_year,
                next_season = next_season,
                next_month = next_month,
                next_day = next_day
            ),
            timestamp = datetime.datetime.fromtimestamp(base_time)
        )

        await ctx.reply(embed=embed)

        
            

        
    ######################################################################################################################################################
    ##### SKYBLOCK COLLECTIONS ###########################################################################################################################
    ######################################################################################################################################################
    
    @skyblock.command(
        name = "collections",
        aliases = ["collection"],
        brief = "View information regarding Skyblock collections.",
        description = "View information regarding Skyblock collections."
    )
    async def skyblock_collections(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            *, item_name: typing.Optional[str] = commands.parameter(description = "The name or id of the item to search for.")
        ):
        if item_name is None:
            await ctx.reply("Please provide the item name to get the collection for.")
            return
        
        collections_data = await self.get_skyblock_collections()

        item_data = None
        
        lower = item_name.lower()

        for skill in collections_data.get("collections", {}).values():
            items = skill.get("items", {})
            if lower in items:
                item_data = items.get(item_name)
                break

            for item in skill.get("items", {}).values():
                if item.get("name").lower() == lower:
                    item_data = item
                    break
            else:
                continue

            break

        if item_data is None:
            await ctx.reply("Please provide the item name to get the collection for.")
            return
        
        tiers = []

        for tier in item_data.get("tiers", []):
            tiers.append("**Tier {}:**\nRequired items: {}\nRewards:\n{}".format(
                u_text.smart_number(tier.get("tier", 0)),
                u_text.smart_number(tier.get("amountRequired", 0)),
                "\n".join(
                    [
                        f"- {reward}"
                        for reward in tier.get("unlocks", [])
                    ]
                )
            ))
        
        fields = []

        if len(tiers) <= 8:
            fields.append(
                (
                    "",
                    "\n".join(tiers[:len(tiers) // 2]),
                    True
                )
            )
            fields.append(
                (
                    "",
                    "\n".join(tiers[len(tiers) // 2:]),
                    True
                )
            )
        else:
            fields.append(
                (
                    "",
                    "\n".join(tiers[:len(tiers) // 3]),
                    True
                )
            )
            fields.append(
                (
                    "",
                    "\n".join(tiers[len(tiers) // 3:len(tiers) // 3 * 2]),
                    True
                )
            )
            fields.append(
                (
                    "",
                    "\n".join(tiers[len(tiers) // 3 * 2:]),
                    True
                )
            )

        embed = u_interface.gen_embed(
            title = f"{item_data.get('name')} collection:",
            # description = "\n".join(description_lines),
            fields = fields,
            timestamp = datetime.datetime.fromtimestamp(collections_data.get("lastUpdated", 0) / 1000)
        )

        await ctx.reply(embed=embed)

        
            

        
    ######################################################################################################################################################
    ##### SKYBLOCK SKILLS ################################################################################################################################
    ######################################################################################################################################################
    
    @skyblock.command(
        name = "skills",
        aliases = ["skill"],
        brief = "View information regarding Skyblock skills.",
        description = "View information regarding Skyblock skills."
    )
    async def skyblock_skills(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            skill_name: typing.Optional[str] = commands.parameter(description = "The name of the skill to get information about."),
            skill_level: typing.Optional[int] = commands.parameter(description = "The level of the skill to get information about.")
        ):
        if skill_name is None:
            await ctx.reply("Please provide the skill name.")
            return
        
        if skill_level is None:
            skill_level = -1

        skills_data = await self.get_skyblock_skills()

        if skill_name.upper() not in skills_data.get("skills", {}):
            await ctx.reply("Please provide the skill name.")
            return
        
        skill_data = skills_data.get("skills", {}).get(skill_name.upper(), {})
        max_level = skill_data.get("maxLevel", 25)
        skill_level = min(skill_level, max_level)
        
        if skill_level < 0:
            skill_level = skill_level % max_level + 1
        
        if skill_level == 0:
            skill_level = 1

        level = skill_data.get("levels", [])[skill_level - 1]
        xp = level.get('totalExpRequired', 0)

        embed = u_interface.gen_embed(
            title = f"{skill_data.get('name')} skill:",
            description = "Information for level {}/{}:\nTotal xp required: {}\nXp to the next level: {}\nRewards:\n{}".format(
                skill_level,
                max_level,
                u_text.smart_number(int(xp)),
                u_text.smart_number(int(skill_data.get("levels", [])[skill_level].get("totalExpRequired", 0) - xp)) if skill_level != max_level else "Max level.",
                "\n".join(
                    [
                        f"- {reward}"
                        for reward in level.get("unlocks", [])
                    ]
                )
            )
        )

        await ctx.reply(embed=embed)




        



async def setup(bot: commands.Bot):
    global database
    database = bot.database

    cog = Games_cog()
    cog.bot = bot
    
    # Add attributes for sys.modules and globals() so the _reload_module() function in utility.custom can read it and get the module objects.
    cog.modules = sys.modules
    cog.globals = globals()
    
    await bot.add_cog(cog)