import discord
from discord.ext import commands
from .perm import has_command_permission

class Utils(commands.Cog):
    """Utilitaires"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping")
    @has_command_permission()
    async def ping(self, ctx):
        await ctx.send(embed=discord.Embed(
            title="🏓 Pong",
            description=f"Latence : {round(self.bot.latency * 1000)} ms",
            color=discord.Color.green()
        ))

    @commands.command(name="say")
    @has_command_permission()
    async def say(self, ctx, *, message: str):
        await ctx.message.delete()
        await ctx.send(message)

async def setup(bot):
    await bot.add_cog(Utils(bot))
