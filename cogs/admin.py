import discord
from discord.ext import commands
import os

class Admin(commands.Cog):
    """Commandes d'administration pour gérer les Cogs"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def load(self, ctx, extension):
        """Charge un cog"""
        try:
            await self.bot.load_extension(f"cogs.{extension}")
            await ctx.send(embed=discord.Embed(
                title="✅ Cog chargé",
                description=f"Le cog `{extension}` a été chargé avec succès.",
                color=discord.Color.green()
            ))
        except Exception as e:
            await ctx.send(embed=discord.Embed(
                title="❌ Erreur de chargement",
                description=f"Impossible de charger `{extension}`\n```{e}```",
                color=discord.Color.red()
            ))

    @commands.command()
    @commands.is_owner()
    async def unload(self, ctx, extension):
        """Décharge un cog"""
        try:
            await self.bot.unload_extension(f"cogs.{extension}")
            await ctx.send(embed=discord.Embed(
                title="✅ Cog déchargé",
                description=f"Le cog `{extension}` a été déchargé avec succès.",
                color=discord.Color.orange()
            ))
        except Exception as e:
            await ctx.send(embed=discord.Embed(
                title="❌ Erreur de déchargement",
                description=f"Impossible de décharger `{extension}`\n```{e}```",
                color=discord.Color.red()
            ))

    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx, extension):
        """Recharge un cog"""
        try:
            await self.bot.reload_extension(f"cogs.{extension}")
            await ctx.send(embed=discord.Embed(
                title="♻️ Cog rechargé",
                description=f"Le cog `{extension}` a été rechargé avec succès.",
                color=discord.Color.blue()
            ))
        except Exception as e:
            await ctx.send(embed=discord.Embed(
                title="❌ Erreur de rechargement",
                description=f"Impossible de recharger `{extension}`\n```{e}```",
                color=discord.Color.red()
            ))

    @commands.command()
    @commands.is_owner()
    async def reloadall(self, ctx):
        """Recharge tous les cogs"""
        success = []
        failed = []
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                name = filename[:-3]
                try:
                    await self.bot.reload_extension(f"cogs.{name}")
                    success.append(name)
                except Exception as e:
                    failed.append(f"{name} ({e})")

        embed = discord.Embed(title="♻️ Résultat du rechargement", color=discord.Color.blurple())
        if success:
            embed.add_field(name="✅ Rechargés", value=", ".join(success), inline=False)
        if failed:
            embed.add_field(name="❌ Échecs", value="\n".join(failed), inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Admin(bot))
