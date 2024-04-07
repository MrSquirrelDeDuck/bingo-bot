"""This cog is for commands that don't fit in the other cogs."""

from discord.ext import commands
import discord
import typing
import random
import copy
import re
import time
import datetime
import os
from os.path import sep as SLASH
import difflib

# pip install python-dateutil
import dateutil

# pip install CairoSVG
import cairosvg

# pip install chess
import chess
import chess.svg

# pip install pytz
import pytz

# pip install aiohttp
import aiohttp

# pip install scipy
from scipy.stats import binom

# pip install mpmath
import mpmath

# pip install wikipedia
import wikipedia

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
import utility.stonks as u_stonks

database = None # type: u_files.DatabaseInterface

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

class Other_cog(
        u_custom.CustomCog,
        name="Other",
        description="Commands that don't fit elsewhere, and are kind of silly."
    ):
    bot = None

    minecraft_wiki_searching = False
    vdc_wiki_searching = False
    lichess_cooldown = 0
    
    ######################################################################################################################################################
    ##### UTILITY FUNCTIONS ##############################################################################################################################
    ######################################################################################################################################################

    async def _cipher_translate(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            cipher_function: typing.Callable,
            text: str,
            translation_type: str
        ) -> discord.Message:
        """Does all the logic required to translate a piece of text with a cipher. Returns the sent message.

        Args:
            ctx (commands.Context | u_custom.CustomContext): The context object.
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
    
    async def _cipher_wikipedia(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            cipher_function: typing.Callable
        ) -> discord.Message:
        """Does all the logic required for the cipher Wikipedia messages.

        Args:
            ctx (commands.Context | u_custom.CustomContext): The context.
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

        embed = u_interface.gen_embed(
            title = title,
            description = page_content
        )
        await ctx.reply(embed=embed)

    def hourly_task(self: typing.Self) -> None:
        """Code that runs for every hour."""
        self.minecraft_wiki_searching = False
        self.vdc_wiki_searching = False

    ######################################################################################################################################################
    ##### AVATAR #########################################################################################################################################
    ######################################################################################################################################################

    @commands.command(
        name = "avatar",
        aliases = ["pfp"],
        brief = "Get someone's avatar.",
        description = "Get someone's avatar.\nThis will use their global avatar, however the `display` parameter can be used to fetch server-specific avatars."
    )
    async def avatar(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
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

        # Setup the embed to send.
        title = "Display avatar" if display else "Avatar"
        embed = u_interface.gen_embed(
            title = title,
            description = "{} for {}:".format(title, target.mention),
            image_link = avatar_url
        )
        
        # Send the embed.
        await ctx.reply(embed=embed)

        
            

        
    ######################################################################################################################################################
    ##### SAY ############################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "say",
        brief = "Use wisely, and follow the rules.",
        description = "Use wisely, and follow the rules."
    )
    async def say(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            *, message: typing.Optional[str] = commands.parameter(description = "What you want me to say.")
        ):
        if message is None:
            await ctx.reply("||\n||")
            return

        # If it's a sub-admin, just go with it.
        if u_checks.sub_admin_check(ctx):
            await ctx.send(message)
    
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                # Missing permissions to delete the command message, oh well.
                pass

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
        # Must contain a custom emoji.
        # Must contain the sum of the current stonk values, but bolded.
        # Must contain one of a few :3 pieces of text.
        # Must contain one of a few server references.
        # Must include the given text, but encoded in ewr.

        if not message[0].isupper():
            await ctx.reply("Please use proper capitalization.")
            return

        if not message[-1] in ".?!":
            await ctx.reply("Please use proper grammar.")
            return
        
        emojis_removed = u_interface.remove_emojis(message)

        if not any([digit in emojis_removed for digit in "0123456789"]):
            await ctx.reply("Please include at least one digit.")
            return
        
        if not u_checks.is_prime(sum([int(i) for i in list(str(u_text.return_numeric(emojis_removed)))])):
            await ctx.reply("Please have the digits in the message sum to a prime number.")
            return
        
        if len(u_text.extract_chess_moves(message)) == 0:
            await ctx.reply("Please include at least one Chess move in algebraic notation.")
            return
        
        if not str(bingo_data["daily_board_id"]) in emojis_removed:
            await ctx.reply("Please include the board number of today's bingo board.")
            return

        if not any([digit in emojis_removed for digit in ["144", "233", "377", "610", "987"]]):
            await ctx.reply("Please include at least one number between 100 and 1,000 that's in the Fibonacci sequence.")
            return
        
        if not "3.1415926" in message:
            await ctx.reply("Please include the first seven digits of pi in your message.")
            return
        
        if not bingo_data["daily_tile_string"][0:3] in emojis_removed:
            await ctx.reply("Please include the 3 character objective id of the objective in the top left of today's bingo board.")
            return
        
        if not str((int(time.time()) // 3600 + 1) * 3600) in emojis_removed:
            await ctx.reply("Please include the Unix Timestamp of the change of the next hour.")
            return
        
        if not str(sum(u_bingo.decompile_enabled(bingo_data["weekly_enabled"], 9))) in emojis_removed:
            await ctx.reply("Please include the amount of objectives completed on this week's bingo board.")
            return
        
        if re.search("<a?:\w+:\d+>", message) is None:
            await ctx.reply("Please include at least one custom emoji.")
            return
        
        current_values = u_stonks.current_values(database)

        stonk_sum = str(sum(current_values.values()))
        bolded_matches = re.finditer("\*\*([\w\W]+?)\*\*", message)

        for match in bolded_matches:
            if stonk_sum in match.group(1).replace(",", ""):
                break
        else: # If it did not break out of the loop.
            await ctx.reply("Please include the sum of the current stonk values, bolded.")
            return

        possible = [
            "nyaaaa",
            ":3",
            "prrrrr",
            "owo",
            "^u^",
            "^w^"
        ]
        chosen = random.Random(time.time() // 300).choice(possible) # Changes every 5 minutes.

        if chosen not in message:
            await ctx.reply(f"Please include '{chosen}' in your message.")
            return

        possible = [
            "boingo bot peak",
            "what the fuck is a bee",
            "i am clean",
            "that's right, it goes in the square hole",
            "Hey there, cheez wiz!!",
            "I didn't get the memo."
        ]
        chosen = random.Random((time.time() + 150) // 300).choice(possible) # Changes every 5 minutes, offset by 2.5 minutes from the previous one.
        
        if f"!! {chosen} !!" not in message:
            await ctx.reply(f"Please include '!! {chosen} !!' in your message.")
            return
        
        seeded = random.Random(time.time() // 600) # Changes every 10 minutes.
        letters = "abcdefghijklmnopqrstuvwxyz"
        sentence_count = seeded.randint(1, 3)
        words = []
        for sentence in range(sentence_count):
            word_count = seeded.randint(5, 10)
            for word_id in range(word_count):
                letter_count = seeded.randint(1, 8)
                out = []
                for _ in range(letter_count):
                    out.append(seeded.choice(letters))
                
                if word_id == word_count - 1:
                    out.append(".")
                
                if word_id == 0:
                    out[0] = out[0].upper()
                words.append("".join(out))

        text = " ".join(words)

        encoded = u_ciphers.ewr_encode(text)

        if encoded not in message:
            await ctx.reply(f"Please include the text '{text}' in your message, but encoded in ewr.")
            return
        
        if u_text.has_ping(message):
            await ctx.reply("Please remove all pings from your message.")
            return
        
        if random.randint(1, 5) == 1:
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
    ##### THANKS #########################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "thanks",
        brief = "Thanks the bot :3",
        description = "Thanks the bot :3"
    )
    async def thanks(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        await ctx.reply("You're welcome!")

        
            

        
    ######################################################################################################################################################
    ##### HOLY ###########################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "holy",
        brief = "Holy code",
        description = "Holy code"
    )
    @commands.check(u_checks.hide_from_help)
    async def holy_command(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        await ctx.reply("holy code")

        
            

        
    ######################################################################################################################################################
    ##### POGGERS ########################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "poggers",
        brief = "Poggers.",
        description = "Poggers."
    )
    async def poggers_command(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        await ctx.reply("Poggers.")

        
            

        
    ######################################################################################################################################################
    ##### GOOD MORNING ###################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "good_morning",
        aliases = ["goodmorning"],
        brief = "Good morning!",
        description = "Good morning!"
    )
    async def good_morning(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
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
    async def good_night(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
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
    @commands.check(u_checks.hide_from_help)
    async def perchance(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        await ctx.reply("You can't just say perchance.")

        
            

        
    ######################################################################################################################################################
    ##### TYPING #########################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "typing",
        brief = "Typing...",
        description = "Typing..."
    )
    @commands.check(u_checks.hide_from_help)
    async def typing_command(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
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
    @commands.check(u_checks.hide_from_help)
    async def tetris(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
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
    @commands.check(u_checks.hide_from_help)
    async def ewr(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        if ctx.invoked_subcommand is not None:
            return
        
        await self._cipher_wikipedia(ctx, u_ciphers.ewr_encode)

    @ewr.command(
        name = "encode",
        brief = "Wbxisw rwzr ubri rgw wqe xuogwe.",
        description = "Wbxisw rwzr ubri rgw wqe xuogwe.",
    )
    async def ewr_encode(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            *, text: typing.Optional[str] = commands.parameter(description = "Rgw rwzr ri wbxisw.", displayed_name = "rwzr")
        ):
        await self._cipher_translate(ctx, u_ciphers.ewr_encode, text, "encode")

    @ewr.command(
        name = "decode",
        brief = "Decode text from the ewr cipher.",
        description = "Decode text from the ewr cipher.",
    )
    async def ewr_decode(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
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
    @commands.check(u_checks.hide_from_help)
    async def fdg(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        if ctx.invoked_subcommand is not None:
            return
        
        await self._cipher_wikipedia(ctx, u_ciphers.fdg_encode)

    @fdg.command(
        name = "encode",
        brief = "Dyelcd gdwg kygl gnd vcb ekpndf.",
        description = "Dyelcd gdwg kygl gnd vcb ekpndf.",
    )
    async def fdg_encode(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            *, text: typing.Optional[str] = commands.parameter(description = "Gnd gdwg gl dyelcd.", displayed_name = "gdwg")
        ):
        await self._cipher_translate(ctx, u_ciphers.fdg_encode, text, "encode")

    @fdg.command(
        name = "decode",
        brief = "Decode text from the fdg cipher.",
        description = "Decode text from the fdg cipher.",
    )
    async def fdg_decode(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
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
    @commands.check(u_checks.hide_from_help)
    async def r_circle_section(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
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
    async def r_circle_section_encode(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
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
    async def r_circle_section_decode(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
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
    @commands.check(u_checks.hide_from_help)
    async def pi(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            guess: typing.Optional[str] = commands.parameter(description = "Your guess as to the value of pi.")
        ):
        if guess is None:
            await ctx.reply("Contrary to popular belief, π actually has digits.")
            return
            
        if guess == "π":
            await ctx.reply("While that is technically correct, it does not test your knowledge of π.")
            return
            
        if guess == "e":
            await ctx.reply("That is the wrong transcendental number.")
            return
            
        if guess == "🥧" or guess == ":pie:":
            await ctx.reply(":yum:")
            return

        if guess == "pi":
            await ctx.reply("You was doing PIPI in your pampers when i was beating players much more stronger then you!")
            return

        if guess == "😋" or guess == ":yum:":
            await ctx.reply(":pie:")
            return

        if guess == "31004150":
            await ctx.reply("You're off by a lot.")
            return

        if guess.startswith("3,"):
            await ctx.reply("Sorry, but can you pwease do that with `3.` instead of `3,`? owo")
            return

        if not u_converters.is_float(guess): # This will catch None.
            await ctx.reply("You should provide a numerical guess.")
            return
        
        guess = str(guess)

        if not guess.replace('.','',1).isdigit():
            await ctx.reply("You must provide a guess.")
            return
        
        if not (guess.startswith("3.")):
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
            break

        
            

        
    ######################################################################################################################################################
    ##### PREPARE ########################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "prepare",
        brief = "Powering up the Grammar Cannon.",
        description = "Powering up the Grammar Cannon."
    )
    @commands.check(u_checks.hide_from_help)
    async def prepare(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
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
    @commands.check(u_checks.hide_from_help)
    async def summon(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
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
    async def brick(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
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
    async def brick_analyze(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
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

        # Fix if any of the stats are None.
        if bricks is None:
            bricks = 0
        if gold is None:
            gold = 0
        if total is None:
            total = 0

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

        embed = u_interface.gen_embed(
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
                        half, round(gold_brick_chance, 2),
                        round(exact_odds, 2)
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
    async def xkcd(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
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
        
        embed = u_interface.gen_embed(
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
    async def xkcd_ping(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            state: typing.Optional[str] = commands.parameter(description = "'on' to join the ping list, 'off' to leave.")
        ):
        new_state = False

        if state in ["on", "off"]:
            new_state = state == "on"
        else:
            on_pinglist = database.user_on_ping_list("xkcd_strips", ctx.author.id)

            new_state = not on_pinglist

        database.update_ping_list("xkcd_strips", ctx.author.id, new_state)

        embed = u_interface.gen_embed(
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
    @commands.check(u_checks.hide_from_help)
    async def askouija(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
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
    @commands.check(u_checks.hide_from_help)
    async def get_count(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        if u_checks.sensitive_check(ctx.channel):
            await ctx.reply("This is not the channel for that.")
            return
        
        counting_data = database.get_counting_data(ctx.channel.id)

        if counting_data["count"] == 0:
            await ctx.reply("There is no count here yet! Send `1` to start it.")
            return
        
        await ctx.reply("The current count is {}.".format(u_text.smart_number(counting_data["count"])))

        
            

        
    ######################################################################################################################################################
    ##### FLIP COIN ######################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "flip_coin",
        aliases = ["coin_flip"],
        brief = "Yep, it's just a coin flip.",
        description = "Yep, it's just a coin flip."
    )
    @commands.check(u_checks.hide_from_help)
    async def flip_coin(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        await ctx.reply(random.choice(["Heads.","Tails."]))

        
            

        
    ######################################################################################################################################################
    ##### WEEKDAY ########################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "weekday",
        brief = "What's the current day of the week in EDT?",
        description = "What's the current day of the week in EDT?"
    )
    async def weekday(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        await ctx.reply(datetime.datetime.today().astimezone(pytz.timezone("US/Eastern")).strftime('%A') + ".")

        
            

        
    ######################################################################################################################################################
    ##### ROLE GRAPH #####################################################################################################################################
    ######################################################################################################################################################

    @commands.command(
        name = "role_graph",
        brief = "Graphs the number of people who have a role.",
        description = "Graphs the number of people who have a role using role snapshots."
    )
    @commands.check(u_checks.hide_from_help)
    async def role_graph(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            role: typing.Optional[discord.Role] = commands.parameter(description = "The id of the role to graph.")
        ):
        if role is None:
            await ctx.reply("You must provide a role.")
            return 
        
        snapshot_list = [item for item in os.listdir(f"data{SLASH}role_snapshots{SLASH}snapshots{SLASH}") if item.endswith(".json")]

        found = False
        tracked_data = []
        for snapshot_id, snapshot in enumerate(snapshot_list):
            count = 0
            snapshot_data = u_files.load("data", "role_snapshots", "snapshots", snapshot, default={}, join_file_path=True)
            for user in snapshot_data:
                if role.id in snapshot_data[user]:
                    count += 1
                    found = True
            
            tracked_data.append((snapshot_id, count))
        
        if not found:
            await ctx.reply("I can't find anyone ever having that role.")
            return
        
        file_path = u_images.generate_graph(
            lines = [{
                    "values": tracked_data
            }],
            x_label = "Days since September 1st.",
            y_label = "Amount of people with that role."
        )

        embed = u_interface.gen_embed(
            title = "Role graph",
            description = "Graph of users with {}:".format(role.mention),
            image_link = "attachment://graph.png"
        )
        
        await ctx.reply(embed=embed, file=discord.File(file_path, filename="graph.png"))
        
            

        
    ######################################################################################################################################################
    ##### ROLE LEADERBOARD ###############################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "role_leaderboard",
        aliases = ["role_lb"],
        brief = "A leaderboard for roles.",
        description = "A leaderboard for roles.\n\nModifier list:\n- '-list' will provide a list of all the roles the highlighted person has."
    )
    @commands.check(u_checks.hide_from_help)
    async def role_leaderboard(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            member: typing.Optional[discord.Member] = commands.parameter(description = "The member to view."),
            *, modifiers: typing.Optional[str] = commands.parameter(description = "Optional modifiers, see above for modifier list.")
        ):
        if ctx.guild is None:
            await ctx.reply("This command can only be used in servers.")
            return

        if member is None:
            member = ctx.author

        role_data = u_interface.get_role_list(ctx.guild)

        if modifiers is not None:
            modifiers = modifiers.split(" ")
        else:
            modifiers = []

        list_roles = "-list" in modifiers

        ## Roles to not count: ##

        selectable = [
            # Pronoun roles:
            959254553562349608, 980602604847501362, 980602604847501362, 959247044701216848, 958920201557119036, 958920265792892938, 958920155025539132, 959220485672026142, 958920124314816532, 958920326006308914,
            
            # "No <channel>" roles:
            1177067684744142888, 1177067733695864942, 1177067611348008970,
            
            # Rating roles:
            970619771374690345, 960928696368259113, 961216939198410792, 960928234273394689, 958737602859655178, 958737525139177492, 958737469635981362, 958737300236406905, 958737243885932564, 958736931246706698,
            
            # Platform roles:
            970574059727380520, 958736670323269742, 958736276415205436,
            
            # Notification roles:
            982060564077498418, 970550144477040650, 962130208700379216, 1058812522507026493,
            
            # Color roles:
            1118418774966665276, 1118415419125026857, 1118415313277558794, 1118415111124701184, 1138140416064102410, 1118415718065635329, 1118415622599098390, 1118415511752024105,
        ]

        additional = [
            # Moderation roles:
            970549665055522850, 1119445209923723396, 958512048306815056, 958755031820161025,
            
            # Jail-like roles:
            975082724501098557, 972268045999431703, 1119317224604307586, 1157009850455302234,

            # "Never gonna be ______" roles: (Note that this does not include "never gonna give you up.")
            1202614210752675850, 960935784075112468, 960937535469658212, 960938170285965312,

            # Other misc roles:
            958774733225230397, # Based.
            1023757953687363634, # Under 18.

            # Pride roles:
            1214062437037506590, # Ace
            1214085642158604379, # Aro
            1214061577213579284, # Bi
            1214101911054061568, # Pan
            1214060839246499860, # Lesbian
            1074083716961402940, # Transfem
            1214084942145912842, # Gay
            1214083260766883840, # Enby
        ]

        prune_ids = selectable + additional
        prune_ids.append(ctx.guild.id)

        ## Figure out how many each person has: ##

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
        
        fields = [("", "\n".join(lines), False)]

        if list_roles:
            title = "Counted roles:"

            character_count = 0
            data_add = []
            for role_id in role_data[member.id]:
                if role_id in prune_ids:
                    continue
                ping = f"<@&{role_id}>"

                character_count += len(ping)

                if character_count >= 1024:
                    fields.append(
                        (
                            title,
                            "".join(data_add),
                            False
                        )
                    )
                    title = ""
                    data_add = []
                    character_count = len(ping)

                data_add.append(ping)
            
            if len(data_add) >= 1:
                fields.append(
                    (
                        title,
                        "".join(data_add),
                        False
                    )
                )
        
        embed = u_interface.gen_embed(
            title = "Role leaderboard",
            description = "*This is excluding self-selectable roles.*",
            fields = fields,
            footer_text = "You can use '%role_leaderboard <member>' to highlight someone else.\nYou can also use '%role_leaderboard <member> -list' to get a list of the counted roles for the highlighted member."
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
    @commands.check(u_checks.hide_from_help)
    async def lichess(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
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

        
        embed = u_interface.gen_embed(
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
    async def emoji_command(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            *, text: typing.Optional[str] = commands.parameter(description = "The emoji, or text to search for.")
        ):
        if text is None:
            await ctx.reply("You can provide a custom emoji to get the image for it or provide a piece of text to search for it.")
            return
            
        matched = re.search("<a?:\w+:(\d+)>", text)
        
        if matched is None:
            await ctx.reply(await self._emoji_search(text))
            return
    
        emoji_id = matched.group(1)
        file_extension = "gif" if matched.group(0)[1] == "a" else "png"

        embed = u_interface.gen_embed(
            title = "Emoji image",
            image_link = f"https://cdn.discordapp.com/emojis/{emoji_id}.{file_extension}"
        )
        await ctx.reply(embed=embed)
        


    async def _emoji_search(
            self: typing.Self,
            text: str
        ) -> str:
        
        def score_emoji(emoji_text: str) -> float:
            return difflib.SequenceMatcher(None, text.lower(), emoji_text.lower()).ratio()
        
        emoji_list = [] # type: list[tuple[str, float]]

        for guild in self.bot.guilds:
            for emoji in guild.emojis:
                emoji_list.append((str(emoji), score_emoji(emoji.name)))
        
        emoji_data = database.load_json_file("data", "emoji_data.json", default=[], join_file_path=False) # This file isn't loaded into the database since it's really large and also shouldn't be changing.
        for data in emoji_data:
            emoji_list.append((data["text"], score_emoji(data["name"])))
        
        emoji_list = sorted(emoji_list, key=lambda x: x[1], reverse=True)

        return " ".join([emoji_list[i][0] for i in range(25)])

        
            

        
    ######################################################################################################################################################
    ##### MINECRAFT ######################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "vdc_wiki",
        brief = "Search the Valve Developer Community Wiki.",
        description = "Search the Valve Developer Community Wiki."
    )
    @commands.check(u_checks.hide_from_help)
    async def vdc_wiki(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            *, search_term: typing.Optional[str] = commands.parameter(description = "The search term to search the wiki with.")
        ):
        
        if self.vdc_wiki_searching:
            await ctx.reply("This commmand is currently being used somewhere, please wait until it's done to try again.")
            return
    
        def manual_replacements(wikitext: str) -> str:            
            wikitext = re.sub( # Ensure things like `hanging_walkway_...` have backslashes put before the underscores.
                r"(.)_(.)",
                r"\1\_\2",
                wikitext
            )

            return wikitext
        
        try:
            self.vdc_wiki_searching = True

            await u_interface.handle_wiki_search(
                ctx = ctx,
                wiki_link = "https://developer.valvesoftware.com/wiki/",
                wiki_main_page = "https://developer.valvesoftware.com/wiki/Main_Page",
                wiki_name = "The Valve Developer Community Wiki",
                wiki_api_url = "https://developer.valvesoftware.com/w/api.php",
                search_term = search_term,
                manual_replacements = manual_replacements
            )

            self.vdc_wiki_searching = False
        except:
            self.vdc_wiki_searching = False

            # After ensuring vdc_wiki_searching has been reset, reraise the exception so the "Something went wrong processing that command." message is still sent.
            raise

        
            

        
    ######################################################################################################################################################
    ##### MINECRAFT ######################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "minecraft",
        brief = "Search the Minecraft Wiki!",
        description = "Search the Minecraft Wiki."
    )
    @commands.check(u_checks.hide_from_help)
    async def minecraft(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext,
            *, search_term: typing.Optional[str] = commands.parameter(description = "The search term to search the wiki with.")
        ):
        
        if self.minecraft_wiki_searching:
            await ctx.reply("This commmand is currently being used somewhere, please wait until it's done to try again.")
            return
        
        def manual_replacements(wikitext: str) -> str:
            templates = re.finditer(r"{{\w+Link\|(.+?)}}", wikitext) # Replace BlockLink, EnvLink, and similar templates with a link to the page.
            for template in templates:
                wikitext = wikitext.replace(template.group(0), f"[{template.group(1)}](https://minecraft.wiki/w/{template.group(1).replace(' ', '_')})")
            
            wikitext = re.sub( # Filter out things like `[[es:Musgo]]` and `[[pt:Musgo]]`
                r"\[\[.{2}:.+?]]",
                "",
                wikitext
            )

            return wikitext
        
        try:
            self.minecraft_wiki_searching = True

            await u_interface.handle_wiki_search(
                ctx = ctx,
                wiki_link = "https://minecraft.wiki/w/",
                wiki_main_page = "https://minecraft.wiki/",
                wiki_name = "The Minecraft Wiki",
                wiki_api_url = "https://minecraft.wiki/api.php",
                search_term = search_term,
                manual_replacements = manual_replacements
            )

            self.minecraft_wiki_searching = False
        except:
            self.minecraft_wiki_searching = False

            # After ensuring minecraft_wiki_searching has been reset, reraise the exception so the "Something went wrong processing that command." message is still sent.
            raise

        
            

        
    ######################################################################################################################################################
    ##### PIGUY ##########################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "piguy",
        brief = "Piguy.",
        description = "Piguy."
    )
    @commands.check(u_checks.hide_from_help)
    async def piguy(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        piguy_timestamp = datetime.datetime.fromtimestamp(1095880500)
        relative_delta = dateutil.relativedelta.relativedelta(datetime.datetime.now(), piguy_timestamp)

        await ctx.reply("Years: {years}\nMonths: {months}\nDays: {days}\nHours: {hours}\nMinutes: {minutes}".format(
            years = relative_delta.years,
            months = relative_delta.months,
            days = relative_delta.days,
            hours = relative_delta.hours,
            minutes = relative_delta.minutes
        ))

        
            

        
    ######################################################################################################################################################
    ##### LILLY ##########################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "lilly",
        brief = "Lilly.",
        description = "Lilly."
    )
    @commands.check(u_checks.hide_from_help)
    async def lilly(
            self: typing.Self,
            ctx: commands.Context | u_custom.CustomContext
        ):
        lilly_timestamp = datetime.datetime.fromtimestamp(1095408240)
        relative_delta = dateutil.relativedelta.relativedelta(datetime.datetime.now(), lilly_timestamp)

        await ctx.reply("Years: {years}\nMonths: {months}\nDays: {days}\nHours: {hours}\nMinutes: {minutes}".format(
            years = relative_delta.years,
            months = relative_delta.months,
            days = relative_delta.days,
            hours = relative_delta.hours,
            minutes = relative_delta.minutes
        ))
    


async def setup(bot: commands.Bot):
    global database
    database = bot.database
    
    cog = Other_cog()
    cog.bot = bot

    # Add attributes for sys.modules and globals() so the _reload_module() function in utility.custom can read it and get the module objects.
    cog.modules = sys.modules
    cog.globals = globals()
    
    await bot.add_cog(cog)
