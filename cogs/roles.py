import discord
from discord.ext import commands
from .perm import has_command_permission

class Roles(commands.Cog):
    """Gestion simple des rôles (avec vérification de hiérarchie)"""

    def __init__(self, bot):
        self.bot = bot

    def can_manage_role(self, ctx, role: discord.Role) -> bool:
        """Vérifie que le rôle est gérable par le bot et par l'auteur."""
        bot_top_role = ctx.guild.me.top_role
        author_top_role = ctx.author.top_role

        # Empêche de gérer un rôle égal ou supérieur au bot
        if role >= bot_top_role:
            return False

        # Empêche de gérer un rôle égal ou supérieur à l'auteur
        if role >= author_top_role:
            return False

        return True

    @commands.command(name="addrole")
    @has_command_permission()
    async def addrole(self, ctx, member: discord.Member, *, role_name: str):
        """Ajoute un rôle à un utilisateur (crée le rôle si inexistant)"""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            # Crée le rôle seulement si le bot peut le gérer
            role = await ctx.guild.create_role(name=role_name)
            await ctx.send(f"✅ Rôle `{role_name}` créé.")

        if not self.can_manage_role(ctx, role):
            await ctx.send(f"⛔ Impossible de gérer le rôle `{role.name}` (hiérarchie).")
            return

        if role in member.roles:
            await ctx.send(f"ℹ {member.mention} a déjà le rôle `{role.name}`.")
            return

        await member.add_roles(role, reason=f"Ajout par {ctx.author}")
        await ctx.send(f"✅ Rôle `{role.name}` ajouté à {member.mention}.")

    @commands.command(name="delrole")
    @has_command_permission()
    async def delrole(self, ctx, member: discord.Member, *, role_name: str):
        """Retire un rôle à un utilisateur"""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            await ctx.send(f"❌ Le rôle `{role_name}` n'existe pas.")
            return

        if not self.can_manage_role(ctx, role):
            await ctx.send(f"⛔ Impossible de gérer le rôle `{role.name}` (hiérarchie).")
            return

        if role not in member.roles:
            await ctx.send(f"ℹ {member.mention} n'a pas le rôle `{role.name}`.")
            return

        await member.remove_roles(role, reason=f"Retrait par {ctx.author}")
        await ctx.send(f"✅ Rôle `{role.name}` retiré à {member.mention}.")

async def setup(bot):
    await bot.add_cog(Roles(bot))
