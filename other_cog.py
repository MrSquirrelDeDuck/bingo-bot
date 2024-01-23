"""This cog is for commands that don't fit in the other cogs."""

from discord.ext import commands
from scipy.stats import binom
from fuzzywuzzy import fuzz
import discord
import typing
import random
import wikipedia
import mpmath
import copy
import re
import asyncio
import aiohttp
import traceback
import time
import datetime, pytz
import cairosvg, chess, chess.svg

import sys

import utility.custom as u_custom
import utility.ciphers as u_ciphers
import utility.checks as u_checks
import utility.converters as u_converters
import utility.interface as u_interface
import utility.text as u_text
import utility.bread as u_bread
import utility.bingo as u_bingo
import utility.files as u_files
import utility.images as u_images

database = None # type: u_files.DatabaseInterface

class TruthOrDare_Buttons(discord.ui.View):
    def __init__(self, timeout=3600.0):
        super().__init__(timeout=timeout)
        self.state = None
        self.interaction = None

    @discord.ui.button(label='Truth', style=discord.ButtonStyle.green)
    async def truth(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.state = "truth"
        self.interaction = interaction
        self.stop()

    @discord.ui.button(label='Dare', style=discord.ButtonStyle.red)
    async def dare(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.state = "dare"
        self.interaction = interaction
        self.stop()
        
    @discord.ui.button(label='Random', style=discord.ButtonStyle.blurple)
    async def random(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.state = "random"
        self.interaction = interaction
        self.stop()

class TruthOrDare_Buttons_Disabled(discord.ui.View):
    def __init__(self, timeout=3600.0):
        super().__init__(timeout=timeout)
        self.state = None
        self.interaction = None

    @discord.ui.button(label='Truth', style=discord.ButtonStyle.green, disabled=True)
    async def truth(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()

    @discord.ui.button(label='Dare', style=discord.ButtonStyle.red, disabled=True)
    async def dare(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        
    @discord.ui.button(label='Random', style=discord.ButtonStyle.blurple, disabled=True)
    async def random(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()

async def send_truth_or_dare(ctx, type_input="truth", interaction=None):
    prompt_type = None

    if type_input == "random":
        if random.randint(1, 2) == 1:
            type_input = "truth"
            prompt_type = "RANDOM: TRUTH"
        else:
            type_input = "dare"
            prompt_type = "RANDOM: DARE"

    prompts = database.load("truth_or_dare")
    options = prompts[type_input]
    if prompt_type is None:
        prompt_type = type_input.upper()

    if interaction is None:
        author = ctx.author
    else:
        author = interaction.user

    embed = u_interface.embed(
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

class Other_cog(u_custom.CustomCog, name="Other", description="Commands that don't fit elsewhere, and are kind of silly."):
    bot = None

    minecraft_wiki_searching = False
    lichess_cooldown = 0

    traitor_game_going = False

    card_keys = card_keys = {'c1': '<a:ace_clubs:1122942670793363466>', 'd1': '<a:ace_diamonds:1122943540549386360>', 'h1': '<a:ace_hearts:1122943541379874838>', 's1': '<a:ace_spades:1122943543472820285>', 'c10': '<:10_clubs:1122941731319582720>', 'd10': '<:10_diamonds:1122941732728873041>', 'h10': '<:10_hearts:1122941734461112320>', 's10': '<:10_spades:1122941735190925496>', 'c2': '<:2_clubs:1122930420158312448>', 'd2': '<:2_diamonds:1122930421043318814>', 'h2': '<:2_hearts:1122930422934945932>', 's2': '<:2_spades:1122930424088379441>', 'c3': '<:3_clubs:1122930451246481458>', 'd5': '<:5_diamonds:1122930499887833160>', 'c5': '<:5_clubs:1122930498860220479>', 's4': '<:4_spades:1122930475414065185>', 'h4': '<:4_hearts:1122930474214510703>', 'd4': '<:4_diamonds:1122930471878271198>', 'c4': '<:4_clubs:1122930470653526066>', 's3': '<:3_spades:1122930454878769283>', 'h3': '<:3_hearts:1122930454044094484>', 'd3': '<:3_diamonds:1122930452416700548>', 'h5': '<:5_hearts:1122930501230006302>', 's5': '<:5_spades:1122930502458953889>', 'c6': '<:6_clubs:1122930520041455666>', 'd6': '<:6_diamonds:1122930521446567936>', 'h6': '<:6_hearts:1122930523145261167>', 's6': '<:6_spades:1122930524072198154>', 'c7': '<:7_clubs:1122930541327560752>', 'd7': '<:7_diamonds:1122930543139487814>', 'h7': '<:7_hearts:1122930544087408660>', 's9': '<:9_spades:1122941711438589952>', 'h9': '<:9_hearts:1122941710473904168>', 'd9': '<:9_diamonds:1122941709169463387>', 'c9': '<:9_clubs:1122941708125081762>', 's8': '<:8_spades:1122941690697748510>', 'h8': '<:8_hearts:1122941689271701664>', 'd8': '<:8_diamonds:1122930562777239674>', 'c8': '<:8_clubs:1122930561133072555>', 's7': '<:7_spades:1122930545043722342>', 'c11': '<:jack_clubs:1122941753759125525>', 'd11': '<:jack_diamonds:1122941755776569464>', 'h11': '<:jack_hearts:1122941756841926757>', 's11': '<:jack_spades:1122941757856952350>', 's12': '<:queen_spades:1122941804036239553>', 'h12': '<:queen_hearts:1122941803272884334>', 'd12': '<:queen_diamonds:1122941802442407936>', 'c12': '<:queen_clubs:1122941800722726992>', 's13': '<:king_spades:1122941784465608724>', 'h13': '<:king_hearts:1123679597188354208>', 'd13': '<:king_diamonds:1122941782028734484>', 'c13': '<:king_clubs:1122941779776381028>'}
    
    ######################################################################################################################################################
    ##### UTILITY FUNCTIONS ##############################################################################################################################
    ######################################################################################################################################################

    async def _cipher_translate(self: typing.Self, ctx: typing.Union[commands.Context, u_custom.CustomContext], cipher_function: typing.Callable, text: str, translation_type: str) -> discord.Message:
        """Does all the logic required to translate a piece of text with a cipher. Returns the sent message.

        Args:
            ctx (typing.Union[discord.Context, u_custom.CustomContext]): The context object.
            cipher_function (typing.Callable): The function that will be called.
            text (str): The text to translate.
            translation_type (str): String for what type of translation this is, "encode" or "decode"

        Returns:
            discord.Message: The sent message.
        """
        if u_interface.is_reply(ctx.message):
            text = ctx.message.reference.resolved.content
        
        if text is None or len(text) == 0:
            return await ctx.reply("I don't see anything to {} and unfortunately will not {} embeds.".format(translation_type, translation_type))
        
        translated = cipher_function(text)

        if len(translated) >= 2000:
            return await ctx.reply("Unfortunately that is simply to long to {}.".format(translation_type))
        
        if u_text.has_ping(translated):
            return await ctx.reply("I will not ping anyone.")
        
        return await ctx.reply(translated)
    
    async def _cipher_wikipedia(self: typing.Self, ctx: typing.Union[commands.Context, u_custom.CustomContext], cipher_function: typing.Callable) -> discord.Message:
        """Does all the logic required for the cipher Wikipedia messages.

        Args:
            ctx (typing.Union[commands.Context, u_custom.CustomContext]): The context.
            cipher_function (typing.Callable): The function that will be called.

        Returns:
            discord.Message: The sent message
        """
        
        page = wikipedia.page(wikipedia.random(pages=1))
        page_content = page.content.split("\n")[0]

        if len(page_content) >= 1000:
            page_content = page_content.split(".")[0]

        title = cipher_function(page.title)
        page_content = cipher_function(page_content)

        embed = u_interface.embed(
            title = title,
            description = page_content
        )
        await ctx.reply(embed=embed)

    ######################################################################################################################################################
    ##### AVATAR #########################################################################################################################################
    ######################################################################################################################################################

    @commands.command(
        name = "avatar",
        brief = "Get someone's avatar.",
        description = "Get someone's avatar.\nThis will use their global avatar, however the `display` parameter can be used to fetch server-specific avatars."
    )
    async def avatar(self, ctx,
            target: typing.Optional[discord.Member] = commands.parameter(description = "The member to use, if nothing is provided it'll use you."),
            display: typing.Optional[str] = commands.parameter(description = "If 'display' is provided it will use server avatars.")
        ):
        # If a target was specified or not.
        if target is None:
            target = ctx.author
        
        # If it should use the display avatar, rather than the global one.
        display = display == "display"
        
        # Get the avatar url.
        if display:
            avatar_url = target.display_avatar
        else:
            avatar_url = target.avatar
        
        # Send the url.
        await ctx.reply(avatar_url)

        
            

        
    ######################################################################################################################################################
    ##### SAY ############################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "say",
        brief = "Use wisely, and follow the rules.",
        description = "Use wisely, and follow the rules."
    )
    async def say(self, ctx,
            *, message: typing.Optional[str] = commands.parameter(description = "What you want me to say.")
        ):
        if message is None:
            await ctx.reply("||\n||")
            return
        
        bingo_data = u_bingo.live(database=database)
        
        # Rules list:
        # Must start with a capital letter.
        # Must end in a punctuation mark.
        # Must contain at least 1 number.
        # Must have the digits sum to a prime number.
        # Must contain at least 1 chess move in algebraic chess notation.
        # Must contain a number in the fibbonachi sequence that's between 100 and 1,000.
        # Must contain the first 7 digits of pi (after the decimal place).
        # Must contain the objective id of the objective in the top left of the daily board (3 characters)
        # Must contain the number of completed objectives on the weekly board.

        if not message[0].isupper():
            await ctx.reply("Please use proper capitalization.")
            return

        if not message[-1] in ".?!":
            await ctx.reply("Please use proper grammar.")
            return

        if not any([digit in message for digit in "0123456789"]):
            await ctx.reply("Please include at least one digit.")
            return
        
        if not u_checks.is_prime(sum([int(i) for i in list(str(u_text.return_numeric(message)))])):
            await ctx.reply("Please have the digits in the message sum to a prime number.")
            return
        
        if len(re.findall("([BNRQK]?([a-h]|[1-8])?x?[a-h][1-8](=[BNRQ])?(\+\+?|#)?)|(O-O(-O)?(\+\+?|#)?)", message)) == 0:
            await ctx.reply("Please include at least one Chess move in algebraic notation.")
            return
        
        if not str(bingo_data["daily_board_id"]) in message:
            await ctx.reply("Please include the board number of today's bingo board.")
            return

        if not any([digit in message for digit in ["144", "233", "377", "610", "987"]]):
            await ctx.reply("Please include at least one number between 100 and 1,000 that's in the Fibonacci sequence.")
            return
        
        if not "3.1415926" in message:
            await ctx.reply("Please include the first seven digits of pi in your message.")
            return
        
        if not bingo_data["daily_tile_string"][0:3] in message:
            await ctx.reply("Please include the 3 character objective id of the objective in the top left of today's bingo board.")
            return
        
        if not str((int(time.time()) // 3600 + 1) * 3600) in message:
            await ctx.reply("Please include the Unix Timestamp of the change of the next hour.")
            return
        
        if not str(sum(u_bingo.decompile_enabled(bingo_data["weekly_enabled"], 9))) in message:
            await ctx.reply("Please include the amount of objectives completed on this week's bingo board.")
            return
        
        if u_text.has_ping(message):
            await ctx.reply("Please remove all pings from your message.")
            return
        
        if random.randint(1, 10) == 1:
            await ctx.reply("Hmm, that's a weird message.")
            return
        
        print("Executing say command for {} with text: {}".format(ctx.message.author, message))
        await ctx.send(message)

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            # Missing permissions to delete the command message, oh well.
            pass
    


        
        
            

        
    ######################################################################################################################################################
    ##### CARD ###########################################################################################################################################
    ######################################################################################################################################################
    
    @commands.group(
        name = "card",
        brief = "Take a card, any card.",
        description = "Take a card, any card.",
        invoke_without_command = True,
        pass_context = True
    )
    async def card_command(self, ctx,
            card: typing.Optional[str] = commands.parameter(description = "The key of the card.")
        ):
        if ctx.invoked_subcommand is not None:
            return
        
        if card not in self.card_keys:
            await ctx.reply("https://cdn.discordapp.com/attachments/1032117556154204180/1122750787588730890/image.png")
            return
        
        await ctx.reply(self.card_keys[card])
        
    @card_command.command(
        name = "random",
        brief = "A random card, because why not?",
        description = "A random card, because why not?"
    )
    async def card_random(self, ctx):
        await ctx.reply(self.card_keys[random.choice(list(self.card_keys.keys()))])


        
        
            

        
    ######################################################################################################################################################
    ##### THANKS #########################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "thanks",
        brief = "Thanks the bot :3",
        description = "Thanks the bot :3"
    )
    async def thanks(self, ctx):
        await ctx.reply("You're welcome!")

        
            

        
    ######################################################################################################################################################
    ##### GOOD MORNING ###################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "good_morning",
        aliases = ["goodmorning"],
        brief = "Good morning!",
        description = "Good morning!"
    )
    async def good_morning(self, ctx):
        await ctx.reply("Good morning!")

        
            

        
    ######################################################################################################################################################
    ##### GOOD NIGHT #####################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "good_night",
        aliases = ["goodnight"],
        brief = "Good night!",
        description = "Good night!"
    )
    async def good_night(self, ctx):
        if random.randint(1, 32) == 1:
            await ctx.reply("Good horser!")
            return

        await ctx.reply("Good night!")

        
            

        
    ######################################################################################################################################################
    ##### PERCHANCE ######################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "perchance",
        brief = "You can't just say perchance.",
        description = "You can't just say perchance."
    )
    async def perchance(self, ctx):
        await ctx.reply("You can't just say perchance.")

        
            

        
    ######################################################################################################################################################
    ##### TYPING #########################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "typing",
        brief = "Typing...",
        description = "Typing..."
    )
    async def typing_command(self, ctx):
        async with ctx.typing():
            pass

        
            

        
    ######################################################################################################################################################
    ##### TETRIS #########################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "tetris",
        brief = "Random tetromino.",
        description = "Random tetromino."
    )
    async def tetris(self, ctx):
        await ctx.reply(random.choice(["O", "L", "The J", "S", "Z", "I", "T"]) + "-piece.")

        
            

        
    ######################################################################################################################################################
    ##### EWR ############################################################################################################################################
    ######################################################################################################################################################
    
    @commands.group(
        name = "ewr",
        brief = "Siwa ainwrgubf qurg rgw wqe xuogwe.",
        description = "Siwa ainwrgubf qurg rgw wqe xuogwe.",
        invoke_without_command = True,
        pass_context = True
    )
    async def ewr(self, ctx):
        if ctx.invoked_subcommand is not None:
            return
        
        await self._cipher_wikipedia(ctx, u_ciphers.ewr_encode)

    @ewr.command(
        name = "encode",
        brief = "Wbxisw rwzr ubri rgw wqe xuogwe.",
        description = "Wbxisw rwzr ubri rgw wqe xuogwe.",
    )
    async def ewr_encode(self, ctx,
            *, text: typing.Optional[str] = commands.parameter(description = "Rgw rwzr ri wbxisw.", displayed_name = "rwzr")
        ):
        await self._cipher_translate(ctx, u_ciphers.ewr_encode, text, "encode")

    @ewr.command(
        name = "decode",
        brief = "Decode text from the ewr cipher.",
        description = "Decode text from the ewr cipher.",
    )
    async def ewr_decode(self, ctx,
            *, text: typing.Optional[str] = commands.parameter(description = "The text to decode.")
        ):
        await self._cipher_translate(ctx, u_ciphers.ewr_decode, text, "decode")

        
            

        
    ######################################################################################################################################################
    ##### FDG ############################################################################################################################################
    ######################################################################################################################################################
    
    @commands.group(
        name = "fdg",
        brief = "Cldx xludgnkyb skgn gnd vcb ekpndf.",
        description = "Cldx xludgnkyb skgn gnd vcb ekpndf.",
        invoke_without_command = True,
        pass_context = True
    )
    async def fdg(self, ctx):
        if ctx.invoked_subcommand is not None:
            return
        
        await self._cipher_wikipedia(ctx, u_ciphers.fdg_encode)

    @fdg.command(
        name = "encode",
        brief = "Dyelcd gdwg kygl gnd vcb ekpndf.",
        description = "Dyelcd gdwg kygl gnd vcb ekpndf.",
    )
    async def fdg_encode(self, ctx,
            *, text: typing.Optional[str] = commands.parameter(description = "Gnd gdwg gl dyelcd.", displayed_name = "gdwg")
        ):
        await self._cipher_translate(ctx, u_ciphers.fdg_encode, text, "encode")

    @fdg.command(
        name = "decode",
        brief = "Decode text from the fdg cipher.",
        description = "Decode text from the fdg cipher.",
    )
    async def fdg_decode(self, ctx,
            *, text: typing.Optional[str] = commands.parameter(description = "The text to decode.")
        ):
        await self._cipher_translate(ctx, u_ciphers.fdg_decode, text, "decode")

        
            

        

    ######################################################################################################################################################
    ##### R○§ ############################################################################################################################################
    ######################################################################################################################################################
    
    @commands.group(
        name = "r○§",
        aliases = ["rp5", "r_circle_section"],
        brief = "Dd;{ ÷WJ0uh§°$ (GG3 tØ; $M5 ytpØ;?.",
        description = "Dd;{ ÷WJ0uh§°$ (GG3 tØ; $M5 ytpØ;?.",
        invoke_without_command = True,
        pass_context = True
    )
    async def r_circle_section(self, ctx):
        if ctx.invoked_subcommand is not None:
            return

        func = u_ciphers.fake_r_circle_section_encode

        if hasattr(ctx.guild, "id") and ctx.guild.id in [1101194105041719468, 1105943535804493955]:
            func = u_ciphers.r_circle_section_encode

        await self._cipher_wikipedia(ctx, func)

    @r_circle_section.command(
        name = "encode",
        brief = "Ec':]X G08t }'^] G3p g@= VGM3pr.",
        description = "Ec':]X G08t }'^] G3p g@= VGM3pr.",
    )
    async def r_circle_section_encode(self, ctx,
            *, text: typing.Optional[str] = commands.parameter(description = "TØ; ^X>G uo ;'[]LB.", displayed_name = "t○b}")
        ):
        func = u_ciphers.fake_r_circle_section_encode

        if hasattr(ctx.guild, "id") and ctx.guild.id in [1101194105041719468, 1105943535804493955]:
            func = u_ciphers.r_circle_section_encode

        await self._cipher_translate(ctx, func, text, "encode")

    @r_circle_section.command(
        name = "decode",
        brief = "Decode text from the r○§ cipher.",
        description = "Decode text from the r○§ cipher.",
    )
    async def r_circle_section_decode(self, ctx,
            *, text: typing.Optional[str] = commands.parameter(description = "The text to decode.")
        ):
        func = u_ciphers.fake_r_circle_section_decode

        if hasattr(ctx.guild, "id") and ctx.guild.id in [1101194105041719468, 1105943535804493955]:
            func = u_ciphers.r_circle_section_decode

        await self._cipher_translate(ctx, func, text, "decode")

        
            

        
    ######################################################################################################################################################
    ##### PI ############################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "pi",
        aliases = ["π"],
        brief = "Test your knowledge of π.",
        description = "Test your knowledge of π."
    )
    async def pi(self, ctx,
            guess: typing.Optional[str] = commands.parameter(description = "Your guess as to the value of pi.")
        ):
        if guess == "π":
            await ctx.reply("While that is technically correct, it does not test your knowledge of π.")
            return

        if not u_converters.is_float(guess): # This will catch None.
            await ctx.reply("You must provide a guess.")
            return
        
        guess = str(guess)

        if not guess.replace('.','',1).isdigit():
            await ctx.reply("You must provide a guess.")
            return
        
        if not guess.startswith("3."):
            await ctx.reply("I'll give you a hint, π starts with `3.`.")
            return
        
        if len(guess) == 2:
            await ctx.reply("That's a good start, but you might want to include at least one more digit.")
            return
        
        mpmath.mp.dps = len(guess) + 5
        correct = str(mpmath.mp.pi)

        if correct[:len(guess)] == guess:
            await ctx.reply("That's correct!")
            return

        for index, data in enumerate(zip(guess, correct)):
            if data[0] == data[1]:
                continue
            
            addition = "th"
            if str(index - 1).endswith("1") and not str(index - 1).endswith("11"):
                addition = "st"
            if str(index - 1).endswith("2") and not str(index - 1).endswith("12"):
                addition = "nd"
            if str(index - 1).endswith("3") and not str(index - 1).endswith("13"):
                addition = "rd"

            await ctx.reply("Unfortunately, that is incorrect.\nThe {}{} digit ({}) is not {} it is {}.".format(
                index - 1,
                addition,
                guess[index - 2:index] + "**" + data[0] + "**" + guess[index + 1:index + 3],
                data[0],
                data[1]
            ))

        
            

        
    ######################################################################################################################################################
    ##### PREPARE ########################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "prepare",
        brief = "Powering up the Grammar Cannon.",
        description = "Powering up the Grammar Cannon."
    )
    async def prepare(self, ctx,
            *, prepare: typing.Optional[str] = commands.parameter(description = "What to prepare.")
        ):
        if prepare is None:
            await ctx.reply("Powering up the Lack of Parameters Cannon.")
            return
        
        if u_text.has_ping(prepare):
            await ctx.reply("Powering up the [REDACTED] Cannon")
            return
        
        if len(prepare) > 200:
            await ctx.reply("Powering up the Character Limits Cannon.")
            return
        
        await ctx.reply("Powering up the {} Cannon".format(prepare.title()))

        
            

        
    ######################################################################################################################################################
    ##### SUMMMON ########################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "summon",
        brief = "Summoning the Grammar Cannon.",
        description = "Summoning the Grammar Cannon."
    )
    async def summon(self, ctx,
            *, summon: typing.Optional[str] = commands.parameter(description = "What to summon.")
        ):
        if summon is None:
            await ctx.reply("Summoning the Lack of Parameters Cannon.")
            return
        
        if u_text.has_ping(summon):
            await ctx.reply("Summoning the [REDACTED] Cannon")
            return
        
        if len(summon) > 200:
            await ctx.reply("Summoning the Character Limits Cannon.")
            return
        
        await ctx.reply("Summoning the {} Cannon".format(summon.title()))

        
            

        
    ######################################################################################################################################################
    ##### BRICK ##########################################################################################################################################
    ######################################################################################################################################################
    
    @commands.group(
        name = "brick",
        brief = "Brick-related utility commands.",
        description = "Brick-related utility commands."
    )
    async def brick(self, ctx):
        if ctx.invoked_subcommand is not None:
            return
        
        await ctx.send_help(self.brick)

        
            

        
    ######################################################################################################################################################
    ##### BRICK ANALYZE ##################################################################################################################################
    ######################################################################################################################################################
    
    @brick.command(
        name = "analyze",
        aliases = ["analyse", "analysis"],
        brief = "Analyzes brick stats messages.",
        description = "Analyzes brick stats messages, note that replying to the brick stats message is required."
    )
    async def brick_analyze(self, ctx):
        replied_to = u_interface.replying_mm_checks(ctx.message, False, True)
        if not replied_to:
            await ctx.reply("You must reply to the stats of someone who has been bricked at least once.")
            return
        
        if replied_to.content.startswith("$brick stats"):
            await ctx.reply("No, a message from Machine-Mind that is someone's brick stats.")
            return
        
        # If it doesn't start with "Brick stats for" or if it ends with ".", "?", or "!" then it's not a brick stats message.
        if not(replied_to.content.startswith("Brick stats for") or replied_to.content[-1] in ".?!"):
            await ctx.reply("You must reply to the stats of someone who has been bricked at least once.")
            return
        
        parsed = u_bread.parse_stats(replied_to)["stats"]

        bricks = parsed["bricks"]
        gold = parsed["brick_gold"]
        total = parsed["total_bricks"]

        # Timeout information
        total_timeout = parsed["total_timeout"]
        extra_timeout = parsed["total_timeout"] - parsed["total_bricks"]

        timeout_time = []

        time_copy = copy.deepcopy(total_timeout)

        if time_copy >= 43200 and total >= 43200: # 1 month, 60 * 24 * 30
            timeout_time.append(u_text.smart_text(time_copy // 43200, "month"))
            time_copy = time_copy % 43200

        if time_copy >= 15840 and total >= 15840: # 1 Scaramucci, 60 * 24 * 11
            timeout_time.append(u_text.smart_text(time_copy // 15840, "Scaramucci"))
            time_copy = time_copy % 15840

        if time_copy >= 1440: # 1 day, 60 * 24
            timeout_time.append(u_text.smart_text(time_copy // 1440, "day"))
            time_copy = time_copy % 1440

        if time_copy >= 60: # 1 hour.
            timeout_time.append(u_text.smart_text(time_copy // 60, "hour"))
            time_copy = time_copy % 60
        
        timeout_time.append(u_text.smart_text(time_copy, "minute"))

        username = re.search("Brick stats for (.+):", replied_to.content).group(1)

        percent_bricked = "*Specific information unavailable due to non-matching usernames.*"

        if username == u_interface.get_display_name(ctx.author):
            # User is correct.
            join = ctx.author.joined_at
            now = ctx.message.created_at

            minutes_since_join = int((now - join).total_seconds() // 60)

            percent_bricked = "Time spent in server timed out: {}%".format(round((total_timeout / minutes_since_join) * 100, 3))

        # Gold brick info:
        exact_odds = round(binom.pmf(k = gold, n = total, p = (1 / 32)) * 100, 2)
        gold_brick_chance = round(binom.cdf(k = gold, n = total, p = (1 / 32)) * 100, 2)
        half = "Bottom"

        if gold_brick_chance > 50:
            gold_brick_chance = 100 - gold_brick_chance
            half = "Top"

        embed = u_interface.embed(
            title = "Brick analysis",
            description = ":bricks:: {}\n<:brick_gold:971239215968944168>: {}\nTotal bricks: {}".format(
                        u_text.smart_number(bricks),
                        u_text.smart_number(gold),
                        u_text.smart_number(total)),
            fields = [
                (
                    "Timeout information",
                    "Total timeout: {}\nExtra timeout: {}\nTimeout time: {}\n{}".format(
                        u_text.smart_number(total_timeout),
                        u_text.smart_number(extra_timeout),
                        ", ".join(timeout_time),
                        percent_bricked
                    ),
                    False
                ),
                (
                    "Gold brick information",
                    "Gold brick percentage: {}%\nExpected golds: {}\nGold brick odds:\n- {} {}%\n- Exact odds: {}%".format(
                        round(gold / total * 100, 2),
                        round(total / 32, 2),
                        half, gold_brick_chance,
                        exact_odds        
                    ), 
                    False
                )
            ]
        )

        await ctx.reply(embed=embed)

        
            

        
    ######################################################################################################################################################
    ##### XKCD #######################################################################################################################################
    ######################################################################################################################################################
        
    @commands.group(
        name = "xkcd",
        brief = "Get an xkcd strip.",
        description = "Get an xkcd strip.\n`random` can be used to get a random strip.",
        invoke_without_command = True,
        pass_context = True
    )
    async def xkcd(self, ctx,
            strip_id: typing.Optional[str] = commands.parameter(description = "The strip id to get, or 'random' for a random strip.")
        ):
        if ctx.invoked_subcommand is not None:
            return

        async with aiohttp.ClientSession() as session:
            if strip_id is None or strip_id == "random":
                returned = await session.get("https://xkcd.com/info.0.json")
                if returned.status != 200:
                    await ctx.reply("Something went wrong when getting the comic strip.")
                    return
                
                json_data = await returned.json()
                
                if strip_id == "random":
                    strip_id = random.randint(1, json_data["num"])
            
            if strip_id is not None:
                returned = await session.get("https://xkcd.com/{}/info.0.json".format(strip_id))
                if returned.status != 200:
                    await ctx.reply("That strip was not found.")
                    return
                
                json_data = await returned.json()
        
        strip_id = json_data["num"]
        
        embed = u_interface.embed(
            title = "{}: {}".format(strip_id, json_data["safe_title"]),
            title_link = "https://xkcd.com/{}/".format(strip_id),
            image_link = json_data["img"],
            footer_text = json_data["alt"]
        )

        await ctx.reply(embed=embed)
    
    @xkcd.command(
        name = "ping",
        description = "Pinglist for new xkcd strips!\nUse '%xkcd ping on' to get on the pinglist and '%xkcd ping off' to leave it.",
        brief = "Pinglist for new xkcd strips!"
    )
    async def xkcd_ping(self, ctx,
            state: typing.Optional[str] = commands.parameter(description = "'on' to join the ping list, 'off' to leave.")
        ):
        new_state = False

        if state in ["on", "off"]:
            new_state = state == "on"
        else:
            on_pinglist = database.user_on_ping_list("xkcd_strips", ctx.author.id)

            new_state = not on_pinglist

        database.update_ping_list("xkcd_strips", ctx.author.id, new_state)

        embed = u_interface.embed(
            title = "xkcd strip ping list",
            description = "You will {} be pinged for new xkcd strips.".format("now" if new_state else "no longer")
        )
        await ctx.reply(embed=embed)


        
            

        
    ######################################################################################################################################################
    ##### ASKOUIJA #######################################################################################################################################
    ######################################################################################################################################################
        
    @commands.command(
        name = "askouija",
        aliases = ["ask_ouija"],
        brief = "Ask the spirits a question.",
        description = "Ask the spirits a question."
    )
    async def askouija(self, ctx,
            *, question: typing.Optional[str] = commands.parameter(description = "The question to ask the spirits.")
        ):
        if u_checks.sensitive_check(ctx.channel):
            await ctx.reply("This is not the channel for that.")
            return

        channel_data = database.get_ouija_data(ctx.channel.id)

        if question is None:
            if channel_data["active"]:
                await ctx.reply("Current letters: {}".format(channel_data["letters"]))
            else:
                await ctx.reply("There is no question going on in this channel.\nYou can ask a question via `%askouija <question>`.")
            return
        
        if channel_data["active"]:
            await ctx.reply("There is already a question going on in this channel.")
            return
        
        if u_text.has_ping(question):
            await ctx.reply("Question cannot contain any pings.")
            return
        
        database.set_ouija_data(
            channel_id = ctx.channel.id,
            active = True,
            letters = "",
            message_id = ctx.message.id,
            author_id = ctx.author.id
        )

        await ctx.send("Spirits, you are being asked a question:\n{}".format(question))


        
            

        
    ######################################################################################################################################################
    ##### GET COUNT ######################################################################################################################################
    ######################################################################################################################################################
        
    @commands.command(
        name = "get_count",
        brief = "Retrieves the current count.",
        description = "Retrieves the current count."
    )
    async def get_count(self, ctx):
        if u_checks.sensitive_check(ctx.channel):
            await ctx.reply("This is not the channel for that.")
            return
        
        counting_data = database.get_counting_data(ctx.channel.id)

        if counting_data["count"] == 0:
            await ctx.reply("There is no count here yet! Send `1` to start it.")
            return
        
        await ctx.reply("The current count is {}.".format(u_text.smart_number(counting_data["count"])))
        


        
            

        
    ######################################################################################################################################################
    ##### TRAITOR #######################################################################################################################################
    ######################################################################################################################################################
        
    @commands.command(
        name = "traitor",
        brief = "Starts a game of Traitor.",
        description = "Starts a game of Traitor, a game where one player is the traitor and everyone else is innocent.\nThis will DM players involved whether they are the traitor or not 2 minutes after the game starts."
    )
    async def traitor(self, ctx):
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
    ##### FLIP COIN ######################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "flip_coin",
        aliases = ["coin_flip"],
        brief = "Yep, it's just a coin flip.",
        description = "Yep, it's just a coin flip."
    )
    async def flip_coin(self, ctx):
        await ctx.reply(random.choice(["Heads.","Tails."]))

        
            

        
    ######################################################################################################################################################
    ##### WEEKDAY ########################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "weekday",
        brief = "Tells you the current day of the week in EDT.",
        description = "Tells you the current day of the week in EDT."
    )
    async def weekday(self, ctx):
        await ctx.reply(datetime.datetime.today().astimezone(pytz.timezone("US/Eastern")).strftime('%A') + ".")

        
            

        
    ######################################################################################################################################################
    ##### TRUTH OR DARE ##################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "truth_or_dare",
        brief = "Truth or dare?",
        description = "Truth or dare?"
    )
    async def truth_or_dare(self, ctx):
        await send_truth_or_dare(ctx, "random")
    
    @commands.command(
        name = "truth",
        brief = "The truth part of Truth or Dare.",
        description = "The truth part of Truth or Dare."
    )
    async def truth(self, ctx):
        await send_truth_or_dare(ctx, "truth")

    @commands.command(
        name = "dare",
        brief = "The dare part of Truth or Dare.",
        description = "The dare part of Truth or Dare."
    )
    async def dare(self, ctx):
        await send_truth_or_dare(ctx, "dare")

        
            

        
    ######################################################################################################################################################
    ##### ROLE LEADERBOARD ##########################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "role_leaderboard",
        brief = "A leaderboard for roles.",
        description = "A leaderboard for roles."
    )
    async def role_leaderboard(self, ctx,
            member: typing.Optional[discord.Member] = commands.parameter(description = "The member to view.")
        ):
        if member is None:
            member = ctx.author

        role_data = u_interface.get_role_list(ctx.guild)

        prune_ids = [958920155025539132, 959220485672026142, 980602604847501362, 958920201557119036, 958920265792892938, 958920326006308914, 970619771374690345, 960928696368259113, 961216939198410792, 960928234273394689, 958737602859655178, 958737525139177492, 958737469635981362, 958737300236406905, 958737243885932564, 958736931246706698, 970574059727380520, 958736670323269742, 958736276415205436, 982060564077498418, 970550144477040650, 962130208700379216, 1118418774966665276, 1118415419125026857, 1118415313277558794, 1118415111124701184, 1138140416064102410, 1118415718065635329, 1118415622599098390, 1118415511752024105, 1177067611348008970, 1177067684744142888, 1177067733695864942, 975082724501098557, 959247044701216848, 1157009850455302234, 1119317224604307586, 958920124314816532, 970549665055522850, 1119445209923723396, 958512048306815056, 958755031820161025, 1023757953687363634]
        prune_ids.append(ctx.guild.id)

        role_counts = [
            (
                key,
                len([role_id for role_id in role_data[key] if role_id not in prune_ids])
            )
            for key in role_data
        ]

        sorted_data = sorted(role_counts, key=lambda x: x[1], reverse=True)

        target_location = 0
        for i in range(len(sorted_data)):
            if sorted_data[i][0] == member.id:
                target_location = i
                break

        lines = []
        last = 0
        for index, data in enumerate(sorted_data):
            if not (index <= 9 or abs(target_location - index) <= 3):
                continue

            if abs(last - index) >= 2:
                lines.append("")
            
            bold = "**" if data[0] == member.id else ""
            
            iter_member = discord.utils.find(lambda m: m.id == data[0], ctx.guild.members)

            display_name = u_interface.get_display_name(iter_member)
            if u_text.has_ping(display_name):
                display_name = iter_member.name

            lines.append(f"{index + 1}. {bold}{display_name}: {data[1]}{bold}")
            last = index
        
        embed = u_interface.embed(
            title = "Role leaderboard",
            description = "*This is excluding reaction roles.*",
            fields = [("", "\n".join(lines), False)],
            footer_text = "You can use '%role_leaderboard <user>' to highlight someone else."
        )
        
        await ctx.reply(embed=embed)

        
            

        
    ######################################################################################################################################################
    ##### LICHESS ########################################################################################################################################
    ######################################################################################################################################################

    @commands.command(
        name = "lichess",
        brief = "Get information about a Lichess tournament.",
        description = "Get information about a Lichess tournament."
    )
    async def lichess(self, ctx,
            tournament: typing.Optional[str] = commands.parameter(description = "The id of the tournament to look up.")
        ):
        if time.time() <= self.lichess_cooldown:
            await ctx.reply("This command is on cooldown, please wait a minute before trying again.")
            return
        
        async with aiohttp.ClientSession() as session:
            if tournament is None:
                returned = await session.get(f"https://lichess.org/api/tournament")
                tournament = (await returned.json())["started"][0]["id"]

            returned = await session.get(f"https://lichess.org/api/tournament/{tournament}")
            await session.close()
        
        if returned.status == 249:
            self.lichess_cooldown = time.time() + 65
            await ctx.reply("This command is on cooldown, please wait a minute before trying again.")
            return
        
        if returned.status == 404:
            await ctx.reply("That tournament does not exist.")
            return
        
        if returned.status != 200:
            await ctx.reply("Something went wrong in the request, make sure you have the tournament id correct.")
            return
        
        ret_json = await returned.json()

        time_control = ret_json["clock"]["limit"]

        time_control /= 60

        if time_control % 1 == 0:
            time_control = int(time_control)
        elif time_control == "0.25":
            time_control = "¼"
        elif time_control == "0.5":
            time_control = "½"
        elif time_control == "0.75":
            time_control = "¾"

        checkboxes = ["<:x_:1189696918645907598>", "<:check:1189696905077325894>"]

        length_days = ret_json["minutes"] // 1440
        length_hours = (ret_json["minutes"] % 1440) // 60
        length_minutes = (ret_json["minutes"] % 1440) % 60

        footer = None
        if "quote" in ret_json:
            footer = "\"{}\" - {}".format(ret_json["quote"]["text"], ret_json["quote"]["author"])
        
        finish_info = "Finished."

        if "isFinished" in ret_json:
            finish_info = "Finished."
        elif "isStarted" in ret_json:
            finish_info = f"In progress, ends <t:{int(time.time() + ret_json['secondsToFinish'])}:R>"
        else:
            finish_info = f"Hasn't started yet! Starts <t:{int(time.time() + ret_json['secondsToStart'])}:R>."

        spotlight = ""
        if "spotlight" in ret_json:
            spotlight = f'*{ret_json["spotlight"]["headline"]}*'

        description = ""
        if "description" in ret_json:
            description = f'*{ret_json["description"]}*'

        fields = []

        fields.append(
            ("Game information:", f"Time control: {ret_json['perf']['name']} {time_control}+{ret_json['clock']['increment']}\nVariant: {ret_json['variant'].title()}\nRated: {checkboxes[ret_json['rated']]}\nBeserkable: {checkboxes[ret_json['berserkable']]}", True),
        )
        fields.append(
            ("Leaderboard:", "\n".join(["**#{}:** [{}](<https://lichess.org/@/{}>) (*{}*) **{}** points.".format(player + 1, ret_json["standing"]["players"][player]["name"], ret_json["standing"]["players"][player]["name"], u_text.smart_number(ret_json["standing"]["players"][player]["rating"]), u_text.smart_number(ret_json["standing"]["players"][player]["score"])) for player in range(5)]), True)
        )

        image = None
        image_file = None

        if "isStarted" in ret_json:
            # Game in progress.
            board_fen = ret_json["featured"]["fen"]
            last_move = ret_json["featured"]["lastMove"]

            last_move = chess.Move(chess.parse_square(last_move[:2]), chess.parse_square(last_move[2:]))

            board = chess.Board(board_fen)

            board_svg = chess.svg.board(board, lastmove=last_move)

            cairosvg.svg2png(bytestring=board_svg,write_to='images/generated/chess_position.png')

            fields.append(
                ("Highlighted game:", f"White: {ret_json['featured']['white']['name']} (*{u_text.smart_number(ret_json['featured']['white']['rating'])}*)\nBlack: {ret_json['featured']['black']['name']} (*{u_text.smart_number(ret_json['featured']['black']['rating'])}*)", False)
            )

            image = "attachment://chess_position.png"
            
            image_file = discord.File("images/generated/chess_position.png", filename="chess_position.png")

        
        embed = u_interface.embed(
            title = ret_json["fullName"],
            title_link = f"https://lichess.org/tournament/{tournament}",
            description = "{}\n\n{}\n\nNumber of players: **{}**\n\nTournament status:\n{}\n\nTournament length: {} {} and {}\nTournament id: {}".format(
                spotlight,
                description,
                u_text.smart_number(ret_json['nbPlayers']),
                finish_info,
                u_text.smart_text(length_days, "day"), u_text.smart_text(length_hours, "hour"), u_text.smart_text(length_minutes, "minute"),
                ret_json["id"]
            ),
            fields = fields,
            footer_text = footer,
            image_link = image
        )

        await ctx.reply(embed = embed, file = image_file)
        
            

        
    ######################################################################################################################################################
    ##### EMOJI ##########################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "emoji",
        brief = "Searches for an emoji, or gives an image.",
        description = "If given a custom emoji, it will send the image for that emoji, otherwise it will search for whatever text is given."
    )
    async def emoji_command(self, ctx,
            *, text: typing.Optional[str] = commands.parameter(description = "The emoji, or text to search for.")
        ):
        matched = re.search("<a?:\w+:(\d+)>", text)
        
        if matched is None:
            await ctx.reply(await self._emoji_search(text))
            return
    
        emoji_id = matched.group(1)
        file_extension = "gif" if matched.group(0)[1] == "a" else "png"

        embed = u_interface.embed(
            title = "Emoji image",
            image_link = f"https://cdn.discordapp.com/emojis/{emoji_id}.{file_extension}"
        )
        await ctx.reply(embed=embed)
        


    async def _emoji_search(self, text: str) -> str:
        
        def score_emoji(emoji_text: str) -> float:
            return fuzz.partial_ratio(text.lower(), u_text.return_alphanumeric(emoji_text.lower()))
        
        emoji_list = [] # type: list[tuple[str, float]]

        for guild in self.bot.guilds:
            for emoji in guild.emojis:
                emoji_list.append((str(emoji), score_emoji(emoji.name)))
        
        emoji_data = database.load_json_file("data/emoji_data.json") # This file isn't loaded into the database since it's really large and also shouldn't be changing.
        for data in emoji_data:
            emoji_list.append((data["text"], score_emoji(data["name"])))
        
        emoji_list = sorted(emoji_list, key=lambda x: x[1], reverse=True)

        return " ".join([emoji_list[i][0] for i in range(25)])

        
            

        
    ######################################################################################################################################################
    ##### MINECRAFT ######################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "minecraft",
        brief = "Search the Minecraft Wiki!",
        description = "Search the Minecraft Wiki."
    )
    async def minecraft(self, ctx,
            *, search_term: typing.Optional[str] = commands.parameter(description = "The search term to search the wiki with.")
        ):
        if search_term is None:
            await ctx.reply("Here's a link to the wiki:\n<https://minecraft.wiki/>\nIf you want to search the wiki, use `%minecraft wiki <search term>`.")
            return
        
        if self.minecraft_wiki_searching:
            await ctx.reply("This commmand is currently being used somewhere, please wait until it's done to try again.")
            return
        
        async def error_message(embed: discord.Embed, sent_message: discord.Message) -> None:
            """Changes all 'Waiting to be loaded' messages to 'Something went wrong'"""
            modified = 0

            for field_id, field in enumerate(embed.fields):
                if "Waiting to be loaded" not in field.value:
                    continue
                
                embed.set_field_at(field_id, name=field.name, value=field.value.replace("Waiting to be loaded", "Something went wrong"), inline=field.inline)
                modified += 1
            
            if modified >= 1:
                await sent_message.edit(content=sent_message.content, embed=embed)
        
        embed = None
        sent_message = None

        try:
            self.minecraft_wiki_searching = True

            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://minecraft.wiki/api.php?format=json&action=query&list=search&srlimit=3&srsearch={search_term}&redirects=true") as resp:
                    if resp.status != 200:
                        self.minecraft_wiki_searching = False
                        await ctx.reply("Something went wrong.")
                        return
                    
                    ret_json = await resp.json()

                description_prefix = f"Search results after searching for '{search_term}' on [The Minecraft Wiki](https://minecraft.wiki/):"
                
                if ret_json["query"]["searchinfo"]["totalhits"] == 0:
                    embed = u_interface.embed(
                        title = "Minecraft Wiki",
                        description = f"{description_prefix}\n\nThe search did not find any results, try different search terms."
                    )
                    await ctx.reply(embed=embed)
                    self.minecraft_wiki_searching = False
                    return
                
                search_results = []

                for page_info in ret_json["query"]["search"]:                    
                    search_results.append(page_info["title"])

                fields = [
                    (page_name, "[Link to wiki page.](https://minecraft.wiki/w/{})\n\n*Waiting to be loaded.*".format(page_name.replace(" ", "_")), True)
                    for page_name in search_results
                ]

                embed = u_interface.embed(
                    title = "Bread Wiki",
                    description = f"{description_prefix}",
                    fields = fields + [("", "Not what you're looking for? Try different search terms.", False)]
                )

                sent_message = await ctx.reply(embed=embed)

                async with session.get("https://minecraft.wiki/api.php?action=query&prop=revisions&titles={}&rvslots=*&rvprop=content&formatversion=2&format=json&redirects=true".format("|".join(search_results))) as resp:
                    if resp.status != 200:
                        self.minecraft_wiki_searching = False
                        await ctx.reply("Something went wrong.")
                        return
                    
                    ret_json = await resp.json()

                wiki_data = {}
                for data in ret_json["query"]["pages"]:
                    wiki_data[data["title"]] = data["revisions"][0]["slots"]["main"]["content"]

                redirect_data = {}
                if "redirects" in ret_json["query"]:
                    for data in ret_json["query"]["redirects"]:
                        redirect_data[data["from"]] = {"to": data["to"], "fragment": data.get("tofragment", None)}

                for field_id, page in enumerate(search_results):
                    page_get = page
                    page_fragment = None

                    redirect_text = ""
                    
                    for redirect_count in range(50):
                        if page_get in redirect_data:
                            page_fragment = redirect_data[page_get]["fragment"]
                            page_get = redirect_data[page_get]["to"]
                            redirect_text = f"*Redirected to {page_get}*\n"
                            continue
                        break

                    if page_fragment is None:
                        page_fragment = page_get
                    
                    sections = u_text.parse_wikitext(wiki_data[page_get], wiki_link="https://minecraft.wiki/w/", page_title=page_get, return_sections=True)
                    
                    summary = "[Link to wiki page.](https://minecraft.wiki/w/{})\n{}\n{}".format(page.replace(" ", "_"), redirect_text, sections[page_fragment])

                    if len(summary) > 900:
                        summary = self._wiki_correct_length(summary, 900)

                    embed.set_field_at(field_id, name=page, value=summary, inline=True)

                await sent_message.edit(content=sent_message.content, embed=embed)

            self.minecraft_wiki_searching = False
        except:
            self.minecraft_wiki_searching = False
            print(traceback.format_exc())

            if embed is not None and sent_message is not None:
                await error_message(embed, sent_message)

        
            

        
    ######################################################################################################################################################
    ##### D&D ######################################################################################################################################
    ######################################################################################################################################################
    
    @commands.group(
        name = "dnd",
        aliases = ["d&d", "DnD", "D&D", "DND"],
        brief = "A few utility commands for D&D.",
        description = "A few utility commands for Dungeons and Dragons.",
        invoke_without_command = True,
        pass_context = True
    )
    async def dnd_command(self, ctx):
        if ctx.invoked_subcommand is not None:
            return
        
        await ctx.send_help(self.dnd_command)
    
    @dnd_command.command(
        name = "roll",
        brief = "Roll some dice.",
        description = "Roll some dice."
    )
    async def dnd_roll(self, ctx,
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
        
        embed = u_interface.embed(
            title = "{}d{}".format(dice_amount, dice_sides),
            description = "Total: **{}**\n\n**Roll distribution:**\n{}".format(
                u_text.smart_number(sum(rolled)),
                " | ".join(["{}: {}".format(u_text.smart_number(i), u_text.smart_number(rolled.count(i))) for i in range(1, int(dice_sides) + 1) if i in rolled]),
            ),
            image_link = "attachment://graph.png"
        )
        await ctx.reply(embed=embed, file=discord.File(image_path, filename="graph.png"))

        


async def setup(bot: commands.Bot):
    cog = Other_cog()
    cog.bot = bot

    global database
    database = bot.database
    
    # Add attributes for sys.modules and globals() so the _reload_module() function in utility.custom can read it and get the module objects.
    cog.modules = sys.modules
    cog.globals = globals()
    
    await bot.add_cog(cog)