import discord
import random
from discord.ext import commands

class Fun(commands.Cog):
    """Commandes amusantes et divertissantes"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="meme")
    async def meme(self, ctx):
        """Envoie un meme aléatoire"""
        memes = [
            "https://i.imgur.com/3M8F3yF.jpeg",
            "https://i.imgur.com/l0zQXzj.jpeg",
            "https://i.imgur.com/Tv7X6aL.png"
        ]
        await ctx.send(random.choice(memes))

    @commands.command(name="8ball")
    async def eight_ball(self, ctx, *, question: str):
        """Répond à une question par oui/non/maybe"""
        responses = [
            "Oui ✅", "Non ❌", "Peut-être 🤔",
            "Absolument ! 🎉", "Jamais ! 🚫"
        ]
        await ctx.send(f"🎱 **Question :** {question}\n💬 **Réponse :** {random.choice(responses)}")

    @commands.command(name="avatar")
    async def avatar(self, ctx, member: discord.Member = None):
        """Affiche l'avatar d'un membre"""
        member = member or ctx.author
        embed = discord.Embed(title=f"Avatar de {member}", color=0x5865F2)
        embed.set_image(url=member.display_avatar.url)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Fun(bot))
