import discord
from discord.ext import commands
import json

class Welcome(commands.Cog):
    """Envoi d'un message de bienvenue stylé via embed"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                cfg = json.load(f)

            channel_id = cfg.get("welcome_channel_id")
            if not channel_id:
                return
            channel = member.guild.get_channel(channel_id)
            if not channel:
                return

            embed = discord.Embed(
                title=f"Bienvenue sur {member.guild.name} !",
                description=f"Salut {member.mention} — passe un bon moment ici 🎉",
                color=0x2F3136
            )
            embed.add_field(name="Règles", value="Merci de lire les règles dans #règles", inline=False)
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"ID: {member.id}")
            await channel.send(embed=embed)

        except Exception as e:
            print("Erreur welcome:", e)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
