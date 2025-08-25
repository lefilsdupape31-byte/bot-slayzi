import discord
from discord.ext import commands, tasks
import asyncio
import json
import random
from datetime import datetime, timedelta
import os

# Import du système de permissions
from cogs.perm import has_command_permission

GIVEAWAY_FILE = "giveaways.json"

def load_giveaways():
    if os.path.exists(GIVEAWAY_FILE):
        with open(GIVEAWAY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_giveaways(data):
    with open(GIVEAWAY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.giveaways = load_giveaways()
        self.check_giveaways.start()

    def cog_unload(self):
        self.check_giveaways.cancel()

    @commands.command(name="gw")
    @has_command_permission()  # ⬅ Ajout du check
    async def giveaway_command(self, ctx):
        """Lance un giveaway interactif"""
        questions = [
            "⏳ **Durée du giveaway ?** (exemple: `10m`, `2h`, `1d`)",
            "🎁 **Quel est le lot ?**",
            "🏆 **Combien de gagnants ?** (nombre)"
        ]
        answers = []

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        for question in questions:
            await ctx.send(question)
            try:
                msg = await self.bot.wait_for("message", check=check, timeout=60)
            except asyncio.TimeoutError:
                await ctx.send("⛔ Temps écoulé, giveaway annulé.")
                return
            answers.append(msg.content)

        # Analyse des réponses
        duration_str, prize, winners_count = answers
        winners_count = int(winners_count)

        # Conversion durée en secondes
        time_multiplier = {"m": 60, "h": 3600, "d": 86400}
        duration_seconds = int(duration_str[:-1]) * time_multiplier[duration_str[-1]]

        end_time = datetime.utcnow() + timedelta(seconds=duration_seconds)

        # Création embed
        embed = discord.Embed(
            title="🎉 GIVEAWAY 🎉",
            description=f"**Lot :** {prize}\n"
                        f"**Nombre de gagnants :** {winners_count}\n"
                        f"**Fin :** <t:{int(end_time.timestamp())}:R>\n\n"
                        f"Réagissez avec 🎉 pour participer !",
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Créé par {ctx.author}", icon_url=ctx.author.display_avatar.url)

        giveaway_message = await ctx.send(embed=embed)
        await giveaway_message.add_reaction("🎉")

        # Sauvegarde
        self.giveaways[str(giveaway_message.id)] = {
            "channel_id": ctx.channel.id,
            "prize": prize,
            "winners_count": winners_count,
            "end_time": end_time.timestamp(),
            "guild_id": ctx.guild.id
        }
        save_giveaways(self.giveaways)

        await ctx.send(f"✅ Giveaway lancé pour **{prize}** ! Fin <t:{int(end_time.timestamp())}:R>")

    @tasks.loop(seconds=10)
    async def check_giveaways(self):
        current_time = datetime.utcnow().timestamp()
        to_remove = []

        for msg_id, data in list(self.giveaways.items()):
            if current_time >= data["end_time"]:
                guild = self.bot.get_guild(data["guild_id"])
                channel = guild.get_channel(data["channel_id"])
                try:
                    message = await channel.fetch_message(int(msg_id))
                except:
                    to_remove.append(msg_id)
                    continue

                # Récupération des réactions
                reaction = discord.utils.get(message.reactions, emoji="🎉")
                if not reaction:
                    await channel.send("⛔ Pas assez de participants pour ce giveaway.")
                    to_remove.append(msg_id)
                    continue

                users = [u async for u in reaction.users() if not u.bot]
                if len(users) < data["winners_count"]:
                    await channel.send("⛔ Pas assez de participants pour ce giveaway.")
                    to_remove.append(msg_id)
                    continue

                winners = random.sample(users, data["winners_count"])
                winners_mentions = ", ".join(w.mention for w in winners)

                await channel.send(f"🎉 Félicitations {winners_mentions} ! Vous gagnez **{data['prize']}** 🎁")

                to_remove.append(msg_id)

        # Nettoyage
        for msg_id in to_remove:
            self.giveaways.pop(msg_id, None)
        if to_remove:
            save_giveaways(self.giveaways)

    @check_giveaways.before_loop
    async def before_check_giveaways(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Giveaway(bot))
