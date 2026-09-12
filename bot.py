"""
Reaction Roles Bot
------------------
Members give themselves a role by reacting to a message, and lose it
when they remove the reaction.

Mappings are stored in a JSON file, so they survive a restart.
"""

import json
import os
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
DATA_FILE = Path("reaction_roles.json")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# --------------------------------------------------------------------
# Storage
# --------------------------------------------------------------------

def load_mappings() -> dict:
    """Return {message_id: {emoji: role_id}}. Empty dict if no file yet."""
    if not DATA_FILE.exists():
        return {}
    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        # A corrupt file should not stop the bot from starting.
        return {}


def save_mappings(mappings: dict) -> None:
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(mappings, f, indent=2)


def emoji_key(emoji: discord.PartialEmoji) -> str:
    """
    Build a stable key for both custom and unicode emoji.
    Custom emoji are identified by ID, unicode emoji by the character.
    """
    return str(emoji.id) if emoji.id else emoji.name


# --------------------------------------------------------------------
# Role assignment
# --------------------------------------------------------------------

async def update_role(payload: discord.RawReactionActionEvent, add: bool) -> None:
    mappings = load_mappings()
    entry = mappings.get(str(payload.message_id))
    if not entry:
        return

    role_id = entry.get(emoji_key(payload.emoji))
    if role_id is None:
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return

    role = guild.get_role(role_id)
    if role is None:
        return

    # The bot can only manage roles below its own highest role.
    if role >= guild.me.top_role:
        return

    try:
        member = payload.member or await guild.fetch_member(payload.user_id)
    except discord.HTTPException:
        return

    if member.bot:
        return

    try:
        if add:
            await member.add_roles(role, reason="Reaction role")
        else:
            await member.remove_roles(role, reason="Reaction role")
    except discord.Forbidden:
        # Missing permissions. Nothing to do but ignore this reaction.
        pass


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent) -> None:
    if payload.guild_id:
        await update_role(payload, add=True)


@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent) -> None:
    if payload.guild_id:
        await update_role(payload, add=False)


# --------------------------------------------------------------------
# Slash commands
# --------------------------------------------------------------------

group = app_commands.Group(
    name="reactionrole",
    description="Manage reaction roles",
    default_permissions=discord.Permissions(manage_roles=True),
)


@group.command(name="add", description="Link an emoji on a message to a role")
@app_commands.describe(
    message_id="ID of the message members will react to",
    emoji="The emoji to react with",
    role="The role to give",
)
async def add_mapping(
    interaction: discord.Interaction,
    message_id: str,
    emoji: str,
    role: discord.Role,
) -> None:
    if not message_id.isdigit():
        await interaction.response.send_message(
            "That message ID is not a number. Enable Developer Mode, "
            "right-click the message and choose Copy Message ID.",
            ephemeral=True,
        )
        return

    if role >= interaction.guild.me.top_role:
        await interaction.response.send_message(
            f"I cannot assign **{role.name}** because it sits above my own "
            "highest role. Move my role higher in Server Settings.",
            ephemeral=True,
        )
        return

    try:
        partial = discord.PartialEmoji.from_str(emoji)
    except Exception:
        await interaction.response.send_message(
            "I could not read that emoji.", ephemeral=True
        )
        return

    mappings = load_mappings()
    mappings.setdefault(message_id, {})[emoji_key(partial)] = role.id
    save_mappings(mappings)

    await interaction.response.send_message(
        f"Done. Reacting with {emoji} now gives **{role.name}**.\n"
        "Add that reaction to the message yourself so members can click it.",
        ephemeral=True,
    )


@group.command(name="remove", description="Unlink an emoji from a role")
@app_commands.describe(message_id="ID of the message", emoji="The emoji to unlink")
async def remove_mapping(
    interaction: discord.Interaction, message_id: str, emoji: str
) -> None:
    mappings = load_mappings()
    entry = mappings.get(message_id)
    partial = discord.PartialEmoji.from_str(emoji)

    if not entry or emoji_key(partial) not in entry:
        await interaction.response.send_message(
            "There is no reaction role set up for that emoji.", ephemeral=True
        )
        return

    del entry[emoji_key(partial)]
    if not entry:
        del mappings[message_id]
    save_mappings(mappings)

    await interaction.response.send_message("Removed.", ephemeral=True)


@group.command(name="list", description="Show all reaction roles on this server")
async def list_mappings(interaction: discord.Interaction) -> None:
    mappings = load_mappings()
    if not mappings:
        await interaction.response.send_message(
            "No reaction roles set up yet.", ephemeral=True
        )
        return

    lines = []
    for message_id, entry in mappings.items():
        for key, role_id in entry.items():
            role = interaction.guild.get_role(role_id)
            if role:
                lines.append(f"Message `{message_id}` - {key} gives **{role.name}**")

    text = "\n".join(lines) if lines else "No reaction roles on this server."
    await interaction.response.send_message(text, ephemeral=True)


bot.tree.add_command(group)


# --------------------------------------------------------------------
# Startup
# --------------------------------------------------------------------

@bot.event
async def on_ready() -> None:
    await bot.tree.sync()
    print(f"Logged in as {bot.user} - slash commands synced")


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit(
            "No token found. Copy .env.example to .env and put your bot token in it."
        )
    bot.run(TOKEN)
