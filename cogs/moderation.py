import discord
from discord.ext import commands
from .perm import has_command_permission
import json
import os

class Moderation(commands.Cog):
    """Commandes de modération avancées"""
    def __init__(self, bot):
        self.bot = bot
        self.warn_file = "warns.json"
        if not os.path.exists(self.warn_file):
            with open(self.warn_file, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=2)

    def load_warns(self):
        with open(self.warn_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_warns(self, data):
        with open(self.warn_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @commands.command(name="kick", help="+kick @membre raison")
    @has_command_permission()
    async def kick(self, ctx, member: discord.Member, *, reason="Aucune raison fournie"):
        await member.kick(reason=reason)
        await ctx.send(f"👢 {member.mention} a été expulsé. **Raison** : {reason}")

    @commands.command(name="ban", help="+ban @membre raison")
    @has_command_permission()
    async def ban(self, ctx, member: discord.Member, *, reason="Aucune raison fournie"):
        await member.ban(reason=reason)
        await ctx.send(f"🔨 {member.mention} a été banni. **Raison** : {reason}")

    @commands.command(name="softban", help="+softban @membre raison")
    @has_command_permission()
    async def softban(self, ctx, member: discord.Member, *, reason="Aucune raison fournie"):
        await member.ban(reason=reason, delete_message_days=7)
        await member.unban(reason="Softban effectué")
        await ctx.send(f"⚡ {member.mention} a été softban (messages supprimés).")

    @commands.command(name="mute", help="+mute @membre raison")
    @has_command_permission()
    async def mute(self, ctx, member: discord.Member, *, reason="Aucune raison fournie"):
        mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not mute_role:
            mute_role = await ctx.guild.create_role(name="Muted")
            for channel in ctx.guild.channels:
                await channel.set_permissions(mute_role, send_messages=False, speak=False)
        await member.add_roles(mute_role, reason=reason)
        await ctx.send(f"🔇 {member.mention} a été mute. **Raison** : {reason}")

    @commands.command(name="unmute", help="+unmute @membre")
    @has_command_permission()
    async def unmute(self, ctx, member: discord.Member):
        mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if mute_role in member.roles:
            await member.remove_roles(mute_role)
            await ctx.send(f"🔊 {member.mention} a été unmute.")

    @commands.command(name="clear", help="+clear nombre")
    @has_command_permission()
    async def clear(self, ctx, amount: int):
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"🧹 {amount} messages supprimés.", delete_after=5)

    @commands.command(name="lock", help="+lock (verrouille le salon)")
    @has_command_permission()
    async def lock(self, ctx):
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(f"🔒 Salon {ctx.channel.mention} verrouillé.")

    @commands.command(name="unlock", help="+unlock (déverrouille le salon)")
    @has_command_permission()
    async def unlock(self, ctx):
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = True
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(f"🔓 Salon {ctx.channel.mention} déverrouillé.")

    @commands.command(name="warn", help="+warn @membre raison")
    @has_command_permission()
    async def warn(self, ctx, member: discord.Member, *, reason="Aucune raison fournie"):
        warns = self.load_warns()
        warns.setdefault(str(member.id), []).append({"reason": reason, "moderator": ctx.author.id})
        self.save_warns(warns)
        await ctx.send(f"⚠ {member.mention} a reçu un avertissement : **{reason}**")

    @commands.command(name="warns", help="+warns @membre")
    @has_command_permission()
    async def warns(self, ctx, member: discord.Member):
        warns = self.load_warns().get(str(member.id), [])
        if not warns:
            await ctx.send(f"{member.mention} n'a aucun avertissement.")
            return
        embed = discord.Embed(title=f"Avertissements de {member}", color=0xFFA500)
        for i, warn in enumerate(warns, start=1):
            mod = ctx.guild.get_member(warn["moderator"])
            embed.add_field(
                name=f"Avertissement {i}",
                value=f"**Raison** : {warn['reason']}\n**Modérateur** : {mod.mention if mod else 'Inconnu'}",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.command(name="unwarn", help="+unwarn @membre numéro_avertissement")
    @has_command_permission()
    async def unwarn(self, ctx, member: discord.Member, index: int):
        warns = self.load_warns()
        if str(member.id) not in warns or index < 1 or index > len(warns[str(member.id)]):
            await ctx.send("⚠ Index invalide ou aucun avertissement trouvé.")
            return
        removed = warns[str(member.id)].pop(index - 1)
        self.save_warns(warns)
        await ctx.send(f"✅ Avertissement retiré : **{removed['reason']}**")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
