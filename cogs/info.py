import discord
from discord.ext import commands
from datetime import datetime

class Info(commands.Cog):
    """Commandes d'informations"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="userinfo", help="Infos d'un membre")
    async def userinfo(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        embed = discord.Embed(
            title=f"ℹ Infos sur {member.display_name}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="ID", value=member.id)
        embed.add_field(name="Pseudo", value=member.name)
        embed.add_field(name="Compte créé le", value=member.created_at.strftime("%d/%m/%Y"), inline=False)
        embed.add_field(name="Rejoint le", value=member.joined_at.strftime("%d/%m/%Y"), inline=False)
        embed.add_field(name="Rôles", value=", ".join([role.mention for role in member.roles if role != ctx.guild.default_role]), inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="serverinfo", help="Infos du serveur")
    async def serverinfo(self, ctx):
        guild = ctx.guild
        embed = discord.Embed(
            title=f"ℹ Infos sur {guild.name}",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)
        embed.add_field(name="Propriétaire", value=guild.owner.mention)
        embed.add_field(name="ID", value=guild.id)
        embed.add_field(name="Membres", value=guild.member_count)
        embed.add_field(name="Créé le", value=guild.created_at.strftime("%d/%m/%Y"), inline=False)
        embed.add_field(name="Niveau de boost", value=guild.premium_tier)
        embed.add_field(name="Nombre de boosts", value=guild.premium_subscription_count)
        await ctx.send(embed=embed)

    @commands.command(name="serverpic", help="Image du serveur")
    async def serverpic(self, ctx):
        if ctx.guild.icon:
            await ctx.send(ctx.guild.icon.url)
        else:
            await ctx.send("❌ Ce serveur n'a pas d'icône.")

    @commands.command(name="userpic", help="Avatar d'un membre")
    async def userpic(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        await ctx.send(member.display_avatar.url)

async def setup(bot):
    await bot.add_cog(Info(bot))
