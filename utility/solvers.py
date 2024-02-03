"""Bread Game solvers using z3."""

import re

# pip install z3-solver
import z3

import utility.values as u_values

import importlib

importlib.reload(u_values)

def universal_solver(items: dict[u_values.Item, int], maximize: u_values.Item) -> dict[str, int]:
    """Universal solver.

    Args:
        items (dict[u_values.Item, int]): A dict with the amount of each item is has to play around with.
        maximize (u_values.Item): The item to maximize.

    Returns:
        dict[str, int]: A dict version of the z3 model.
    """

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
            for cost_item, cost_amount in recipe["cost"]:
                if cost_item not in modifier_data:
                    # del item_recipes[recipe_name]
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

def solver_wrapper(items: dict[u_values.Item, int], maximize: u_values.Item) -> tuple[list[str], dict[u_values.Item, int], dict[str, int]]:
    """Wrapper for the universal_solver that automatically generates the command list.

    Args:
        items (dict[u_values.Item, int]): A dict with the amount of each item is has to play around with.
        maximize (u_values.Item): The item to maximize.

    Returns:
        tuple[list[str], dict[u_values.Item, int], dict[str, int]]: The command list, post-alchemy version of the items, and the dict version of the solver.
    """

    solver_result = universal_solver(items=items.copy(), maximize=maximize)

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
    
    final_replacements = [ # type: list[tuple[str, str]], (<old pattern>, <replacement pattern>)
        (r"\$bread \w+ (\d+) chessatron .+", r"$bread chessatron \1")
    ]

    for old, new in final_replacements:
        for index, command in enumerate(command_list):
            command_list[index] = re.sub(old, new, command)
    
    return (command_list, item_copy, solver_result)