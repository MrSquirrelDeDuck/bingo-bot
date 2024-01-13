from os.path import sep as SLASH

from discord.ext import commands
import discord
import typing
import random
import copy

import sys

import utility.bread as u_bread
import utility.stonks as u_stonks
import utility.converters as u_converters
import utility.interface as u_interface
import utility.values as u_values
import utility.text as u_text
import utility.files as u_files
import utility.custom as u_custom
import utility.images as u_images

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
    





    ######################################################################################################################################################
    ##### STONK MESSAGE ##################################################################################################################################
    ######################################################################################################################################################
    
    @stonk.command(
        name = "message",
        description = "Get a link to the last stonk tick.",
        brief = "Get a link to the last stonk tick."
    )
    async def stonk_message(self, ctx):
        ctx = u_custom.CustomContext(ctx)

        await ctx.reply(u_stonks.full_current_tick()["message_link"])
    





    ######################################################################################################################################################
    ##### STONK RANDOM ###################################################################################################################################
    ######################################################################################################################################################
    
    @stonk.command(
        name = "random",
        description = "When you're having trouble deciding what to invest in.",
        brief = "When you're having trouble deciding what to invest in."
    )
    async def stonk_message(self, ctx):
        ctx = u_custom.CustomContext(ctx)

        commands = [f"$bread invest all {stonk.internal_name}" for stonk in u_values.stonks]

        random.shuffle(commands)

        embed = u_interface.embed(
            title = "Random stonk",
            description = "\n".join(commands),
            footer_text = "On mobile you can tap and hold on the commands to copy them."
        )

        await ctx.reply(embed=embed)
    





    ######################################################################################################################################################
    ##### STONK ANALYZE ##################################################################################################################################
    ######################################################################################################################################################
    
    @stonk.command(
        name = "analyze",
        description = "Calculate a portfolio's value on any stonk tick.\n\nNote that if a stonk is in the portfolio but did not exist for the tick you're analyzing it will not be used.",
        brief = "Calculate a portfolio's value on any stonk tick."
    )
    async def stonk_analyze(self, ctx,
            tick_id: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The tick number to use the values from.")
        ):
        ctx = u_custom.CustomContext(ctx)

        current_tick = u_stonks.current_tick_number()

        if tick_id is None or not(current_tick * -1 <= tick_id <= current_tick):
            await ctx.reply("You must provide a stonk tick id between 0 and {} to get the values from.\nHowever, negative numbers can be used to go back from the end, so -1 is the most recent tick.".format(u_text.smart_number(current_tick)))
            return
        
        if tick_id < 0:
            tick_id = current_tick + tick_id + 1
        
        replied_to = u_interface.replying_mm_checks(ctx.message, require_reply=True, return_replied_to=True)

        if not replied_to:
            await ctx.reply("You must reply to a portfolio to analyze it.")
            return
        
        parsed = u_bread.parse_stats(replied_to)


        if parsed.get("stats_type") != "portfolio":
            await ctx.reply("You must reply to a portfolio to analyze it.")
            return
        
        parsed = parsed["stats"]
        
        tick_data = u_stonks.stonk_history()[tick_id]
        previous_tick_data = u_stonks.stonk_history()[max(tick_id - 1, 0)]

        dough_value = []
        previous_dough_value = []

        output_lines = []
        for stonk in u_values.stonks:
            if stonk.internal_name not in tick_data:
                output_lines.append("{} -- {}, however it did not exist on this tick.".format(stonk, u_text.smart_text(parsed[stonk], "stonk")))
                continue

            value = parsed[stonk] * tick_data[stonk.internal_name]
            dough_value.append(value)

            output_lines.append("{} -- {}, worth **{} dough**".format(stonk, u_text.smart_text(parsed[stonk], "stonk"), u_text.smart_number(value)))

            if stonk.internal_name not in previous_tick_data:
                previous_dough_value.append(value)
                continue
            
            previous_dough_value.append(parsed[stonk] * previous_tick_data[stonk.internal_name])
        
        embed = u_interface.embed(
            title = "Analyzed portfolio",
            description = "That portfolio, using the values from stonk tick {}:".format(u_text.smart_number(tick_id)),
            fields=[
                ("", "\n".join(output_lines), False),
                ("", "In total, that portfolio would be worth **{} dough**, and on that tick changed by **{} dough**.".format(u_text.smart_number(sum(dough_value)), u_text.smart_number(sum(dough_value) - sum(previous_dough_value))), False)
            ]
        )
        await ctx.reply(embed=embed)
    





    ######################################################################################################################################################
    ##### STONK FILE #####################################################################################################################################
    ######################################################################################################################################################
    
    @stonk.command(
        name = "file",
        description = "Provides the entire stonk history as a json file.",
        brief = "Provides the entire stonk history as a json file."
    )
    async def stonk_file(self, ctx):
        ctx = u_custom.CustomContext(ctx)

        await ctx.reply(file=discord.File(f"data/stonks/stonk_history.json"))
    





    ######################################################################################################################################################
    ##### STONK SEARCH ###################################################################################################################################
    ######################################################################################################################################################
    
    @stonk.command(
        name = "search",
        description = "Searches for stonk values in the stonk history.\n\nTo provide the values for your search, format each one as '<stonk> <value>', with a space in the middle. Multiple stonks can be provided, as well.\n\nFor example, '%stonk search cookie 25' would search for ticks where cookies are worth 25 dough.\n\nIf multiple stonks are provided, they all must be true, so if you provide 'cookie 30 pretzel 107' then it will search for every tick where cookies are worth 30 and pretzels are worth 107.",
        brief = "Searches for stonk values in the stonk history."
    )
    async def stonk_search(self, ctx,
            *, parameters: typing.Optional[str] = commands.parameter(description = "The stonk values to search. See above for more info.", displayed_name="values")
        ):
        ctx = u_custom.CustomContext(ctx)

        if parameters is None:
            await ctx.reply("Unfortunately, you must provide at least 1 stonk value.")
            return

        parameters = parameters.split(" ")

        stonk_values = {}

        for index, param in enumerate(parameters):
            stonk = u_values.get_item(param, "stonk")

            if not stonk:
                continue

            if index == len(parameters) - 1 or not u_converters.is_digit(parameters[index + 1]):
                await ctx.reply("You specified the {} stonk but didn't provide a value.".format(stonk))
                return
            
            stonk_values[stonk] = u_converters.parse_int(parameters[index + 1])

        if len(stonk_values) == 0:
            await ctx.reply("Unfortunately, you must provide at least 1 stonk value.")
            return
        
        stonk_history = u_stonks.stonk_history()

        matched_ticks = []

        items = stonk_values.items()

        for tick_id, tick_data in enumerate(stonk_history):
            for stonk, value in items:
                if tick_data[stonk.internal_name] != value:
                    break
            else:
                matched_ticks.append(tick_id)
        
        embed = u_interface.embed(
            title = "Stonk search",
            description = "{} found:".format("1 tick was" if len(matched_ticks) == 1 else f"{u_text.smart_number(len(matched_ticks))} ticks were"),
            fields = [
                ("", ", ".join([str(item) for item in matched_ticks]), False),
                ("", "You can use `%stonk history` to get values for a specific tick.", False)
            ]
        )
        await ctx.reply(embed=embed)
    





    ######################################################################################################################################################
    ##### STONK SPLIT ####################################################################################################################################
    ######################################################################################################################################################
    
    @stonk.command(
        name = "splits",
        aliases = ["split"],
        description = "Get the number of splits in a time frame.\nIf no end is provided it'll use the current tick as the end.",
        brief = "Get the number of splits in a time frame."
    )
    async def stonk_splits(self, ctx,
            start: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The start of the time frame."),
            end: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The end of the time frame."),
        ):
        ctx = u_custom.CustomContext(ctx)

        if start is None:
            start = 0
        
        if end is None:
            end = u_stonks.current_tick_number()
        
        if end <= start:
            await ctx.reply("The end must be after the start.")
            return

        split_counts = {stonk: 0 for stonk in u_values.stonks}

        stonk_history = u_stonks.stonk_history()

        for stonk in u_values.stonks:
            name = stonk.internal_name
            previous_value = stonk_history[start].get(name, None)

            for tick in stonk_history[start + 1: end + 1]:
                if previous_value is not None and tick[name] / previous_value <= 0.85:
                    for i in range(50):
                        previous_value /= 2
                        split_counts[stonk] += 1
                        if not(tick[name] / previous_value <= 0.85):
                            break

                previous_value = tick.get(name, None)
        
        embed = u_interface.embed(
            title = "Splits",
            description = "Number of times the stonks were split between ticks {} and {}:".format(u_text.smart_number(start), u_text.smart_number(end)),
            fields = [
                ("", "\n".join(["{}: {}".format(stonk, value) for stonk, value in split_counts.items()]), False)
            ]
        )
        await ctx.reply(embed=embed)
    





    ######################################################################################################################################################
    ##### STONK GRAPH ####################################################################################################################################
    ######################################################################################################################################################
    
    @stonk.command(
        name = "graph",
        description = "Graphs of stonk values.\n\nParameters:\n- The stonks you want to use, you can use an emoji or their name. You can also use 'all' to use all the stonks. Putting an exclamation mark before a stonk will remove it. If none are provided it will use them all.\n- To mark the start of the graph, use 'start <start point>'. If none is provided it will use 0.\n- To mark the end, 'end <end point>'. If none is provided it will use the current tick.\n- 'log' can be used to set the Y axis to a log scale.",
        brief = "Graphs of stonk values."
    )
    async def stonk_graph(self, ctx,
            *, parameters: typing.Optional[str] = commands.parameter(description = "The parameters to use. See above for more information.")
        ):
        ctx = u_custom.CustomContext(ctx)

        current_tick = u_stonks.current_tick_number()

        log_scale = False
        start_tick = 0
        end_tick = current_tick
        stonks = []
        
        if parameters is None:
            stonks = copy.deepcopy(u_values.stonks)
        else:
            parameters = parameters.split(" ")

            negated = []

            for param_id, param in enumerate(parameters):
                if param == "all":
                    stonks = copy.deepcopy(u_values.stonks)
                    continue

                if param == "log":
                    log_scale = True
                    continue

                if param == "start":
                    if param_id == len(parameters) - 1:
                        continue # "start" is not going to be the name of a stonk, and does not start with an exclamation mark.
                    
                    if u_converters.is_digit(parameters[param_id + 1]):
                        start_tick = u_converters.parse_int(parameters[param_id + 1])

                    continue

                if param == "end":
                    if param_id == len(parameters) - 1:
                        continue # "end" is not going to be the name of a stonk, and does not start with an exclamation mark.
                    
                    if u_converters.is_digit(parameters[param_id + 1]):
                        end_tick = u_converters.parse_int(parameters[param_id + 1])

                    continue
                
                if param.startswith("!"):
                    param = param.replace("!", "", 1)
                    modify = negated # Set "modify" to a reference to "negated".
                else:
                    modify = stonks # Set "modify" to a reference to "stonks".

                get_item = u_values.get_item(param, "stonk")

                if get_item:
                    if get_item not in modify:
                        modify.append(get_item)
                    continue
            
            if len(stonks) == 0:
                stonks = copy.deepcopy(u_values.stonks)
            
            for stonk in negated:
                if stonk in stonks:
                    stonks.remove(stonk)
        
        if end_tick <= start_tick:
            await ctx.reply("The end must be before the start.")
            return
        
        start_tick = max(start_tick, 0)
        end_tick = min(end_tick, current_tick)
        
        stonk_history = u_stonks.stonk_history()

        lines = []

        for stonk in stonks:
            values = []

            for tick_number, tick in enumerate(stonk_history[start_tick:end_tick + 1]):
                if stonk.internal_name not in tick:
                    continue

                values.append((tick_number + start_tick, tick[stonk.internal_name]))
            
            if len(values) == 0:
                continue

            lines.append({
                "label": stonk.name,
                "color": stonk.graph_color,
                "values": values
            })
        
        file_name = u_images.generate_graph(
            lines = lines,
            x_label = "Tick number",
            y_label = "Stonk value",
            log_scale = log_scale
        )

        await ctx.reply(file=discord.File(file_name))
    





    ######################################################################################################################################################
    ##### STONK REPORT ###################################################################################################################################
    ######################################################################################################################################################
    
    @stonk.command(
        name = "report",
        description = "Sends the last stonk report.",
        brief = "Sends the last stonk report."
    )
    async def stonk_report(self, ctx):
        ctx = u_custom.CustomContext(ctx)

        try:
            await ctx.reply(file=discord.File(f"images{SLASH}generated{SLASH}stonk_report.png"))
        except FileNotFoundError:
            await ctx.reply("Unfortunately I don't appear have a copy of the stonk report.")
    





    ######################################################################################################################################################
    ##### STONK PORTFOLIO GRAPH ##########################################################################################################################
    ######################################################################################################################################################
    
    @stonk.command(
        name = "portfolio_graph",
        description = "Shows a graph of a portfolio.\nThis does require you to reply to a portfolio.",
        brief = "Shows a graph of a portfolio."
    )
    async def stonk_portfolio_graph(self, ctx,
            start: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The start tick of the graph."),
            end: typing.Optional[u_converters.parse_int] = commands.parameter(description = "The end tick of the graph.")
        ):
        ctx = u_custom.CustomContext(ctx)

        replied_to = u_interface.replying_mm_checks(ctx.message, require_reply=True, return_replied_to=True)

        if not replied_to:
            await ctx.reply("You must reply to a portfolio to get a graph of it.")
            return
        
        parsed = u_bread.parse_stats(replied_to)

        if parsed.get("stats_type") != "portfolio":
            await ctx.reply("You must reply to a portfolio to get a graph of it.")
            return

        if start is None:
            start = 0
        if end is None:
            end = u_stonks.current_tick_number()
        
        if end <= start:
            await ctx.reply("The start must be before the end.")
            return
        
        start = max(start, 0)
        end = min(end, u_stonks.current_tick_number())

        stonk_history = u_stonks.stonk_history()

        def sum_portfolio(portfolio: dict, tick: dict) -> int:
            return sum([portfolio[stonk] * tick.get(stonk.internal_name, 0) for stonk in portfolio])

        portfolio = {stonk: parsed["stats"].get(stonk, 0) for stonk in u_values.stonks}

        values = []

        total_splits = 0

        previous_tick = None
        for tick_id, tick_data in enumerate(stonk_history[start:end]):
            if previous_tick is not None:
                for stonk in previous_tick:
                    if not (tick_data[stonk] / previous_tick[stonk] < 0.85):
                        continue

                    for i in range(50):
                        total_splits += 1
                        previous_tick[stonk] /= 2
                        portfolio[u_values.get_item(stonk)] *= 2
                        if not tick_data[stonk] / previous_tick[stonk] < 0.85:
                            break

            values.append((tick_id + start, sum_portfolio(portfolio, tick_data)))
            previous_tick = tick_data

        file_name = u_images.generate_graph(
            lines = [{
                "label": "Portfolio", # Underscore at the start to not put it in the legend.
                "color": "#1f77b4",
                "values": values
            }],
            x_label = "Tick number",
            y_label = "Portfolio value",
        )

        await ctx.reply(file=discord.File(file_name))

        





async def setup(bot: commands.Bot):
    cog = Stonk_cog()
    cog.bot = bot
    
    # Add attributes for sys.modules and globals() so the _reload_module() function in utility.custom can read it and get the module objects.
    cog.modules = sys.modules
    cog.globals = globals()
    
    await bot.add_cog(cog)