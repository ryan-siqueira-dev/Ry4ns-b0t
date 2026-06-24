from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from .config import Settings

LOGGER = logging.getLogger(__name__)


class Ry4nsBot(commands.Bot):
    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix=commands.when_mentioned, intents=intents)
        self.settings = settings
        self.guild_scope = (
            discord.Object(id=settings.discord_guild_id)
            if settings.discord_guild_id is not None
            else None
        )

    async def setup_hook(self) -> None:
        register_commands(self)

        if self.guild_scope is not None:
            self.tree.copy_global_to(guild=self.guild_scope)
            synced = await self.tree.sync(guild=self.guild_scope)
            LOGGER.info("Synced %s command(s) to guild %s.", len(synced), self.guild_scope.id)
            return

        synced = await self.tree.sync()
        LOGGER.info("Synced %s global command(s).", len(synced))

    async def on_ready(self) -> None:
        if self.user is None:
            LOGGER.info("Bot is ready.")
            return

        LOGGER.info("Logged in as %s (%s).", self.user, self.user.id)


def create_bot(settings: Settings) -> Ry4nsBot:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    return Ry4nsBot(settings)


def register_commands(bot: Ry4nsBot) -> None:
    @bot.tree.command(name="ping", description="Show the bot latency.")
    async def ping(interaction: discord.Interaction) -> None:
        latency_ms = round(bot.latency * 1000)
        await interaction.response.send_message(f"Pong! `{latency_ms} ms`", ephemeral=True)

    @bot.tree.command(name="server", description="Show information about this server.")
    async def server(interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title=guild.name,
            description="Server information",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="ID", value=str(guild.id), inline=True)
        embed.add_field(name="Members", value=str(guild.member_count or "Unknown"), inline=True)
        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="Created", value=discord.utils.format_dt(guild.created_at, "F"), inline=False)

        if guild.icon is not None:
            embed.set_thumbnail(url=guild.icon.url)

        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="user", description="Show information about a member.")
    @app_commands.describe(member="Member to inspect")
    async def user(interaction: discord.Interaction, member: discord.Member | None = None) -> None:
        target = member or interaction.user
        joined_at = getattr(target, "joined_at", None)

        embed = discord.Embed(
            title=str(target),
            description="User information",
            color=discord.Color.green(),
        )
        embed.add_field(name="ID", value=str(target.id), inline=True)
        embed.add_field(name="Bot", value="Yes" if target.bot else "No", inline=True)
        embed.add_field(name="Created", value=discord.utils.format_dt(target.created_at, "F"), inline=False)

        if joined_at is not None:
            embed.add_field(name="Joined", value=discord.utils.format_dt(joined_at, "F"), inline=False)

        embed.set_thumbnail(url=target.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="avatar", description="Show a member avatar.")
    @app_commands.describe(member="Member whose avatar should be shown")
    async def avatar(interaction: discord.Interaction, member: discord.Member | None = None) -> None:
        target = member or interaction.user
        embed = discord.Embed(
            title=f"{target.display_name}'s avatar",
            color=discord.Color.purple(),
        )
        embed.set_image(url=target.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="clear", description="Delete messages from the current channel.")
    @app_commands.describe(amount="Number of messages to delete, from 1 to 100")
    @app_commands.default_permissions(manage_messages=True)
    async def clear(
        interaction: discord.Interaction,
        amount: app_commands.Range[int, 1, 100],
    ) -> None:
        guild = interaction.guild
        channel = interaction.channel

        if guild is None or channel is None:
            await interaction.response.send_message(
                "This command can only be used in a server channel.",
                ephemeral=True,
            )
            return

        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "Could not verify your server permissions.",
                ephemeral=True,
            )
            return

        if not hasattr(channel, "purge") or not hasattr(channel, "permissions_for"):
            await interaction.response.send_message(
                "This channel does not support message cleanup.",
                ephemeral=True,
            )
            return

        user_permissions = channel.permissions_for(interaction.user)
        if not user_permissions.manage_messages:
            await interaction.response.send_message(
                "You need the Manage Messages permission to use this command.",
                ephemeral=True,
            )
            return

        bot_member = guild.me
        if bot_member is not None:
            bot_permissions = channel.permissions_for(bot_member)
            if not bot_permissions.manage_messages:
                await interaction.response.send_message(
                    "I need the Manage Messages permission in this channel.",
                    ephemeral=True,
                )
                return

        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            deleted = await channel.purge(limit=int(amount))
        except discord.Forbidden:
            await interaction.followup.send(
                "I do not have permission to delete messages here.",
                ephemeral=True,
            )
            return
        except discord.HTTPException as exc:
            LOGGER.exception("Failed to clear messages in channel %s.", getattr(channel, "id", "unknown"))
            await interaction.followup.send(
                f"Discord rejected the cleanup request: {exc.text}",
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            f"Deleted {len(deleted)} message(s).",
            ephemeral=True,
        )
