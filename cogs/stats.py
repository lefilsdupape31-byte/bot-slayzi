import discord
from discord.ext import commands
from .perm import has_command_permission

class Stats(commands.Cog):
    """Statistiques du serveur"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="stats")
    @has_command_permission()
    async def stats(self, ctx):
        guild = ctx.guild
        embed = discord.Embed(
            title=f"📊 Statistiques de {guild.name}",
            color=discord.Color.blue()
        )
        embed.add_field(name="👥 Membres", value=guild.member_count)
        embed.add_field(name="📅 Créé le", value=guild.created_at.strftime("%d/%m/%Y"))
        embed.add_field(name="🛡 Rôles", value=len(guild.roles))
        embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Stats(bot))
