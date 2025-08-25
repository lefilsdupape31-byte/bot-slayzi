import discord
from discord.ext import commands
import os
import asyncio
import json

# Charger la config (pour le préfixe seulement)
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

# Récupérer le token depuis la variable d'environnement
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

if TOKEN is None:
    print("Erreur : la variable d'environnement DISCORD_BOT_TOKEN n'est pas définie.")
    exit(1)

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Création du bot, on récupère le préfixe dans config.json toujours (ou tu peux le remplacer aussi par une variable d'environnement)
bot = commands.Bot(
    command_prefix=config.get("prefix", "+"),
    help_command=None,
    intents=intents
)

# Chargement des cogs
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and filename != "__init__.py":
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"✅ Cog chargé: {filename}")
            except Exception as e:
                print(f"❌ Erreur lors du chargement du cog {filename}: {e}")

@bot.event
async def on_ready():
    print(f"{bot.user} est connecté ✅")

# Lancement
async def main():
    await load_cogs()
    async with bot:
        await bot.start(TOKEN)

asyncio.run(main())
