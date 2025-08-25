import discord
from discord.ext import commands
from discord.ui import View, Select, Button
import asyncio
import json
import os

CONFIG_FILE = "tickets_config.json"

# Chargement ou création du fichier config
if not os.path.exists(CONFIG_FILE):
    default_config = {
        "embed_title": "Support",
        "embed_description": "➜ Voici le salon support !",
        "embed_image": "https://i.pinimg.com/736x/a5/98/ad/a598ad37bfba1b9cd3c7fc1a885ada48.jpg",
        "categories": {},
        "ping_role_id": None
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(default_config, f, indent=4)

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config_data = json.load(f)

# ---------- Bouton Fermer le Ticket ----------
class CloseTicketButton(Button):
    def __init__(self):
        super().__init__(label="Fermer le ticket", style=discord.ButtonStyle.danger, emoji="🔒")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("🔒 Ce ticket sera fermé dans 5 secondes...", ephemeral=True)
        await asyncio.sleep(5)
        await interaction.channel.delete()

# ---------- Menu déroulant ----------
class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=cat, description=desc, emoji=emoji)
            for cat, (desc, emoji) in config_data["categories"].items()
        ]
        super().__init__(placeholder="Choisissez le type de ticket...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        category_name = self.values[0]
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True)
        }

        # Rôle à ping
        role_mention = ""
        if config_data["ping_role_id"]:
            role = guild.get_role(config_data["ping_role_id"])
            if role:
                role_mention = role.mention

        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}".replace(" ", "-"),
            overwrites=overwrites,
            reason=f"Ticket créé par {interaction.user}"
        )

        embed = discord.Embed(
            title=f"{category_name} - Support",
            description=f"{role_mention}\nBonjour {interaction.user.mention}, un membre du staff va vous répondre sous peu.\n\n**Catégorie :** {category_name}",
            color=0xFFFFFF
        )
        await ticket_channel.send(embed=embed, view=discord.ui.View().add_item(CloseTicketButton()))

        await interaction.response.send_message(f"🎫 Votre ticket a été créé : {ticket_channel.mention}", ephemeral=True)

# ---------- Vue principale ----------
class TicketSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

# ---------- Cog principal ----------
class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def setticket(self, ctx):
        embed = discord.Embed(
            title=f"{config_data['embed_title']} {ctx.guild.name} !",
            description=config_data["embed_description"],
            color=0xFFFFFF
        )
        for cat, (desc, emoji) in config_data["categories"].items():
            embed.add_field(name=f"{emoji} {cat}", value=desc, inline=False)
        embed.set_image(url=config_data["embed_image"])
        embed.set_footer(text=f"L'équipe {ctx.guild.name} !")

        view = TicketSelectView()
        await ctx.send(embed=embed, view=view)

    # ---------- Commande pour changer l'embed ----------
    @commands.command()
    async def ticketconfig(self, ctx, field: str, *, value: str):
        """Modifier l'embed ou la config: titre, description, image, pingrole"""
        if field not in ["titre", "description", "image", "pingrole"]:
            return await ctx.send("❌ Champs possibles: titre, description, image, pingrole")

        if field == "titre":
            config_data["embed_title"] = value
        elif field == "description":
            config_data["embed_description"] = value
        elif field == "image":
            config_data["embed_image"] = value
        elif field == "pingrole":
            role = discord.utils.get(ctx.guild.roles, mention=value) or discord.utils.get(ctx.guild.roles, name=value)
            if not role:
                return await ctx.send("❌ Rôle introuvable.")
            config_data["ping_role_id"] = role.id

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)

        await ctx.send(f"✅ `{field}` mis à jour avec succès.")

    # ---------- Commande pour gérer les catégories ----------
    @commands.command()
    async def addticketcat(self, ctx, nom: str, emoji: str, *, description: str):
        """Ajouter une catégorie"""
        config_data["categories"][nom] = [description, emoji]
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)
        await ctx.send(f"✅ Catégorie `{nom}` ajoutée.")

    @commands.command()
    async def removeticketcat(self, ctx, nom: str):
        """Supprimer une catégorie"""
        if nom in config_data["categories"]:
            del config_data["categories"][nom]
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4)
            await ctx.send(f"✅ Catégorie `{nom}` supprimée.")
        else:
            await ctx.send("❌ Catégorie introuvable.")

async def setup(bot):
    await bot.add_cog(TicketCog(bot))
