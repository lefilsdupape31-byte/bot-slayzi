import discord
from discord.ext import commands
import re

class AntiLink(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.antilink_enabled = set()  # Garde les guildes avec antilink activé

    @commands.command(name="antilink")
    @commands.has_permissions(manage_messages=True)
    async def toggle_antilink(self, ctx):
        guild_id = ctx.guild.id
        if guild_id in self.antilink_enabled:
            self.antilink_enabled.remove(guild_id)
            await ctx.send("Antilink OFF ❌")
        else:
            self.antilink_enabled.add(guild_id)
            await ctx.send("Antilink ON ✅")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        if not message.guild:
            return

        if message.guild.id not in self.antilink_enabled:
            return

        # Detecte un lien http(s):// ou www. ou discord.gg/
        if re.search(r"(https?://|www\.|discord\.gg/)", message.content, re.IGNORECASE):
            try:
                await message.delete()
                await message.channel.send(f"{message.author.mention} Les liens sont interdits ici !", delete_after=5)
            except discord.Forbidden:
                print("Je n'ai pas la permission de supprimer ce message.")
            except discord.HTTPException:
                print("Erreur lors de la suppression du message.")

    async def cog_load(self):
        print("AntiLink cog chargé")

async def setup(bot):
    await bot.add_cog(AntiLink(bot))
