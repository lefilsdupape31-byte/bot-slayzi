import discord
from discord.ext import commands

class Gestion(commands.Cog):
    """Commandes de gestion du serveur"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="slowmode")
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, secondes: int = 0):
        """Active ou désactive le slowmode dans un salon"""
        if secondes < 0 or secondes > 21600:
            await ctx.send("❌ Le slowmode doit être entre **0** et **21600 secondes**.")
            return
        await ctx.channel.edit(slowmode_delay=secondes)
        if secondes == 0:
            await ctx.send("⏱ Slowmode désactivé.")
        else:
            await ctx.send(f"⏱ Slowmode activé : {secondes} secondes.")

async def setup(bot):
    await bot.add_cog(Gestion(bot))
