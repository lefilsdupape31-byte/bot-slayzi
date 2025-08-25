import discord
from discord.ext import commands
import json
import os

PERM_FILE = "permissions.json"

def load_permissions():
    if os.path.exists(PERM_FILE):
        with open(PERM_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_permissions(data):
    with open(PERM_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def has_command_permission():
    async def predicate(ctx):
        # Admins ont toujours accès
        if ctx.author.guild_permissions.administrator:
            return True

        permissions = load_permissions()
        guild_perms = permissions.get(str(ctx.guild.id), {})

        # Vérifie tous les rôles de l'utilisateur
        for role in ctx.author.roles:
            allowed_cmds = guild_perms.get(str(role.id), [])
            if ctx.command.name in allowed_cmds:
                return True

        # Si aucun rôle n'a la permission
        return False

    return commands.check(predicate)

class Perm(commands.Cog):
    """Gestion des permissions de commandes par rôle"""

    def __init__(self, bot):
        self.bot = bot

        # Application auto du check à toutes les commandes (sauf celles autorisées pour tous)
        @self.bot.check
        async def global_command_check(ctx):
            public_commands = ["help", "ping", "avatar", "meme", "8ball", "userinfo", "serverinfo", "serverpics", "userpic", "invites", "invitesleaderboard"]
  # commandes utilisables par tout le monde
            if ctx.command.name in public_commands:
                return True
            return await has_command_permission().predicate(ctx)

    @commands.command(name="setroleperm")
    @commands.has_permissions(administrator=True)
    async def set_role_perm(self, ctx, role: discord.Role, command_name: str):
        """Autorise un rôle à utiliser une commande"""
        permissions = load_permissions()
        guild_perms = permissions.setdefault(str(ctx.guild.id), {})
        role_perms = guild_perms.setdefault(str(role.id), [])

        if command_name not in [cmd.name for cmd in self.bot.commands]:
            await ctx.send(f"❌ La commande `{command_name}` n'existe pas.")
            return

        if command_name not in role_perms:
            role_perms.append(command_name)
            save_permissions(permissions)
            await ctx.send(f"✅ Le rôle {role.mention} peut maintenant utiliser `+{command_name}`")
        else:
            await ctx.send(f"ℹ Le rôle {role.mention} a déjà accès à `+{command_name}`")

    @commands.command(name="delroleperm")
    @commands.has_permissions(administrator=True)
    async def del_role_perm(self, ctx, role: discord.Role, command_name: str):
        """Retire à un rôle l'accès à une commande"""
        permissions = load_permissions()
        guild_perms = permissions.get(str(ctx.guild.id), {})
        role_perms = guild_perms.get(str(role.id), [])

        if command_name in role_perms:
            role_perms.remove(command_name)
            save_permissions(permissions)
            await ctx.send(f"✅ Le rôle {role.mention} ne peut plus utiliser `+{command_name}`")
        else:
            await ctx.send(f"ℹ Le rôle {role.mention} n'a pas accès à `+{command_name}`")

    @commands.command(name="listroleperms")
    async def list_role_perms(self, ctx, role: discord.Role):
        """Liste les commandes qu'un rôle peut utiliser"""
        permissions = load_permissions()
        guild_perms = permissions.get(str(ctx.guild.id), {})
        role_perms = guild_perms.get(str(role.id), [])

        if role_perms:
            cmds_list = ", ".join(f"+{cmd}" for cmd in role_perms)
            await ctx.send(f"📜 Commandes pour {role.mention} : {cmds_list}")
        else:
            await ctx.send(f"ℹ Le rôle {role.mention} n'a aucune commande autorisée.")

async def setup(bot):
    await bot.add_cog(Perm(bot))
