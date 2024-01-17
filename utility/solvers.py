"""Bread Game solvers using z3."""

import z3

import utility.values as u_values

def gold_gem_solver(*, gem_red: int, gem_blue: int, gem_purple: int, gem_green: int) -> dict:
    """Runs the gold gem solver.

    Args:
        gem_red (int): The number of red gems.
        gem_purple (int): The number of purple gems.
        gem_blue (int): The number of blue gems.
        gem_green (int): The number of green gems.

    Returns:
        dict: A dict version of the z3 model.
    """
    gems = {
        u_values.gem_red: gem_red,
        u_values.gem_blue: gem_blue,
        u_values.gem_purple: gem_purple,
        u_values.gem_green: gem_green,
        u_values.gem_gold: 0
    }

    s = z3.Optimize()

    gem_amounts = {}
    gem_modifiers = {}
    gem_totals = {}
    gem_recipes = {}

    modifier_data = {gem: [] for gem in gems}

    for gem, amount in gems.items():
        gem_amounts[gem] = z3.Int(f"{gem.internal_name}_amounts")
        gem_modifiers[gem] = z3.Int(f"{gem.internal_name}_modifier")
        gem_totals[gem] = z3.Int(f"{gem.internal_name}_total")

        s.add(gem_totals[gem] == (amount + gem_modifiers[gem]))
        s.add(gem_totals[gem] >= 0, gem_amounts[gem] >= 0)

        if gem.internal_name not in u_values.alchemy_recipes:
            continue

        for recipe_id, recipe in enumerate(u_values.alchemy_recipes[gem.internal_name]):
            recipe_name = f"{gem.internal_name}_recipe_{recipe_id + 1}"
            gem_recipes[recipe_name] = z3.Int(recipe_name)
            for cost_item, cost_amount in recipe["cost"]:
                if cost_item not in modifier_data:
                    del gem_recipes[recipe_name]
                    break
                
                modifier_data[cost_item].append((recipe_name, cost_amount * -1))
            else:

                s.add(gem_recipes[recipe_name] >= 0)

                modifier_data[gem].append((recipe_name, recipe.get("result", 1)))

    for gem, data in modifier_data.items():
        constraints = []
        for recipe, multiplier in data:
            constraints.append((gem_recipes[recipe] * multiplier))

        s.add(gem_modifiers[gem] == z3.Sum(constraints))

    s.maximize(gem_totals[u_values.gem_gold])

    for maximize in gem_recipes.values():
        s.minimize(maximize)

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

                        
                

