import discord
from discord.ext import commands
import json
import os
from collections import defaultdict
from datetime import datetime, timedelta

DATA_FILE = "antiabuse.json"

class AntiAbuse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = self.load_data()
        # structure: guild_id -> executor_id -> action_type -> [timestamps]
        self.action_logs = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    # === Gestion fichier de config ===
    def load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"owners": [], "guilds": {}}

    def save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)

    def is_owner(self, user_id: int) -> bool:
        return user_id in self.data.get("owners", [])

    def ensure_guild(self, guild_id: int):
        gid = str(guild_id)
        if gid not in self.data["guilds"]:
            self.data["guilds"][gid] = {
                "whitelist": [],
                "log_channel": None,
                "limits": {
                    "mute": {"count": 3, "seconds": 10},
                    "move": {"count": 5, "seconds": 10},
                    "disconnect": {"count": 3, "seconds": 10},
                    "role_add": {"count": 5, "seconds": 10},
                    "role_remove": {"count": 5, "seconds": 10},
                    "kick": {"count": 3, "seconds": 10},
                    "ban": {"count": 2, "seconds": 10}
                }
            }
            self.save_data()
        return self.data["guilds"][gid]

    def parse_duration(self, duration_str: str):
        try:
            duration_str = duration_str.lower()
            if duration_str.endswith("s"):
                return int(duration_str[:-1])
            elif duration_str.endswith("min"):
                return int(duration_str[:-3]) * 60
            elif duration_str.endswith("h"):
                return int(duration_str[:-1]) * 3600
            else:
                return None
        except:
            return None

    # === Commandes de configuration ===
    @commands.command()
    async def setantiabuse(self, ctx, action_type: str, count: int, duration: str):
        """Configurer le seuil anti-abus : ex: +setantiabuse mute 3 5min"""
        if not self.is_owner(ctx.author.id):
            return await ctx.send("⛔ Vous n'avez pas la permission.")

        valid_types = ["mute", "move", "disconnect", "role_add", "role_remove", "kick", "ban"]
        if action_type not in valid_types:
            return await ctx.send(f"Types valides : {', '.join(valid_types)}")

        duration_seconds = self.parse_duration(duration)
        if duration_seconds is None:
            return await ctx.send("Format de durée invalide. Ex : 10s, 5min, 2h")

        guild_data = self.ensure_guild(ctx.guild.id)
        guild_data["limits"][action_type] = {"count": count, "seconds": duration_seconds}
        self.save_data()
        await ctx.send(f"✅ Limite {action_type} mise à {count} actions sur {duration}")

    @commands.command()
    async def setlogchannel(self, ctx, channel: discord.TextChannel):
        """Définir le salon de logs anti-abus"""
        if not self.is_owner(ctx.author.id):
            return await ctx.send("⛔ Vous n'avez pas la permission.")
        guild_data = self.ensure_guild(ctx.guild.id)
        guild_data["log_channel"] = channel.id
        self.save_data()
        await ctx.send(f"✅ Salon de logs défini sur {channel.mention}")

    # === Gestion whitelist ===
    @commands.group()
    async def whitelist(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Utilisation : +whitelist add/remove @membre")

    @whitelist.command(name="add")
    async def whitelist_add(self, ctx, member: discord.Member):
        if not self.is_owner(ctx.author.id):
            return await ctx.send("⛔ Vous n'avez pas la permission.")
        guild_data = self.ensure_guild(ctx.guild.id)
        if member.id not in guild_data["whitelist"]:
            guild_data["whitelist"].append(member.id)
            self.save_data()
            await ctx.send(f"✅ {member} ajouté à la whitelist.")
        else:
            await ctx.send("⚠️ Ce membre est déjà dans la whitelist.")

    @whitelist.command(name="remove")
    async def whitelist_remove(self, ctx, member: discord.Member):
        if not self.is_owner(ctx.author.id):
            return await ctx.send("⛔ Vous n'avez pas la permission.")
        guild_data = self.ensure_guild(ctx.guild.id)
        if member.id in guild_data["whitelist"]:
            guild_data["whitelist"].remove(member.id)
            self.save_data()
            await ctx.send(f"✅ {member} retiré de la whitelist.")
        else:
            await ctx.send("⚠️ Ce membre n'est pas dans la whitelist.")

    # === Gestion owners globaux ===
    @commands.group()
    async def owner(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Utilisation : +owner add/remove @membre")

    @owner.command(name="add")
    async def owner_add(self, ctx, member: discord.Member):
        if not self.is_owner(ctx.author.id):
            return await ctx.send("⛔ Vous n'avez pas la permission.")
        if member.id not in self.data.get("owners", []):
            self.data.setdefault("owners", []).append(member.id)
            self.save_data()
            await ctx.send(f"✅ {member} ajouté en tant qu'owner global.")
        else:
            await ctx.send("⚠️ Ce membre est déjà owner.")

    @owner.command(name="remove")
    async def owner_remove(self, ctx, member: discord.Member):
        if not self.is_owner(ctx.author.id):
            return await ctx.send("⛔ Vous n'avez pas la permission.")
        if member.id in self.data.get("owners", []):
            self.data["owners"].remove(member.id)
            self.save_data()
            await ctx.send(f"✅ {member} retiré des owners globaux.")
        else:
            await ctx.send("⚠️ Ce membre n'est pas owner.")

    # === Système anti-abuse ===
    def _now_ts(self):
        return int(datetime.utcnow().timestamp())

    async def register_action(self, guild_id: int, executor_id: int, action_type: str, amount: int = 1):
        """Enregistre `amount` actions pour executor_id et vérifie le seuil."""
        guild_data = self.ensure_guild(guild_id)
        now = self._now_ts()
        limit = guild_data["limits"].get(action_type)
        if not limit:
            return

        # prune
        arr = self.action_logs[str(guild_id)][str(executor_id)][action_type]
        cutoff = now - limit["seconds"]
        arr = [t for t in arr if t >= cutoff]
        # add `amount` timestamps (simple approach: same timestamp repeated)
        for _ in range(amount):
            arr.append(now)
        self.action_logs[str(guild_id)][str(executor_id)][action_type] = arr

        if len(arr) >= limit["count"]:
            # reset records to avoid double-sanctioning
            self.action_logs[str(guild_id)][str(executor_id)][action_type] = []
            await self.derank_user(guild_id, executor_id, f"Abus détecté : {action_type} ({len(arr)} >= {limit['count']})")

    async def derank_user(self, guild_id: int, user_id: int, reason: str):
        guild = self.bot.get_guild(int(guild_id))
        if not guild:
            return
        member = guild.get_member(int(user_id))
        guild_data = self.ensure_guild(guild_id)

        # member peut être None si l'exécuteur a quitté; on essaiera de logguer quand même
        if member is None:
            # log only
            if guild_data.get("log_channel"):
                ch = guild.get_channel(guild_data["log_channel"])
                if ch:
                    await ch.send(f"🔨 Un utilisateur (ID {user_id}) aurait dû être derank mais n'est pas présent. Raison: {reason}")
            return

        if member.id in guild_data["whitelist"] or self.is_owner(member.id):
            return

        try:
            roles_to_remove = [r for r in member.roles if r != guild.default_role]
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason=reason)
        except Exception as e:
            print("Erreur derank:", e)

        # Log dans le salon défini
        if guild_data.get("log_channel"):
            channel = guild.get_channel(guild_data["log_channel"])
            if channel:
                embed = discord.Embed(title="🚨 Membre derank", color=discord.Color.red())
                embed.add_field(name="Membre", value=f"{member} ({member.id})", inline=False)
                embed.add_field(name="Raison", value=reason, inline=False)
                embed.timestamp = datetime.utcnow()
                await channel.send(embed=embed)

    # === Événements surveillés ===
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # s'assure que le serveur est configuré
        if not after or not after.guild:
            return
        gid = str(after.guild.id)
        if gid not in self.data.get("guilds", {}):
            return

        # 1) détection timeout (mute via communication_disabled_until)
        before_td = getattr(before, "communication_disabled_until", None)
        after_td = getattr(after, "communication_disabled_until", None)
        if before_td != after_td and after_td is not None:
            executor = None
            try:
                async for entry in after.guild.audit_logs(limit=6, action=discord.AuditLogAction.member_update):
                    if entry.target and getattr(entry.target, "id", None) == after.id:
                        executor = entry.user
                        break
            except Exception:
                executor = None

            if executor and not getattr(executor, "bot", False):
                if not (self.is_owner(executor.id) or self.ensure_guild(after.guild.id).get("whitelist") and str(executor.id) in map(str, self.ensure_guild(after.guild.id).get("whitelist"))):
                    await self.register_action(after.guild.id, executor.id, "mute")

        # 2) détection role add/remove — on compare et on consulte l'audit log pour trouver l'exécuteur
        if before.roles != after.roles:
            before_ids = {r.id for r in before.roles}
            after_ids = {r.id for r in after.roles}
            added = after_ids - before_ids
            removed = before_ids - after_ids

            executor = None
            try:
                async for entry in after.guild.audit_logs(limit=6, action=discord.AuditLogAction.member_role_update):
                    if entry.target and getattr(entry.target, "id", None) == after.id:
                        executor = entry.user
                        break
            except Exception:
                executor = None

            if executor and not getattr(executor, "bot", False):
                gid = str(after.guild.id)
                if self.is_owner(executor.id) or str(executor.id) in map(str, self.ensure_guild(after.guild.id).get("whitelist", [])):
                    return
                if added:
                    # compte par rôle ajouté
                    await self.register_action(after.guild.id, executor.id, "role_add", amount=len(added))
                if removed:
                    await self.register_action(after.guild.id, executor.id, "role_remove", amount=len(removed))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member or not member.guild:
            return
        gid = str(member.guild.id)
        if gid not in self.data.get("guilds", {}):
            return

        if before.channel != after.channel:
            # rechercher l'entrée d'audit pour member_move
            executor = None
            try:
                async for entry in member.guild.audit_logs(limit=6, action=discord.AuditLogAction.member_move):
                    if entry.target and getattr(entry.target, "id", None) == member.id:
                        executor = entry.user
                        break
            except Exception:
                executor = None

            if executor and not getattr(executor, "bot", False):
                if self.is_owner(executor.id) or str(executor.id) in map(str, self.ensure_guild(member.guild.id).get("whitelist", [])):
                    return
                # si déconnect -> after.channel is None
                if before.channel and not after.channel:
                    await self.register_action(member.guild.id, executor.id, "disconnect")
                else:
                    await self.register_action(member.guild.id, executor.id, "move")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        # Kick detection via audit log
        if not member or not member.guild:
            return
        gid = str(member.guild.id)
        if gid not in self.data.get("guilds", {}):
            return

        try:
            async for entry in member.guild.audit_logs(limit=6, action=discord.AuditLogAction.kick):
                if entry.target and getattr(entry.target, "id", None) == member.id:
                    executor = entry.user
                    if executor and not getattr(executor, "bot", False):
                        if not (self.is_owner(executor.id) or str(executor.id) in map(str, self.ensure_guild(member.guild.id).get("whitelist", []))):
                            await self.register_action(member.guild.id, executor.id, "kick")
                    break
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        # Ban detection via audit log
        if not guild:
            return
        gid = str(guild.id)
        if gid not in self.data.get("guilds", {}):
            return

        try:
            async for entry in guild.audit_logs(limit=6, action=discord.AuditLogAction.ban):
                if entry.target and getattr(entry.target, "id", None) == user.id:
                    executor = entry.user
                    if executor and not getattr(executor, "bot", False):
                        if not (self.is_owner(executor.id) or str(executor.id) in map(str, self.ensure_guild(guild.id).get("whitelist", []))):
                            await self.register_action(guild.id, executor.id, "ban")
                    break
        except Exception:
            pass


async def setup(bot):
    await bot.add_cog(AntiAbuse(bot))
