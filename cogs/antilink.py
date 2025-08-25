import discord
from discord.ext import commands
import re

class AntiLink(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.antilink_enabled = {}

    @commands.command(name="antilink")
    @commands.has_permissions(manage_messages=True)
    async def toggle_antilink(self, ctx):
        guild_id = ctx.guild.id
        current_state = self.antilink_enabled.get(guild_id, False)
        new_state = not current_state
        self.antilink_enabled[guild_id] = new_state

        print(f"Antilink state: {self.antilink_enabled}")  # Debug

        status = "ON ✅" if new_state else "OFF ❌"
        await ctx.send(f"Antilink {status}")

    @commands.Cog.listener()
    async def on_message(self, message):
        print(f"Message reçu : {message.content}")  # Debug

        if message.author.bot:
            return

        guild_id = message.guild.id if message.guild else None

        if guild_id and self.antilink_enabled.get(guild_id, False):
            # Expression régulière pour détecter tous les liens + discord.gg
            if re.search(r"(https?://|www\\.|discord\\.gg/)", message.content, re.IGNORECASE):
                print("Lien détecté")  # Debug
                try:
                    await message.delete()
                    await message.channel.send(
                        f"{message.author.mention}, les liens ne sont pas autorisés ici. 🚫", delete_after=5
                    )
                except discord.Forbidden:
                    print("Permission manquante pour supprimer un message.")
                except discord.HTTPException:
                    print("Erreur lors de la suppression d'un message.")

        await self.bot.process_commands(message)

async def setup(bot):
    await bot.add_cog(AntiLink(bot))
