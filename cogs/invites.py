import discord
from discord.ext import commands
import json
import os
from typing import Optional

INVITES_FILE = "invites.json"

def load_data():
    if os.path.exists(INVITES_FILE):
        try:
            with open(INVITES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_data(data):
    with open(INVITES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

class Invites(commands.Cog):
    """Système complet de gestion des invites"""
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()
        self.invites_cache = {}

    def _ensure_user(self, gid: str, uid: str):
        if gid not in self.data:
            self.data[gid] = {"users": {}, "log_channel": None, "invited_by": {}}
        if "users" not in self.data[gid]:
            self.data[gid]["users"] = {}
        self.data[gid]["users"].setdefault(uid, {"joins": 0, "leaves": 0, "bonus": 0})

    def _calculate_total(self, stats: dict) -> int:
        return stats["joins"] - stats["leaves"] + stats["bonus"]

    async def _update_cache(self, guild: discord.Guild):
        try:
            invites = await guild.invites()
            self.invites_cache[guild.id] = {invite.code: invite.uses for invite in invites}
        except discord.Forbidden:
            self.invites_cache[guild.id] = {}
        except Exception:
            self.invites_cache[guild.id] = {}

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            await self._update_cache(guild)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        before_invites = self.invites_cache.get(guild.id, {})
        await self._update_cache(guild)
        after_invites = self.invites_cache.get(guild.id, {})

        inviter = None
        for code, uses in after_invites.items():
            if uses > before_invites.get(code, 0):
                try:
                    invite_obj = await guild.fetch_invite(code)
                    inviter = invite_obj.inviter
                    break
                except:
                    pass

        gid = str(guild.id)
        self._ensure_user(gid, str(member.id))
        if inviter:
            self._ensure_user(gid, str(inviter.id))
            self.data[gid]["users"][str(inviter.id)]["joins"] += 1
            self.data[gid]["invited_by"][str(member.id)] = str(inviter.id)
        save_data(self.data)

        # log
        log_channel_id = self.data[gid].get("log_channel")
        if log_channel_id:
            channel = guild.get_channel(log_channel_id)
            if channel:
                if inviter:
                    await channel.send(f"{member.mention} a rejoint grâce à {inviter.mention}")
                else:
                    await channel.send(f"{member.mention} a rejoint (inviteur inconnu)")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild = member.guild
        gid = str(guild.id)
        inviter_id = self.data.get(gid, {}).get("invited_by", {}).get(str(member.id))
        if inviter_id:
            self._ensure_user(gid, inviter_id)
            self.data[gid]["users"][inviter_id]["leaves"] += 1
            save_data(self.data)

    @commands.command(name="setinvitelog", help="Définir le salon où seront envoyés les logs d'invitations")
    async def setinvitelog(self, ctx, channel: discord.TextChannel):
        gid = str(ctx.guild.id)
        if gid not in self.data:
            self.data[gid] = {"users": {}, "log_channel": None, "invited_by": {}}
        self.data[gid]["log_channel"] = channel.id
        save_data(self.data)
        await ctx.send(f"Salon de logs des invites défini sur {channel.mention} ✅")

    @commands.command(name="invites", help="Voir vos statistiques d'invitations ou celles d'un membre")
    async def invites(self, ctx, member: Optional[discord.Member] = None):
        member = member or ctx.author
        gid = str(ctx.guild.id)
        self._ensure_user(gid, str(member.id))
        stats = self.data[gid]["users"][str(member.id)]
        total = self._calculate_total(stats)

        embed = discord.Embed(color=discord.Color.blurple())
        embed.set_author(name=f"{member.display_name}", icon_url=member.display_avatar.url)
        if total == 0 and stats["joins"] == 0 and stats["leaves"] == 0 and stats["bonus"] == 0:
            embed.description = "Vous n'avez pas encore invité de membres."
        else:
            embed.description = (
                f"Vous avez actuellement **{total}** invites\n"
                f"(*{stats['joins']} join, {stats['leaves']} leave, {stats['bonus']} bonus*)"
            )
        embed.set_footer(text="+slayzi")
        await ctx.send(embed=embed)

    @commands.command(name="invitesleaderboard", help="Afficher le classement des invitations")
    async def invitesleaderboard(self, ctx):
        gid = str(ctx.guild.id)
        if gid not in self.data or not self.data[gid]["users"]:
            return await ctx.send("Aucune donnée d'invites pour ce serveur.")

        leaderboard = sorted(self.data[gid]["users"].items(), key=lambda x: self._calculate_total(x[1]), reverse=True)
        desc = ""
        for i, (uid, stats) in enumerate(leaderboard[:10], start=1):
            member = ctx.guild.get_member(int(uid))
            name = member.display_name if member else f"Utilisateur quitté ({uid})"
            total = self._calculate_total(stats)
            desc += f"**{i}.** {name} — **{total}** invites\n"

        embed = discord.Embed(title="🏆 Classement des invites", description=desc, color=discord.Color.blurple())
        embed.set_footer(text="+slayzi")
        await ctx.send(embed=embed)

    @commands.command(name="giveinvites", help="Ajouter des invitations bonus à un membre")
    async def giveinvites(self, ctx, member: discord.Member, amount: int):
        gid = str(ctx.guild.id)
        self._ensure_user(gid, str(member.id))
        self.data[gid]["users"][str(member.id)]["bonus"] += amount
        save_data(self.data)
        await ctx.send(f"{amount} invites bonus ajoutées à {member.mention} ✅")

    @commands.command(name="delinvites", help="Retirer des invitations bonus à un membre")
    async def delinvites(self, ctx, member: discord.Member, amount: int):
        gid = str(ctx.guild.id)
        self._ensure_user(gid, str(member.id))
        self.data[gid]["users"][str(member.id)]["bonus"] -= amount
        save_data(self.data)
        await ctx.send(f"{amount} invites bonus retirées à {member.mention} ✅")

    @commands.command(name="resetinvites", help="Réinitialiser les invitations d'un membre ou de tout le serveur")
    async def resetinvites(self, ctx, target: str):
        gid = str(ctx.guild.id)
        if target.lower() == "all":
            self.data[gid]["users"] = {}
            save_data(self.data)
            await ctx.send("Toutes les invites ont été réinitialisées ✅")
        else:
            member = ctx.message.mentions[0] if ctx.message.mentions else None
            if not member:
                return await ctx.send("Veuillez mentionner un membre ou mettre `all`.")
            self._ensure_user(gid, str(member.id))
            self.data[gid]["users"][str(member.id)] = {"joins": 0, "leaves": 0, "bonus": 0}
            save_data(self.data)
            await ctx.send(f"Invites réinitialisées pour {member.mention} ✅")

async def setup(bot):
    await bot.add_cog(Invites(bot))
