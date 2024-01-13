from discord.ext import commands
import discord
import typing

import sys

import utility.stonks as u_stonks
import utility.converters as u_converters
import utility.interface as u_interface
import utility.values as u_values
import utility.text as u_text
import utility.files as u_files
import utility.custom as u_custom

class Stonk_cog(u_custom.CustomCog, name="Stonks"):

    @commands.group(
        name = "stonks",
        aliases = ["stonk"],
        description = "You might want `$bread stonks` instead of this.\n\nHeader command for stonk related utility commands.",
        brief = "Header for stonk related commands.",
        invoke_without_command = True,
        pass_context = True
    )
    async def stonk(self, ctx):
        ctx = u_custom.CustomContext(ctx)

        if ctx.invoked_subcommand is not None:
            return
        
        await ctx.send_help(self.stonk)
    





    ######################################################################################################################################################
    ##### STONK HISTORY ##################################################################################################################################
    ######################################################################################################################################################
    
    @stonk.command(
        name = "history",
        description = "Look through previous stonk values.",
        brief = "Look through previous stonk values."
    )
    async def stonk_history(self, ctx,
            tick_id: typing.Optional[u_converters.parse_int] = commands.parameter(description = "An optional specific tick to look at.")
        ):
        ctx = u_custom.CustomContext(ctx)

        stonk_history = u_stonks.stonk_history()

        if tick_id is None:
            tick_id = len(stonk_history) - 1
        
        if not(0 <= tick_id <= len(stonk_history) - 1):
            await ctx.reply(f"The stonk tick number must be between 0 and {u_text.smart_number(len(stonk_history) - 1)}.")
            return
        
        tick_data = stonk_history[tick_id]
        
        description_lines = []

        for stonk in u_values.stonks:
            if stonk.internal_name not in tick_data:
                continue

            description_lines.append("- {}: {}".format(stonk.internal_emoji, u_text.smart_number(tick_data[stonk.internal_name])))
        
        embed = u_interface.embed(
            title = "Stonk history for tick {}".format(u_text.smart_number(tick_id)),
            description = "The values on that tick:\n{}".format("\n".join(description_lines)),
            footer_text = "A missing stonk means it did not exist on that tick."
        )

        await ctx.reply(embed=embed)
    





    ######################################################################################################################################################
    ##### STONK CURRENT ##################################################################################################################################
    ######################################################################################################################################################
    
    @stonk.command(
        name = "current",
        description = "Get information about the current tick.",
        brief = "Get information about the current tick."
    )
    async def stonk_current(self, ctx):
        ctx = u_custom.CustomContext(ctx)

        stonk_data = u_stonks.full_current_tick()

        tick_data = stonk_data["values"]
        
        description_lines = []

        for stonk in u_values.stonks:
            if stonk.internal_name not in tick_data:
                continue

            description_lines.append("- {}: {}".format(stonk.internal_emoji, u_text.smart_number(tick_data[stonk.internal_name])))

        embed = u_interface.embed(
            title = "Current stonk tick",
            description = "It is currently stonk tick **{}**.\nCurrent stonk values:\n{}".format(u_text.smart_number(stonk_data["tick_number"]), "\n".join(description_lines))
        )
        await ctx.reply(embed=embed)
    





    ######################################################################################################################################################
    ##### STONK PING #####################################################################################################################################
    ######################################################################################################################################################
    
    @stonk.command(
        name = "ping",
        description = "Pinglist for stonk ticks!\nUse '%stonk ping on' to get on the pinglist and '%stonk ping off' to leave it.",
        brief = "Pinglist for stonk ticks!"
    )
    async def stonk_ping(self, ctx,
            state: typing.Optional[str] = commands.parameter(description = "'on' to join the ping list, 'off' to leave.")
        ):
        ctx = u_custom.CustomContext(ctx)

        new_state = False

        if state in ["on", "off"]:
            new_state = state == "on"
        else:
            on_pinglist = u_files.user_on_ping_list("stonk_tick_pings", ctx.author.id)

            new_state = not on_pinglist

        u_files.update_ping_list("stonk_tick_pings", ctx.author.id, new_state)

        embed = u_interface.embed(
            title = "Stonk tick ping list",
            description = "You will {} be pinged for future stonk ticks.".format("now" if new_state else "no longer")
        )
        await ctx.reply(embed=embed)
        return
    





    ######################################################################################################################################################
    ##### STONK PREVIOUS #################################################################################################################################
    ######################################################################################################################################################
    
    @stonk.command(
        name = "previous",
        description = "Previous stonk values, stonk tick style.\nYou can provide a specific stonk or set of stonks to use just those. If no stonks are provided, all will be used.\nAdditional parameters:\n  '-color' or '-colour to use emojis to mark rises, falls, or stagnations.",
        brief = "Previous stonk values, stonk tick style."
    )
    async def stonk_previous(self, ctx,
            ticks: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The number of ticks to show, must be between 2 and 50."),
            *, modifiers: typing.Optional[str] = commands.parameter(description = "Optional modifiers, see above for modifier list."),
        ):
        ctx = u_custom.CustomContext(ctx)

        if ticks is None:
            await ctx.reply("You must provide the number of ticks to show.")
            return
        
        if not(2 <= ticks <= 50):
            await ctx.reply("The number of ticks must be between 2 and 50.")
            return
        
        color_mode = False

        stonks_use = []

        if modifiers is not None:
            for modifier in modifiers.split(" "):
                item = u_values.get_item(modifier, "stonk")

                if item:
                    stonks_use.append(item)
                    continue

                if modifier in ["-color", "-colour"]:
                    color_mode = True
                    continue
        
        if len(stonks_use) == 0:
            stonks_use = u_values.stonks
        
        found_data = {stonk: [] for stonk in stonks_use}
        
        stonk_history = u_stonks.stonk_history()

        previous_tick = {}
        
        for tick_back in range(ticks + 1):
            tick_data = stonk_history[ticks * -1 - 1 + tick_back]

            if tick_back == 0:
                previous_tick = tick_data.copy()
                continue

            for stonk in stonks_use:
                if stonk.internal_name not in tick_data:
                    continue
                
                if color_mode:
                    change_amount = tick_data[stonk.internal_name] - previous_tick[stonk.internal_name]

                    if change_amount > 0:
                        found_data[stonk].append("🟩")
                    elif change_amount == 0:
                        found_data[stonk].append("🟨")
                    else:
                        found_data[stonk].append("🟥")
                    
                    continue

                bonus = ""
                if tick_data[stonk.internal_name] / previous_tick[stonk.internal_name] <= 0.85:
                    bonus = "__"
                
                dough = ""
                if tick_back == ticks:
                    dough = " dough"
                    bonus += "**"

                found_data[stonk].append("".join([bonus, str(tick_data[stonk.internal_name]), dough, bonus]))
        
            previous_tick = tick_data.copy()
        
        if color_mode:
            found_data = {stonk: "".join(value) for stonk, value in found_data.items()}
        else:
            found_data = {stonk: " -> ".join(value) for stonk, value in found_data.items()}
        
        fields = [(f"{stonk}:", value, False) for stonk, value in found_data.items()]
        
        embed = u_interface.embed(
            title = "Previous {} ticks".format(u_text.smart_number(ticks)),
            fields = fields
        )
        
        await ctx.reply(embed=embed)

                









async def setup(bot: commands.Bot):
    cog = Stonk_cog()
    cog.bot = bot
    
    # Add attributes for sys.modules and globals() so the _reload_module() function in utility.custom can read it and get the module objects.
    cog.modules = sys.modules
    cog.globals = globals()
    
    await bot.add_cog(cog)