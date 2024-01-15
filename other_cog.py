from discord.ext import commands
from scipy.stats import binom
import discord
import typing
import random
import wikipedia
import mpmath
import copy
import re
import aiohttp
import traceback
import time

import sys

import utility.custom as u_custom
import utility.ciphers as u_ciphers
import utility.checks as u_checks
import utility.converters as u_converters
import utility.interface as u_interface
import utility.text as u_text
import utility.bread as u_bread
import utility.bingo as u_bingo

class Other_cog(u_custom.CustomCog, name="Other", description="Commands that don't fit elsewhere, and are kind of silly."):
    bot = None

    minecraft_wiki_searching = False
    
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
        ctx = u_custom.CustomContext(ctx)

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
        ctx = u_custom.CustomContext(ctx)

        if message is None:
            await ctx.reply("||\n||")
            return
        
        bingo_data = u_bingo.live()
        
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
            await ctx.reply("Please have the numbers in the message sum to a prime number.")
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
        
        print("Executing say command for {} with text: {}".format(message.author, message))
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
    async def thanks(self, ctx):
        ctx = u_custom.CustomContext(ctx)
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
        ctx = u_custom.CustomContext(ctx)
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
        ctx = u_custom.CustomContext(ctx)

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
        ctx = u_custom.CustomContext(ctx)
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
        ctx = u_custom.CustomContext(ctx)
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
        ctx = u_custom.CustomContext(ctx)
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
        ctx = u_custom.CustomContext(ctx)

        if ctx.invoked_subcommand is not None:
            return
        
        page = wikipedia.page(wikipedia.random(pages=1))
        page_content = page.content.split("\n")[0]

        if len(page_content) >= 1000:
            page_content = page_content.split(".")[0]

        title = u_ciphers.ewr_encode(page.title)
        page_content = u_ciphers.ewr_encode(page_content)

        embed = u_interface.embed(
            title = title,
            description = page_content
        )
        await ctx.reply(embed=embed)

    @ewr.command(
        name = "encode",
        brief = "Wbxisw rwzr ubri rgw wqe xuogwe.",
        description = "Wbxisw rwzr ubri rgw wqe xuogwe.",
    )
    async def ewr_encode(self, ctx,
            *, text: typing.Optional[str] = commands.parameter(description = "Rgw rwzr ri wbxisw.", displayed_name = "rwzr")
        ):
        ctx = u_custom.CustomContext(ctx)

        await self._cipher_translate(ctx, u_ciphers.ewr_encode, text, "encode")

    @ewr.command(
        name = "decode",
        brief = "Decode text from the ewr cipher.",
        description = "Decode text from the ewr cipher.",
    )
    async def ewr_decode(self, ctx,
            *, text: typing.Optional[str] = commands.parameter(description = "The text to decode.")
        ):
        ctx = u_custom.CustomContext(ctx)
        
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
        ctx = u_custom.CustomContext(ctx)

        if ctx.invoked_subcommand is not None:
            return
        
        page = wikipedia.page(wikipedia.random(pages=1))
        page_content = page.content.split("\n")[0]

        if len(page_content) >= 1000:
            page_content = page_content.split(".")[0]

        title = u_ciphers.fdg_encode(page.title)
        page_content = u_ciphers.fdg_encode(page_content)

        embed = u_interface.embed(
            title = title,
            description = page_content
        )
        await ctx.reply(embed=embed)

    @fdg.command(
        name = "encode",
        brief = "Dyelcd gdwg kygl gnd vcb ekpndf.",
        description = "Dyelcd gdwg kygl gnd vcb ekpndf.",
    )
    async def fdg_encode(self, ctx,
            *, text: typing.Optional[str] = commands.parameter(description = "Gnd gdwg gl dyelcd.", displayed_name = "gdwg")
        ):
        ctx = u_custom.CustomContext(ctx)

        await self._cipher_translate(ctx, u_ciphers.fdg_encode, text, "encode")

    @fdg.command(
        name = "decode",
        brief = "Decode text from the fdg cipher.",
        description = "Decode text from the fdg cipher.",
    )
    async def fdg_decode(self, ctx,
            *, text: typing.Optional[str] = commands.parameter(description = "The text to decode.")
        ):
        ctx = u_custom.CustomContext(ctx)

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
        ctx = u_custom.CustomContext(ctx)

        if ctx.invoked_subcommand is not None:
            return
        
        page = wikipedia.page(wikipedia.random(pages=1))
        page_content = page.content.split("\n")[0]

        if len(page_content) >= 1000:
            page_content = page_content.split(".")[0]

        title = u_ciphers.r_circle_section_encode(page.title)
        page_content = u_ciphers.r_circle_section_encode(page_content)

        embed = u_interface.embed(
            title = title,
            description = page_content
        )
        await ctx.reply(embed=embed)

    @r_circle_section.command(
        name = "encode",
        brief = "Ec':]X G08t }'^] G3p g@= VGM3pr.",
        description = "Ec':]X G08t }'^] G3p g@= VGM3pr.",
    )
    async def r_circle_section_encode(self, ctx,
            *, text: typing.Optional[str] = commands.parameter(description = "TØ; ^X>G uo ;'[]LB.", displayed_name = "t○b}")
        ):
        ctx = u_custom.CustomContext(ctx)

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
        ctx = u_custom.CustomContext(ctx)

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
        ctx = u_custom.CustomContext(ctx)

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
        ctx = u_custom.CustomContext(ctx)

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
        ctx = u_custom.CustomContext(ctx)

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
        ctx = u_custom.CustomContext(ctx)

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
        ctx = u_custom.CustomContext(ctx)

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
    ##### FLIP COIN ######################################################################################################################################
    ######################################################################################################################################################
    
    @commands.command(
        name = "flip_coin",
        aliases = ["coin_flip"],
        brief = "Yep, it's just a coin flip.",
        description = "Yep, it's just a coin flip."
    )
    async def flip_coin(self, ctx):
        ctx = u_custom.CustomContext(ctx)
        await ctx.reply(random.choice(["Heads.","Tails."]))

        
            

        
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
        ctx = u_custom.CustomContext(ctx)

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
        


async def setup(bot: commands.Bot):
    cog = Other_cog()
    cog.bot = bot
    
    # Add attributes for sys.modules and globals() so the _reload_module() function in utility.custom can read it and get the module objects.
    cog.modules = sys.modules
    cog.globals = globals()
    
    await bot.add_cog(cog)