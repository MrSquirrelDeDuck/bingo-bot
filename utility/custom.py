"""Custom versions of discord.py objects.

Note that in order to reload this code utility.custom needs to be reloaded, and then every cog that uses it."""

import typing
import discord
from discord.ext import commands
import traceback

import importlib

import utility.text as u_text
import utility.interface as u_interface

everyone_prevention = discord.AllowedMentions(everyone=False)

class CustomCog(commands.Cog):
    """Custom discord.ext.commands cog that is used by the cog files to allow for universal code."""

    def __init__(
            self: typing.Self,
            **kwargs: typing.Any
        ) -> None:
        super().__init__(**kwargs)
    
    def _reload_module(
            self: typing.Self,
            module_name: str
        ) -> bool:
        """Reloads a module by name.
        For imports that are in a folder, the folder name must be included. For instance: `utility.files` would reload the utility.files code.
        Returns a bool for whether anything was reloaded, so the number of reloads can be counted."""

        # Get a list of the names of every module in globals(). This can be done with a list comprehension but this is easier to read.
        globals_modules = []

        for module in self.globals.values():
            if hasattr(module, "__name__"):
                globals_modules.append(module.__name__)
        
        # Get a list of every imported module via cross-checking globals_modules and sys.modules.
        all_modules = set(self.modules) & set(globals_modules)

        # If the provided module name 
        if module_name not in all_modules:
            return False
        
        # Get the module object.
        module = self.modules[module_name]

        # Reload the module via importlib.reload.
        importlib.reload(module)

        # Run the on_reload() function if it exists.
        try:
            module.on_reload()
        except AttributeError:
            pass

        print("- {} has reloaded {}.".format(self.qualified_name, module_name))

        # Return True, since it has been reloaded in theory.
        return True
    
    async def on_stonk_tick(
            self: typing.Self,
            message: discord.Message
        ) -> None:
        """Code that runs for every stonk tick."""
        pass
    
    async def hourly_task(self: typing.Self) -> None:
        """Code that runs for every hour."""
        pass
    
    async def daily_task(self: typing.Self) -> None:
        """Code that runs for every day."""
        pass

    def bingo_cache_updated(self: typing.Self) -> None:
        """Code that runs when the bingo cache is updated."""
        pass

    def save_all_data(self: typing.Self) -> None:
        """Saves all stored data to files."""
        pass

class CustomContext(commands.Context):    
    async def safe_reply(
            self: typing.Self,
            content: str = "",
            **kwargs
        ) -> discord.Message:        
        kwargs["allowed_mentions"] = everyone_prevention

        return await super().reply(content, **kwargs)
    
    async def send(
            self: typing.Self,
            content: str = "",
            **kwargs
        ) -> discord.Message:
        kwargs["allowed_mentions"] = everyone_prevention

        return await super().send(content, **kwargs)
    
    async def reply(
            self: typing.Self,
            content: str = "",
            **kwargs
        ) -> discord.Message | None:
        if (content is None or len(str(content)) == 0) and kwargs.get("embed", None) is None and kwargs.get("file", None) is None:
            return None
        
        try:
            return await self.safe_reply(content, **kwargs)
        except discord.HTTPException:
            # If something went wrong replying.
            if kwargs.get("mention_author", True):
                return await self.send(f"{self.author.mention},\n\n{content}", **kwargs)
            else:
                return await self.send(f"{u_text.ping_filter(u_interface.get_display_name(self.author))},\n\n{content}", **kwargs)
    
    async def send_help(
            self: typing.Self,
            *args: typing.Any
        ) -> typing.Any:
        """Slightly modified version of base Context send_help to pass ctx to the send_group_help method."""
        bot = self.bot
        cmd = bot.help_command

        if cmd is None:
            return None

        cmd = cmd.copy()
        cmd.context = self

        if len(args) == 0:
            await cmd.prepare_help_command(self, None)
            mapping = cmd.get_bot_mapping()
            injected = commands.core.wrap_callback(cmd.send_bot_help)
            try:
                return await injected(mapping)
            except commands.errors.CommandError as e:
                await cmd.on_help_command_error(self, e)
                return None

        entity = args[0]
        if isinstance(entity, str):
            entity = bot.get_cog(entity) or bot.get_command(entity)

        if entity is None:
            return None

        try:
            entity.qualified_name
        except AttributeError:
            # if we're here then it's not a cog, group, or command.
            return None

        await cmd.prepare_help_command(self, entity.qualified_name)

        try:
            if commands.context.is_cog(entity):
                injected = commands.core.wrap_callback(cmd.send_cog_help)
                return await injected(entity)
            elif isinstance(entity, commands.Group):
                injected = commands.core.wrap_callback(cmd.send_group_help)
                return await injected(entity, self)
            elif isinstance(entity, commands.Command):
                injected = commands.core.wrap_callback(cmd.send_command_help)
                return await injected(entity)
            else:
                return None
        except commands.errors.CommandError as e:
            await cmd.on_help_command_error(self, e)

class CustomBot(commands.Bot):
    # THIS CAN ONLY BE RELOADED BY RESTARTING THE ENTIRE BOT.
    
    async def get_context(
            self: typing.Self,
            message: discord.Message,
            *,
            cls=CustomContext):
        return await super().get_context(message, cls=cls)
    
    def update_bingo_cache(
            self: typing.Self,
            live_data: dict
        ) -> None:
        """Updates the bingo cache in all the cogs that have the bingo_cache attribute."""
        for cog in self.cogs.values():
            if hasattr(cog, "bingo_cache"):
                cog.bingo_cache = live_data
                cog.bingo_cache_updated()
    
    def save_all_data(self: typing.Self) -> None:
        """Runs save_all_data() in all the cogs.."""
        for cog in self.cogs.values():
            try:
                cog.save_all_data()
            except AttributeError:
                pass


class CustomHelpCommand(commands.DefaultHelpCommand):
    # THIS CAN ONLY BE RELOADED BY RESTARTING THE ENTIRE BOT.

    def get_ending_note(self: typing.Self) -> str:
        command_name = self.invoked_with

        return f'Type `{self.context.clean_prefix}{command_name} <command>` for more info on a command.\nYou can also type `{self.context.clean_prefix}{command_name} <category>` for more info on a category.'

    def get_opening_note(self: typing.Self) -> str:
        return self.get_ending_note()

    async def command_not_found(
            self: typing.Self,
            string: str
        ) -> None:
        embed_send = u_interface.gen_embed(
            title = "Bingo-Bot help",
            description = f"Command `{string}` not found."
        )
        return await self.context.reply(embed=embed_send)
    
    async def subcommand_not_found(
            self: typing.Self,
            command: commands.Command,
            string: str
        ) -> None:
        embed_send = u_interface.gen_embed(
            title = "Bingo-Bot help",
            description = f"Command `{command.qualified_name}` has no subcommand called `{string}`."
        )
        return await self.context.reply(embed=embed_send)

    async def send_cog_help(
            self: typing.Self,
            cog: commands.Cog | CustomBot
        ) -> None:
            
        command_lines = []
        all_commands = await self.filter_commands(cog.get_commands(), sort=self.sort_commands)

        for command in all_commands:
            try:

                command_description = command.brief

                if command_description is None:
                    command_description = command.help
                    if command_description is None:
                        command_description = ""

                if len(command_description) > 120:
                    command_description = f"{command_description[:120]}..."
                
                command_lines.append(f"- `{command.name}` -- {command_description}")
            except commands.CommandError:
                continue
        
        if len(command_lines) == 0:
            command_lines.append("*Nothing to list.*")
        
        embed = u_interface.gen_embed(
            title = "Bingo-Bot help",
            description = "{}\n\n**Commands:**\n{}\n\n{}".format(
                cog.description,
                "\n".join(command_lines),
                self.get_opening_note()
            )
        )
        await self.context.reply(embed=embed)
    
    async def send_bot_help(self: typing.Self) -> None:
        all_commands = await self.filter_commands(self.context.bot.commands, sort=self.sort_commands)
        all_commands = [(c.name, c) for c in all_commands]
        all_commands: dict[str, commands.Command] = dict(sorted(all_commands, key=lambda c: c[0]))

        command_data = {}
        listed = []
        for name, command in all_commands.items():
            try:
                if len(command.parents) != 0:
                    continue

                if command in listed:
                    continue

                listed.append(command)

                if command.cog not in command_data:
                    command_data[command.cog] = []

                brief = command.short_doc
                
                if len(brief) > 120:
                    brief = f"{brief[120]}..."

                command_data[command.cog].append(f"- `{name}` -- {brief}")

            except commands.CommandError:
                continue
        
        command_data = dict(sorted(command_data.items(), key=lambda c: "No Category" if c[0] is None else c[0].qualified_name))

        lines = []

        if self.context.bot.description is not None:
            lines.append(f"{self.context.bot.description}\n")
        
        for cog, command_list in command_data.items():
            if cog is None:
                lines.append(f"**No Category:**")
            else:
                lines.append(f"**{cog.qualified_name}:**")
            for cmd in command_list:
                lines.append(cmd)
        
        lines.append("")
        lines.append(self.get_ending_note())
        
        embed = u_interface.gen_embed(
            title = "Bingo-Bot help",
            description = "\n".join(lines)
        )
        await self.context.reply(embed=embed)

    async def send_command_help(
            self: typing.Self,
            command: commands.Command
        ) -> None:
        command_lines = []

        breadcrumbs = []
        for parent in reversed(command.parents):
            breadcrumbs.append(parent.name)
        
        if len(breadcrumbs) != 0:
            breadcrumbs.append(command.name)

            command_lines.append("*{}*".format(" -> ".join(breadcrumbs)))

        ####

        command_name = f"{command.full_parent_name} {command.name}".strip()
        command_lines.append(f"## **{self.context.clean_prefix}{command_name}**")
        command_lines.append(command.description)
        command_lines.append("")

        usage = f"{self.context.clean_prefix}{command_name} {command.signature}".strip()
        command_lines.append(f"Syntax: `{usage}`")
        if len(command.aliases) > 0:
            command_lines.append("Aliases: {}".format(', '.join([f"`{a}`" for a in command.aliases])))

        
        arguments = command.clean_params.values()
        if len(arguments) > 0:
            command_lines.append("\n**Arguments:**")
            for argument in arguments:
                name = argument.displayed_name or argument.name
                description = argument.description or self.default_argument_description
                command_lines.append(f"- `{name}`-- {description}")

        ####
        
        command_lines.append("")
        command_lines.append(self.get_ending_note())
        
        embed = u_interface.gen_embed(
            title = "Bingo-Bot help",
            description = "\n".join(command_lines)
        )
        await self.context.reply(embed=embed)
        
    async def send_group_help(
            self: typing.Self,
            command: commands.Group,
            ctx: commands.Context | CustomContext
        ) -> None:
        command_lines = []

        breadcrumbs = []
        for parent in reversed(command.parents):
            breadcrumbs.append(parent.name)
        
        if len(breadcrumbs) != 0:
            breadcrumbs.append(command.name)

            command_lines.append("*{}*".format(" -> ".join(breadcrumbs)))

        ####

        command_name = f"{command.full_parent_name} {command.name}".strip()
        command_lines.append(f"## **{self.context.clean_prefix}{command_name}**")
        command_lines.append(command.description)
        command_lines.append("")

        usage = f"{self.context.clean_prefix}{command_name} {command.signature}".strip()
        command_lines.append(f"Syntax: `{usage}`")
        if len(command.aliases) > 0:
            command_lines.append("Aliases: {}".format(', '.join([f"`{a}`" for a in command.aliases])))

        
        arguments = command.clean_params.values()
        if len(arguments) > 0:
            command_lines.append("\n**Arguments:**")
            for argument in arguments:
                name = argument.displayed_name or argument.name
                description = argument.description or self.default_argument_description
                command_lines.append(f"- `{name}` -- {description}")

        subcommands = command.commands
        if len(subcommands) > 0:
            command_lines.append("\n**Subcommands:**")

            # Probably a bad way of doing this, but it does prevent the toggle
            # check from sending a message if a subcommand here is disabled.
            old_invoked = ctx.invoked_with
            ctx.invoked_with = "help"
            
            for subcommand in sorted(subcommands, key=lambda c: c.name):
                try:
                    if not await subcommand.can_run(ctx):
                        continue
                except commands.CommandError:
                    continue

                name = subcommand.name
                description = subcommand.short_doc
                command_lines.append(f"- `{name}` -- {description}")

            ctx.invoked_with = old_invoked
        ####
        
        command_lines.append("")
        command_lines.append(self.get_ending_note())
        
        embed = u_interface.gen_embed(
            title = "Bingo-Bot help",
            description = "\n".join(command_lines)
        )
        await self.context.reply(embed=embed)

    async def command_callback(
            self: typing.Self,
            ctx: commands.Context | CustomContext,
            /, *,
            command: typing.Optional[str] = None
        ) -> None:

        bot = ctx.bot

        if command is None:
            return await self.send_bot_help()

        # Check if it's a cog
        cog = bot.get_cog(command)
        if cog is not None:
            return await self.send_cog_help(cog)

        keys = command.split(' ')
        cmd = bot.all_commands.get(keys[0])
        if cmd is None:
            return await self.command_not_found(keys[0])
            

        for key in keys[1:]:
            try:
                found = cmd.all_commands.get(key)  # type: ignore
            except AttributeError:
                return await self.subcommand_not_found(cmd, self.remove_mentions(key))
            else:
                if found is None:
                    return await self.subcommand_not_found(cmd, self.remove_mentions(key))
                cmd = found

        if isinstance(cmd, commands.Group):
            return await self.send_group_help(cmd, ctx)
        else:
            return await self.send_command_help(cmd)
    
    async def on_help_command_error(
            self: typing.Self,
            ctx: commands.Context | CustomContext,
            error: Exception, /
        ) -> None:
        raise error

class BingoError(RuntimeError):
    pass