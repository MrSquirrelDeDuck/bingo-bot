"""Functions for Discord related things."""

import discord

import utility.text as text

def get_display_name(member):
    return (member.global_name if (member.global_name is not None and member.name == member.display_name) else member.display_name)

async def smart_reply(ctx, content: str, **kwargs) -> discord.Message:
    """Attempts to reply, if there's an error it then tries to send it normally."""

    try:
        return await safe_reply(ctx, content, **kwargs)
    except:
        if kwargs.get("mention_author", True):
            return await safe_send(ctx, f"{ctx.author.mention},\n\n{content}", **kwargs)
        else:
            return await safe_send(ctx, f"{text.ping_filter(get_display_name(ctx.author))},\n\n{content}", **kwargs)

async def safe_reply(ctx, content: str, **kwargs) -> discord.Message:
    """Replies in a safe manner."""
    return await ctx.reply(content, **kwargs, allowed_mentions = discord.AllowedMentions(everyone=False))

async def safe_send(ctx, content: str, **kwargs) -> discord.Message:
    """Sends a message in a safe manner."""
    return await ctx.send(content, **kwargs, allowed_mentions = discord.AllowedMentions(everyone=False))
