import discord
from discord.ext import commands
import json

class ReactionRoles(commands.Cog):
    """Cog basique pour reaction roles: configuration via config.json"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="reaction_setup")
    @commands.has_permissions(administrator=True)
    async def reaction_setup(self, ctx, message_id: int):
        """Configure le message (id) qui contient les réactions & map dans config.json"""
        with open("config.json", "r", encoding="utf-8") as f:
            cfg = json.load(f)
        cfg["reaction_role_message_id"] = message_id
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        await ctx.send(f"Message configuré: {message_id}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                cfg = json.load(f)
            if payload.message_id != cfg.get("reaction_role_message_id"):
                return
            guild = self.bot.get_guild(payload.guild_id)
            if not guild:
                return
            emoji = str(payload.emoji)
            mapping = cfg.get("reaction_role_mappings", {})
            role_id = mapping.get(emoji)
            if not role_id:
                return
            role = guild.get_role(role_id)
            member = guild.get_member(payload.user_id)
            if role and member:
                await member.add_roles(role, reason="Reaction role ajouté")
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                cfg = json.load(f)
            if payload.message_id != cfg.get("reaction_role_message_id"):
                return
            guild = self.bot.get_guild(payload.guild_id)
            if not guild:
                return
            emoji = str(payload.emoji)
            mapping = cfg.get("reaction_role_mappings", {})
            role_id = mapping.get(emoji)
            if not role_id:
                return
            role = guild.get_role(role_id)
            member = guild.get_member(payload.user_id)
            if role and member:
                await member.remove_roles(role, reason="Reaction role retiré")
        except Exception:
            pass

async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))
