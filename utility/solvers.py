"""Specific Bread Game solvers using z3, and other mathematical solvers."""
from __future__ import annotations
import multiprocessing.queues

from discord.ext import commands
import discord
import re
import mpmath
import decimal
import time
import operator
import multiprocessing

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
        disabled_recipes: list[str] = None,
        disabled_items: list[u_values.Item] = None,
        minimum_items: dict[u_values.Item, int] = None,
        output: multiprocessing.Queue = None
    ) -> dict[str, int]:
    """Universal solver.

    Args:
        items (dict[u_values.Item, int]): A dict with the amount of each item is has to play around with.
        maximize (u_values.Item): The item to maximize.

    Returns:
        dict[str, int]: A dict version of the z3 model.
    """
    try:
        if disabled_recipes is None:
            disabled_recipes = []
        if disabled_items is None:
            disabled_items = []
        if minimum_items is None:
            minimum_items = {}

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

            if item in disabled_items:
                s.add(item_modifiers[item] == 0)

            for recipe_id, recipe in enumerate(recipes[item.internal_name]):
                recipe_name = f"{item.internal_name}_recipe_{recipe_id + 1}"
                if recipe_name in disabled_recipes:
                    continue

                if any(filter(lambda i: i[0] in disabled_items, recipe["cost"])):
                    continue

                for cost_item, cost_amount in recipe["cost"]:
                    if cost_item not in modifier_data:
                        break

                    if cost_item in disabled_items:
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
        
        for item, minimum in minimum_items.items():
            s.add(item_totals[item] >= minimum)

        s.maximize(item_totals[maximize])

        for minimize in item_recipes.values():
            s.minimize(minimize)
        
        # s.minimize(z3.Sum(list(item_recipes.values())))

        if s.check() != z3.sat:
            output.put({"state": "unsat"})
            return
        
        model = s.model()

        result_json = {"state":"valid"}

        items_send = []

        for item in model:
            items_send.append(item)

        for item in items_send:
            result_json[str(item)] = model[item].as_long()

        output.put(result_json)
    except Exception as error:
        output.put({"state": "error", "exception": error})

def solver_wrapper(
        items: dict[u_values.Item, int],
        maximize: u_values.Item,
        disabled_recipes: list[str] = None,
        disabled_items: list[u_values.Item] = None,
        minimum_items: dict[u_values.Item, int] = None,
        timeout_time: int | float = 30.0
    ) -> tuple[list[str], dict[u_values.Item, int], dict[str, int]] | None:
    """Wrapper for the universal_solver that automatically generates the command list.

    Args:
        items (dict[u_values.Item, int]): A dict with the amount of each item is has to play around with.
        maximize (u_values.Item): The item to maximize.
        disabled_recipes (list[str], optional): List of recipes to disable in the format of `<item>_recipe_<recipe id>` where recipe id is 1 indexed. `None` is functionally the same as an empty list. Defaults to None.
        disabled_items (list[u_values.Item], optional): List of items to disallow the solver from using. Defaults to None.
        timeout_time (int | float, optional): Amount of time to give the solver before killing it. Defaults to 30.0.

    Returns:
        tuple[list[str], dict[u_values.Item, int], dict[str, int]] | None: The command list, post-alchemy version of the items, and the dict version of the solver. If `None` is returned then the timeout was encountered.
    """
    if disabled_recipes is None:
        disabled_recipes = []
    if disabled_items is None:
        disabled_items = []
    if minimum_items is None:
        minimum_items = {}

    # Go through `minimum_items` to make sure every item in it is also in `items`.
    for key in minimum_items.copy():
        if key not in items:
            minimum_items.pop(key)

    # Run the solver in a new thread.
    queue = multiprocessing.Queue()

    process = multiprocessing.Process(
        None,
        universal_solver,
        args=(
            items.copy(),
            maximize,
            disabled_recipes,
            disabled_items,
            minimum_items,
            queue
        )
    )
    process.start()

    # solver_result = universal_solver(
    #     items = items.copy(),
    #     maximize = maximize,
    #     disabled_recipes = disabled_recipes,
    #     disabled_items = disabled_items
    # )

    process.join(timeout_time)

    if process.is_alive():
        process.terminate()
        return None
    
    solver_result = queue.get()

    if solver_result.get("state") == "unsat":
        return False

    if solver_result.get("state") == "error":
        raise solver_result.get("exception")

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
        disabled_recipes: list[str] = None,
        disabled_items: list[u_values.Item] = None,
        minimum_items: dict[u_values.Item, int] = None,
    ) -> discord.Embed:
    """Given an inventory item dictionary, goal item, disabled recipes, and disabled items it will run the solver and generate the output embed."""
    # Run the solver.
    try:
        await ctx.message.add_reaction("✅")
    except:
        pass
    
    full_result = solver_wrapper(
        items = inventory,
        maximize = goal_item,
        disabled_recipes = disabled_recipes,
        disabled_items = disabled_items,
        minimum_items = minimum_items
    )

    if not full_result:
        if full_result is None:
            return u_interface.gen_embed(
                title = f"{goal_item.name} solver",
                description = "Timeout reached.\nThe solver took too long to run and was stopped before it found a solution. Please do not try again, as the same thing will likely occur."
            )
        else:
            return u_interface.gen_embed(
                title = f"{goal_item.name} solver",
                description = "Impossible restraints.\nThe solver does not think a solution is possible given the restraints.\nIf you're setting the amount of an item to end up with (like `chessatron=25`), that is likely the problem."
            )

    command_list, post_alchemy, solver_result = full_result

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















########################################################################################################################
########################################################################################################################
########################################################################################################################

# Amount of digits to show.
# This influences mpmath.mp.dps and decimals.getcontext().prec
SOLVER_PRECISION = 64

def floor_inputs(f):
    def wrapped(a, b):
        return decimal.Decimal(f(int(a), int(b)))
    
    return wrapped

def clamp_inputs(f, clamp):
    def wrapped(a, b):
        if a > clamp:
            raise u_custom.BingoError(f"Given argument `{a}` above set clamp of {clamp}.")
        if b > clamp:
            raise u_custom.BingoError(f"Given argument `{b}` above set clamp of {clamp}.")
        return f(a, b)
    
    return wrapped

def mpwrapper(f):
    def wrapped(*args):
        mpmath.mp.dps = SOLVER_PRECISION + 4
        return decimal.Decimal(str(f(*args)))

    return wrapped

NUMBER_REGEX = r"((-?[\d,\.]+(e[\+\-]?\d+)?)|pi|e|tau|phi|π|τ|φ)"
FUNCTION_LIST = ["sin", "tan", "cos", "asin", "atan", "acos", "ln", "log", "factorial", "sqrt", "exp", "nCr", "nPr", "floor", "ceiling", "ceil"]
FUNCTION_REGEX = rf"({'|'.join(FUNCTION_LIST)})"

FUNCTION_LIST_SORTED = list(sorted(FUNCTION_LIST, key=lambda l: len(l), reverse=True))

FULL_EQUATION_PATTERN = rf"({NUMBER_REGEX}?({FUNCTION_REGEX}|([ ()]*))([\^\/\+\*\-\%\&\|]|>>|<<|\*\*|\/\/)?({FUNCTION_REGEX}|([ ()]*)){NUMBER_REGEX}?)+"
FUNCTION_PATTERN = rf"{FUNCTION_REGEX}\((({NUMBER_REGEX},? *)+)\)"

REGEX_EVALUATE = re.compile(rf"^{NUMBER_REGEX}( *)([\^\/\+\*\-\%\&\|]|>>|<<|\*\*|\/\/)( *){NUMBER_REGEX}$")
REGEX_FUNCTION = re.compile(rf"^{FUNCTION_PATTERN}$")

"""
Order of operations:
1. **
2. */% //
3. +-
4. <<
5. >>
6. &
7. ^
8. |
"""
REGEX_EXPONENTS = re.compile(rf"{NUMBER_REGEX}( *)(\*\*)( *){NUMBER_REGEX}")
REGEX_MULTIPLICATIVE = re.compile(rf"{NUMBER_REGEX}( *)([\*\/\%]|\/\/)( *){NUMBER_REGEX}")
REGEX_ADDITIVE = re.compile(rf"{NUMBER_REGEX}( *)([\+\-])( *){NUMBER_REGEX}")
REGEX_SHIFT_LEFT = re.compile(rf"{NUMBER_REGEX}( *)(<<)( *){NUMBER_REGEX}")
REGEX_SHIFT_RIGHT = re.compile(rf"{NUMBER_REGEX}( *)(>>)( *){NUMBER_REGEX}")
REGEX_BIT_AND = re.compile(rf"{NUMBER_REGEX}( *)(\&)( *){NUMBER_REGEX}")
REGEX_BIT_XOR = re.compile(rf"{NUMBER_REGEX}( *)(\^)( *){NUMBER_REGEX}")
REGEX_BIT_OR = re.compile(rf"{NUMBER_REGEX}( *)(\|)( *){NUMBER_REGEX}")

ORDER_OF_OPERATIONS = [REGEX_EXPONENTS, REGEX_MULTIPLICATIVE, REGEX_ADDITIVE, REGEX_SHIFT_LEFT, REGEX_SHIFT_RIGHT, REGEX_BIT_AND, REGEX_BIT_XOR, REGEX_BIT_OR]

OPERATIONS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "//": operator.floordiv,
    "**": operator.pow,
    "%": operator.mod,
    "&": floor_inputs(operator.and_),
    "|": floor_inputs(operator.or_),
    "^": floor_inputs(operator.xor),
    "<<": clamp_inputs(floor_inputs(operator.lshift), 4096),
    ">>": clamp_inputs(floor_inputs(operator.rshift), 4096),
}

mpmath.mp.dps = SOLVER_PRECISION + 4

OTHER_CONSTANTS = {
    "π": decimal.Decimal(str(mpmath.mp.pi)),
    "pi": decimal.Decimal(str(mpmath.mp.pi)),
    "tau": decimal.Decimal(str(mpmath.mp.pi * 2)), # i'm sorry savings, mpmath doesnt have tau
    "τ": decimal.Decimal(str(mpmath.mp.pi * 2)),
    "e": decimal.Decimal(str(mpmath.mp.e)),
    "φ": decimal.Decimal(str(mpmath.mp.phi)),
    "phi": decimal.Decimal(str(mpmath.mp.phi)),
}

def nCr(n, k):
    f = OTHER_OPERATIONS["factorial"]
    return f(n) / (f(k) * f(n - k))

def nPr(n, k):
    f = OTHER_OPERATIONS["factorial"]
    return f(n) / f(n - k)

def square_root_wrapper(n):
    if n < 0:
        raise u_custom.BingoError("I don't have support for complex numbers, so please avoid the square root of negative numbers.")
    return mpwrapper(mpmath.sqrt)(n)

OTHER_OPERATIONS = {
    "sin": mpwrapper(mpmath.sin),
    "cos": mpwrapper(mpmath.cos),
    "tan": mpwrapper(mpmath.tan),
    "asin": mpwrapper(mpmath.asin),
    "acos": mpwrapper(mpmath.acos),
    "atan": mpwrapper(mpmath.atan),
    "log": mpwrapper(mpmath.log),
    "ln": lambda n: mpwrapper(mpmath.log)(n), # math.log without a base argument is natural log
    "factorial": mpwrapper(mpmath.factorial),
    "sqrt": square_root_wrapper,
    "exp": mpwrapper(mpmath.exp),
    "nCr": nCr,
    "nPr": nPr,
    "floor": mpwrapper(mpmath.floor),
    "ceiling": mpwrapper(mpmath.ceil),
    "ceil": mpwrapper(mpmath.ceil),
}

def evaluate_problem(
        equation: str,
        timeout_time: int | float = 2.5
    ) -> decimal.Decimal:
    """Attempts to parse and solve a math equation like `2 - 7 / (4 * 9) ** sin(10 // 9 * pi) - 10 - (8 ** 3 * 5) + (7 + 10) / 2 // 5 ** 5`. All bitwise operations other than NOT (`~`) are allowed, but all inputs will be floored.

    Args:
        equation (str): The equation to solve.
        timeout_time (int | decimal.Decimal, optional): How long to give `while` loops time to run, in seconds. Defaults to 1.0.

    Raises:
        ValueError: Something went wrong when parsing the equation somewhere.
        RuntimeError: The timeout has been triggered.

    Returns:
        decimal.Decimal: The calculated result.
    """

    def parse_float(i: str) -> decimal.Decimal:
        if i in OTHER_CONSTANTS:
            return OTHER_CONSTANTS[i]
        return decimal.Decimal(i.replace(",", ""))

    def final_check(i: str) -> bool:
        try:
            parse_float(i)
            return True
        except:
            return False
    
    def evaluate_function(eq: str) -> decimal.Decimal:
        m = REGEX_FUNCTION.match(eq)
        try:
            function = m.group(1)

            if function not in OTHER_OPERATIONS:
                raise u_custom.BingoError(f"Function `{function}` not found.")

            arguments = [i.strip() for i in m.group(2).split(",")]
            for index, arg in enumerate(arguments):
                arguments[index] = parse_float(arg)
            
            try:
                return OTHER_OPERATIONS[function](*arguments)
            except ValueError:
                raise u_custom.BingoError(f"Invalid domain for function `{function}`.")
            except TypeError:
                raise u_custom.BingoError(f"Incorrect argument amount for function `{function}`")

            
        except AttributeError:
            raise u_custom.BingoError(f"Function `{eq}` failed to parse.")


    def evaluate(eq: str) -> decimal.Decimal:
        m = REGEX_EVALUATE.match(eq)
        try:
            start = parse_float(m.group(1))
            operation = m.group(5)
            end = parse_float(m.group(7))
        except AttributeError:
            raise u_custom.BingoError(f"Equation `{eq}` failed to parse.")

        return OPERATIONS[operation](start, end)

    def evaluate_set(eq: str) -> str:
        c = eq
        if "(" in c:
            while "(" in c:
                if c.count("(") != c.count(")"):
                    raise u_custom.BingoError(f"Mismatching amount of parentheses in case `{c}`.")
                
                c = substitute_parentheses(c)
                
                if time.time() > timeout:
                    raise u_custom.BingoError(f"Timeout of {timeout_time} reached.")
        
        while not final_check(c):
            found = False
            for pattern in ORDER_OF_OPERATIONS:
                search = list(pattern.finditer(c))
                while search: # If search has items in it.
                    item = search[0]

                    if item.group(0).startswith("e"):
                        if c[item.start(0) - 1].isdigit():
                            search.pop(0)
                            continue

                    found = True
                    num = evaluate(item.group(0))

                    if num.is_nan():
                        raise u_custom.BingoError(f"Encountered NaN in case `{c}`. >:(")
                    if num.is_infinite():
                        raise u_custom.BingoError(f"Encountered infinity in case `{c}`. >:(")
                    
                    if num > 9e+4096:
                        raise OverflowError
                    
                    c = c.replace(item.group(0), str(num))
                    
                    search = list(pattern.finditer(c))
                    if time.time() > timeout:
                        raise u_custom.BingoError(f"Timeout of {timeout_time} reached.")
            
            if not found:
                raise u_custom.BingoError(f"Invalid equation in case `{c}`.")
                    
            if time.time() > timeout:
                raise u_custom.BingoError(f"Timeout of {timeout_time} reached.")

        return c

    def find_parentheses(eq: str) -> str:
        if "(" not in eq:
            raise u_custom.BingoError(f"No parentheses found in `{eq}`.")
        
        start = eq.find("(")
        current = "("

        amount = 1
        i = start + 1
        m = len(eq)
        while amount > 0:
            if i >= m:
                raise u_custom.BingoError(f"Equation `{eq}` failed to find proper parentheses.")
            
            char = eq[i]
            current += char

            if char == "(":
                amount += 1
            elif char == ")":
                amount -= 1
            
            i += 1
        
        return current

    def substitute_parentheses(eq: str) -> str:
        found = find_parentheses(eq)

        functions = [f"{i}(" in eq for i in FUNCTION_LIST_SORTED]
        if any(functions):
            function = FUNCTION_LIST_SORTED[functions.index(True)]
            location = eq.index(function)
            function_inside = find_parentheses(eq[location:])[1:-1]
            arguments = [i.strip() for i in function_inside.split(",")]

            for index, arg in enumerate(arguments):
                arguments[index] = evaluate_set(arg)
            
            solved = evaluate_function(f"{function}({', '.join(arguments)})")

            return eq.replace(f"{function}({function_inside})", str(solved))
        
        return eq.replace(found, evaluate_set(found[1:-1]))

    decimal.getcontext().prec = SOLVER_PRECISION + 2
    decimal.getcontext().capitals = 0
    
    timeout = time.time() + timeout_time
    result = evaluate_set(equation)
    out = parse_float(result)

    decimal.getcontext().prec -= 2
    return +out

##############################################################################################################################################################

def is_math_equation(input_string: str) -> bool:
    """Attempts to determine whether the given input string is a math equation. There are certain situations where this may be incorrect, you can use `evaluate_problem()` to get a more accurate answer, but that requires more computation.

    Args:
        input_string (str): The input string.

    Returns:
        bool: Whether the string is a math equation.
    """
    NUMBERS = "0123456789"
    OPERATORS = "+-*/%&|^<>"
    DUPLICATES = "/*<>"

    parenthesis_level = 0

    NUMBER = 1
    OPERATOR = 2
    FUNCTION = 3
    DELIMITER = 4
    OPEN = 5
    CLOSE = 6
    NEGATIVE = 7

    log = [0]
    length = len(input_string)

    IN_NUMBER = 1 << 0
    FUNCTION_NAME = 1 << 1
    DECIMAL_FOUND = 1 << 2

    state = 0
    checkpoint = 0
    function_stack = []

    def parse_text(i):
        nonlocal state, log
        if not (state & FUNCTION_NAME):
            return True
        
        state -= FUNCTION_NAME
        
        text = input_string[checkpoint:i]

        if text in FUNCTION_LIST:
            log.append(FUNCTION)
            return False
        if text in OTHER_CONSTANTS:
            log.append(NUMBER)
            return False
        
        raise u_custom.BingoError(f"Unrecognized function or constant `{text}`.")
    
    def surrounding(i):
        return f"(`{input_string[max(0, i - 2):min(length, i + 3)]}`)"

    for index, char in enumerate(input_string):
        past = "_" + input_string[:index]
        
        if char == ",":
            parse_text(index)
            
            if state & IN_NUMBER and len(function_stack) == 0:
                continue

            log.append(DELIMITER)
            continue

        if char == ".":
            parse_text(index)
            
            if state & IN_NUMBER:
                if state & DECIMAL_FOUND:
                    raise u_custom.BingoError(f"Unrecognized decimal point at character {index + 1} {surrounding(index)}.")
                else:
                    state += DECIMAL_FOUND
                continue
            
            raise u_custom.BingoError(f"Unrecognized decimal point at character {index + 1} {surrounding(index)}.")

        # Ignore spaces.
        if char == " ":
            parse_text(index)

            if state & IN_NUMBER:
                state -= IN_NUMBER
            continue

        ##################################

        if char == "(":
            last_log = log[-1]
            
            if last_log == NUMBER or last_log == CLOSE:
                raise u_custom.BingoError(f"Unexpected opening parenthesis at character {index + 1} {surrounding(index)}.")
            
            # This shouldn't be needed, but just in case...
            if state & IN_NUMBER:
                state -= IN_NUMBER

            ### Dealing with functions.

            if state & FUNCTION_NAME:
                state -= FUNCTION_NAME

                function_name = input_string[checkpoint:index]

                if function_name not in FUNCTION_LIST:
                    raise u_custom.BingoError(f"Unrecognized function name `{function_name}` {surrounding(index)}.")
                
                log.append(FUNCTION)

                function_stack.append(parenthesis_level)

            ###

            log.append(OPEN)
            parenthesis_level += 1
            continue
        
        if char == ")":
            parse_text(index)
            
            last_log = log[-1]

            if last_log == OPEN:
                raise u_custom.BingoError(f"Unexpected closing parenthesis directly after opening parenthesis at character {index + 1} {surrounding(index)}.")
            
            if last_log == OPERATOR:
                raise u_custom.BingoError(f"Unexpected closing parenthesis at character {index + 1} {surrounding(index)}.")
            
            log.append(CLOSE)
            parenthesis_level -= 1

            if len(function_stack) > 0:
                if parenthesis_level == function_stack[-1]:
                    function_stack.pop()

            if state & IN_NUMBER:
                state -= IN_NUMBER
            
            if parenthesis_level < 0:
                raise u_custom.BingoError(f"Unmatched closing parenthesis at character{index + 1} {surrounding(index)}.")
            continue

        if char in NUMBERS:
            parse_text(index)

            if state & IN_NUMBER:
                continue
            else:
                last_log = log[-1]

                if last_log == NUMBER:
                    raise u_custom.BingoError(f"Unexpected number at character {index + 1} {surrounding(index)}.")
                
                if last_log == CLOSE:
                    raise u_custom.BingoError(f"Unexpected number at character {index + 1} {surrounding(index)}.")
                
                state += IN_NUMBER
                if state & DECIMAL_FOUND:
                    state -= DECIMAL_FOUND
                log.append(NUMBER)
                continue
        
        if char in OPERATORS:
            parse_text(index)
            
            if past[-1] in OPERATORS: # Can't use log[-1] here due to spaces.
                if char == "-":
                    if not (state & IN_NUMBER):
                        state += IN_NUMBER
                    log.append(NEGATIVE)
                    continue

                if char not in DUPLICATES:
                    raise u_custom.BingoError(f"Unexpected operator `{char}` at character {index + 1} {surrounding(index)}.")
                elif char != past[-1]:
                    raise u_custom.BingoError(f"Unexpected operator `{char}` at character {index + 1} {surrounding(index)}.")
                else: # If it is the same, and is a duplicate operator.
                    continue
            else:
                if log[-1] == NUMBER or log[-1] == CLOSE:
                    if state & IN_NUMBER:
                        state -= IN_NUMBER

                    log.append(OPERATOR)
                    continue
                elif char == "-" and (log[-1] == OPEN or log[-1] == 0 or log[-1] == OPERATOR):
                    log.append(NEGATIVE)
                    continue
                else:
                    raise u_custom.BingoError(f"Unexpected operator `{char}` at character {index + 1} {surrounding(index)}.")
        
        # If it's here then assume it's part of a function.
        if state & FUNCTION_NAME:
            continue
        
        checkpoint = index
        state += FUNCTION_NAME
            
    if parenthesis_level > 0:
        raise u_custom.BingoError("Unmatched opening parenthesis.")
    
    parse_text(length)

    return True

def is_math_equation_bool(input_string: str) -> bool:
    """Converts `is_math_equation` into a boolean, and catches any BingoErrors that occcur.
    
    Args:
        input_string (str): The input string.

    Returns:
        bool: Whether the string is a math equation."""
    try:
        return is_math_equation(input_string)
    except u_custom.BingoError:
        return False