"""Bread Game solvers using z3."""
from __future__ import annotations

from discord.ext import commands
import discord
import re

# pip install z3-solver
import z3

import utility.values as u_values
import utility.custom as u_custom
import utility.interface as u_interface
import utility.text as u_text

import importlib

importlib.reload(u_values)

def universal_solver(
        items: dict[u_values.Item, int],
        maximize: u_values.Item,
        disabled_recipes: list[str] = None
    ) -> dict[str, int]:
    """Universal solver.

    Args:
        items (dict[u_values.Item, int]): A dict with the amount of each item is has to play around with.
        maximize (u_values.Item): The item to maximize.

    Returns:
        dict[str, int]: A dict version of the z3 model.
    """
    if disabled_recipes is None:
        disabled_recipes = []

    items[maximize] = 0

    s = z3.Optimize()

    item_amounts = {}
    item_modifiers = {}
    item_totals = {}
    item_recipes = {}

    modifier_data = {item: [] for item in items}

    recipes = u_values.alchemy_recipes.copy()

    recipes.update(u_values.misc_conversions)

    for item, amount in items.items():
        item_amounts[item] = z3.Int(f"{item.internal_name}_amounts")
        item_modifiers[item] = z3.Int(f"{item.internal_name}_modifier")
        item_totals[item] = z3.Int(f"{item.internal_name}_total")

        s.add(item_totals[item] == (amount + item_modifiers[item]))
        s.add(item_totals[item] >= 0, item_amounts[item] >= 0)

        if item.internal_name not in recipes:
            continue

        for recipe_id, recipe in enumerate(recipes[item.internal_name]):
            recipe_name = f"{item.internal_name}_recipe_{recipe_id + 1}"
            if recipe_name in disabled_recipes:
                continue

            for cost_item, cost_amount in recipe["cost"]:
                if cost_item not in modifier_data:
                    break
                
                modifier_data[cost_item].append((recipe_name, cost_amount * -1))
            else:
                item_recipes[recipe_name] = z3.Int(recipe_name)

                s.add(item_recipes[recipe_name] >= 0)

                modifier_data[item].append((recipe_name, recipe.get("result", 1)))

    for item, data in modifier_data.items():
        constraints = []
        for recipe, multiplier in data:
            constraints.append((item_recipes[recipe] * multiplier))

        s.add(item_modifiers[item] == z3.Sum(constraints))

    s.maximize(item_totals[maximize])

    for minimize in item_recipes.values():
        s.minimize(minimize)

    if s.check() != z3.sat:
        raise z3.Z3Exception("No solution found")
    
    model = s.model()

    result_json = {"state":"valid"}

    items_send = []

    for item in model:
        items_send.append(item)

    for item in items_send:
        result_json[str(item)] = model[item].as_long()

    return result_json

def solver_wrapper(
        items: dict[u_values.Item, int],
        maximize: u_values.Item,
        disabled_recipes: list[str] = None
    ) -> tuple[list[str], dict[u_values.Item, int], dict[str, int]]:
    """Wrapper for the universal_solver that automatically generates the command list.

    Args:
        items (dict[u_values.Item, int]): A dict with the amount of each item is has to play around with.
        maximize (u_values.Item): The item to maximize.

    Returns:
        tuple[list[str], dict[u_values.Item, int], dict[str, int]]: The command list, post-alchemy version of the items, and the dict version of the solver.
    """
    if disabled_recipes is None:
        disabled_recipes = []

    solver_result = universal_solver(
        items = items.copy(),
        maximize = maximize,
        disabled_recipes = disabled_recipes
    )

    # Quick alchemy simulation to determine the command order.
    command_list = []
    item_copy = items.copy()

    recipe_list = u_values.alchemy_recipes.copy()
    recipe_list.update(u_values.misc_conversions)

    recipes = [name for name, value in solver_result.items() if "recipe" in name and value >= 1]

    for i in range(len(recipes)):
        for recipe_name in recipes.copy():
            recipe_item = recipe_name.split("_recipe_")[0]
            recipe_id = int(recipe_name.split("_recipe_")[-1])
            recipe_amount = solver_result[recipe_name]

            alchemy_data = recipe_list[recipe_item][recipe_id - 1]
            for cost_item, cost_value in alchemy_data["cost"]:
                if not item_copy[cost_item] >= cost_value * recipe_amount:
                    break
            else:
                command_list.append(f"$bread distill {solver_result[recipe_name]} {recipe_item} {recipe_id} y")

                for cost_item, cost_value in alchemy_data["cost"]:
                    item_copy[cost_item] -= cost_value * recipe_amount

                item_copy[u_values.get_item(recipe_item)] += alchemy_data.get("result", 1) * recipe_amount
                
                recipes.remove(recipe_name)
                break
    
    if len(recipes) >= 1:
        print(f"WARNING! Unused recipes! {recipes}")
    
    final_replacements: list[tuple[str, str]] = [ # (<old pattern>, <replacement pattern>)
        (r"\$bread \w+ (\d+) chessatron 1 .+", r"$bread chessatron \1"),
        (r"\$bread \w+ (\d+) chessatron 2 .+", r"$bread gem_chessatron \1"),
        (r"\$bread \w+ (\d+) anarchy_chessatron 1 .+", r"$bread anarchy_chessatron \1"),
    ]

    for old, new in final_replacements:
        for index, command in enumerate(command_list):
            command_list[index] = re.sub(old, new, command)
    
    return (command_list, item_copy, solver_result)

async def solver_embed(
        ctx: commands.Context | u_custom.CustomContext,
        inventory: dict[u_values.Item, int],
        goal_item: u_values.Item,
        disabled_recipes: list[str]
    ) -> discord.Embed:
    """Given an inventory item dictionary, goal item, and disabled recipies it will run the solver and generate the output embed."""
    # Run the solver.
    try:
        await ctx.message.add_reaction("✅")
    except:
        pass
    
    command_list, post_alchemy, solver_result = solver_wrapper(
        items = inventory,
        maximize = goal_item,
        disabled_recipes = disabled_recipes
    )

    ################
    
    return u_interface.gen_embed(
        title = f"{goal_item.name} solver",
        description = "Inventory changes:\n{}\nYou should be able to make **{}** {}.".format(
            "\n".join([
                f"{item}: {u_text.smart_number(inventory[item])} -> {u_text.smart_number(post_alchemy[item])}"
                for item in inventory
                if inventory[item] != post_alchemy[item]
            ]),
            u_text.smart_number(solver_result[f"{goal_item.internal_name}_total"]),
            goal_item,
        ),
        fields = [
            ("Commands:", "\n".join(command_list), False)
        ],
        footer_text = "On mobile you can tap and hold on the commands section to copy it."
    )