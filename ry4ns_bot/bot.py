from __future__ import annotations

import logging
import random
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands

from .config import Settings
from .entertainment import ChoiceParseError, parse_choice_options

LOGGER = logging.getLogger(__name__)
EIGHT_BALL_RESPONSES = (
    "It is certain.",
    "Most likely.",
    "Ask again later.",
    "Cannot predict now.",
    "Do not count on it.",
    "My reply is no.",
    "Outlook good.",
    "Very doubtful.",
)


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


def _clean_reason(reason: str | None) -> str | None:
    if reason is None:
        return None

    cleaned = reason.strip()
    return cleaned or None


def _member_can_act_on(actor: discord.Member, target: discord.Member) -> bool:
    guild = actor.guild
    if actor.id == guild.owner_id:
        return True

    if target.id == guild.owner_id:
        return False

    return actor.top_role > target.top_role


def _bot_can_act_on(guild: discord.Guild, target: discord.Member) -> bool:
    bot_member = guild.me
    if bot_member is None or target.id == guild.owner_id:
        return False

    return bot_member.top_role > target.top_role


async def _ensure_moderation_allowed(
    interaction: discord.Interaction,
    target: discord.Member,
    permission_name: str,
    permission_label: str,
) -> bool:
    guild = interaction.guild

    if guild is None:
        await interaction.response.send_message(
            "This command can only be used in a server.",
            ephemeral=True,
        )
        return False

    if not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message(
            "Could not verify your server permissions.",
            ephemeral=True,
        )
        return False

    if not getattr(interaction.user.guild_permissions, permission_name, False):
        await interaction.response.send_message(
            f"You need the {permission_label} permission to use this command.",
            ephemeral=True,
        )
        return False

    if target.id == interaction.user.id:
        await interaction.response.send_message(
            "You cannot moderate yourself.",
            ephemeral=True,
        )
        return False

    if guild.me is not None and target.id == guild.me.id:
        await interaction.response.send_message(
            "I cannot moderate myself.",
            ephemeral=True,
        )
        return False

    bot_member = guild.me
    if bot_member is None:
        await interaction.response.send_message(
            "Could not verify my server permissions.",
            ephemeral=True,
        )
        return False

    if not getattr(bot_member.guild_permissions, permission_name, False):
        await interaction.response.send_message(
            f"I need the {permission_label} permission to use this command.",
            ephemeral=True,
        )
        return False

    if not _member_can_act_on(interaction.user, target):
        await interaction.response.send_message(
            "You cannot moderate a member with an equal or higher role.",
            ephemeral=True,
        )
        return False

    if not _bot_can_act_on(guild, target):
        await interaction.response.send_message(
            "I cannot moderate a member with an equal or higher role than mine.",
            ephemeral=True,
        )
        return False

    return True


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

    @bot.tree.command(name="timeout", description="Temporarily mute a member.")
    @app_commands.describe(
        member="Member to timeout",
        duration_minutes="Timeout duration in minutes, from 1 to 40320",
        reason="Optional reason for the audit log",
    )
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.guild_only()
    async def timeout(
        interaction: discord.Interaction,
        member: discord.Member,
        duration_minutes: app_commands.Range[int, 1, 40320],
        reason: str | None = None,
    ) -> None:
        if not await _ensure_moderation_allowed(
            interaction,
            member,
            "moderate_members",
            "Moderate Members",
        ):
            return

        until = discord.utils.utcnow() + timedelta(minutes=int(duration_minutes))

        try:
            await member.timeout(until, reason=_clean_reason(reason))
        except discord.Forbidden:
            await interaction.response.send_message(
                "I do not have permission to timeout this member.",
                ephemeral=True,
            )
            return
        except discord.HTTPException as exc:
            LOGGER.exception("Failed to timeout member %s.", member.id)
            await interaction.response.send_message(
                f"Discord rejected the timeout request: {exc.text}",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"Timed out {member.mention} for {int(duration_minutes)} minute(s).",
            ephemeral=True,
        )

    @bot.tree.command(name="untimeout", description="Remove a member timeout.")
    @app_commands.describe(
        member="Member whose timeout should be removed",
        reason="Optional reason for the audit log",
    )
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.guild_only()
    async def untimeout(
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str | None = None,
    ) -> None:
        if not await _ensure_moderation_allowed(
            interaction,
            member,
            "moderate_members",
            "Moderate Members",
        ):
            return

        try:
            await member.timeout(None, reason=_clean_reason(reason))
        except discord.Forbidden:
            await interaction.response.send_message(
                "I do not have permission to remove this timeout.",
                ephemeral=True,
            )
            return
        except discord.HTTPException as exc:
            LOGGER.exception("Failed to remove timeout from member %s.", member.id)
            await interaction.response.send_message(
                f"Discord rejected the untimeout request: {exc.text}",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"Removed timeout from {member.mention}.",
            ephemeral=True,
        )

    @bot.tree.command(name="kick", description="Kick a member from the server.")
    @app_commands.describe(
        member="Member to kick",
        reason="Optional reason for the audit log",
    )
    @app_commands.default_permissions(kick_members=True)
    @app_commands.guild_only()
    async def kick(
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str | None = None,
    ) -> None:
        if not await _ensure_moderation_allowed(
            interaction,
            member,
            "kick_members",
            "Kick Members",
        ):
            return

        try:
            await member.kick(reason=_clean_reason(reason))
        except discord.Forbidden:
            await interaction.response.send_message(
                "I do not have permission to kick this member.",
                ephemeral=True,
            )
            return
        except discord.HTTPException as exc:
            LOGGER.exception("Failed to kick member %s.", member.id)
            await interaction.response.send_message(
                f"Discord rejected the kick request: {exc.text}",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"Kicked {member.mention}.",
            ephemeral=True,
        )

    @bot.tree.command(name="ban", description="Ban a member from the server.")
    @app_commands.describe(
        member="Member to ban",
        delete_message_days="Delete this many days of message history, from 0 to 7",
        reason="Optional reason for the audit log",
    )
    @app_commands.default_permissions(ban_members=True)
    @app_commands.guild_only()
    async def ban(
        interaction: discord.Interaction,
        member: discord.Member,
        delete_message_days: app_commands.Range[int, 0, 7] = 0,
        reason: str | None = None,
    ) -> None:
        if not await _ensure_moderation_allowed(
            interaction,
            member,
            "ban_members",
            "Ban Members",
        ):
            return

        try:
            await member.ban(
                reason=_clean_reason(reason),
                delete_message_seconds=int(delete_message_days) * 24 * 60 * 60,
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "I do not have permission to ban this member.",
                ephemeral=True,
            )
            return
        except discord.HTTPException as exc:
            LOGGER.exception("Failed to ban member %s.", member.id)
            await interaction.response.send_message(
                f"Discord rejected the ban request: {exc.text}",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"Banned {member.mention}.",
            ephemeral=True,
        )

    @bot.tree.command(name="slowmode", description="Set slowmode in the current text channel.")
    @app_commands.describe(seconds="Slowmode delay in seconds, from 0 to 21600")
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.guild_only()
    async def slowmode(
        interaction: discord.Interaction,
        seconds: app_commands.Range[int, 0, 21600],
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

        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "This command can only be used in a text channel.",
                ephemeral=True,
            )
            return

        user_permissions = channel.permissions_for(interaction.user)
        if not user_permissions.manage_channels:
            await interaction.response.send_message(
                "You need the Manage Channels permission to use this command.",
                ephemeral=True,
            )
            return

        bot_member = guild.me
        if bot_member is not None:
            bot_permissions = channel.permissions_for(bot_member)
            if not bot_permissions.manage_channels:
                await interaction.response.send_message(
                    "I need the Manage Channels permission in this channel.",
                    ephemeral=True,
                )
                return

        try:
            await channel.edit(slowmode_delay=int(seconds))
        except discord.Forbidden:
            await interaction.response.send_message(
                "I do not have permission to edit this channel.",
                ephemeral=True,
            )
            return
        except discord.HTTPException as exc:
            LOGGER.exception("Failed to set slowmode in channel %s.", channel.id)
            await interaction.response.send_message(
                f"Discord rejected the slowmode request: {exc.text}",
                ephemeral=True,
            )
            return

        if int(seconds) == 0:
            message = "Slowmode disabled in this channel."
        else:
            message = f"Slowmode set to {int(seconds)} second(s)."

        await interaction.response.send_message(message, ephemeral=True)

    @bot.tree.command(name="coinflip", description="Flip a coin.")
    async def coinflip(interaction: discord.Interaction) -> None:
        await interaction.response.send_message(random.choice(("Heads", "Tails")))

    @bot.tree.command(name="roll", description="Roll a die.")
    @app_commands.describe(sides="Number of sides, from 2 to 1000")
    async def roll(
        interaction: discord.Interaction,
        sides: app_commands.Range[int, 2, 1000] = 6,
    ) -> None:
        result = random.randint(1, int(sides))
        await interaction.response.send_message(f"Rolled **{result}** on a d{int(sides)}.")

    @bot.tree.command(name="choose", description="Choose one option from a comma-separated list.")
    @app_commands.describe(options="Options separated by commas, like pizza, sushi, burger")
    async def choose(interaction: discord.Interaction, options: str) -> None:
        try:
            parsed_options = parse_choice_options(options)
        except ChoiceParseError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return

        choice = random.choice(parsed_options)
        await interaction.response.send_message(
            f"I choose: **{choice}**",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @bot.tree.command(name="8ball", description="Ask the magic 8-ball a question.")
    @app_commands.describe(question="Question to ask")
    async def eightball(interaction: discord.Interaction, question: str) -> None:
        await interaction.response.send_message(
            f"Question: {question}\nAnswer: **{random.choice(EIGHT_BALL_RESPONSES)}**",
            allowed_mentions=discord.AllowedMentions.none(),
        )
