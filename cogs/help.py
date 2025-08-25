import discord
from discord.ext import commands
from discord.ui import View, Select
import json
import os
import traceback

PERM_FILE = "permissions.json"

ICON_URL = "https://cdn.discordapp.com/attachments/1403563379775373343/1403816227020734464/5e65ec2cd1adaac9810e2c664ba213ad.jpg?ex=6898ed3e&is=68979bbe&hm=34bd9516c032b23a6d3b226338f750e1c5a2e62b7d055b035da13e8dd18ba8fa&"
MAIN_IMAGE_URL = "https://i.pinimg.com/736x/a5/98/ad/a598ad37bfba1b9cd3c7fc1a885ada48.jpg"

PUBLIC_CATEGORIES = ["Fun", "Info"]  # toujours visibles pour tous

def load_permissions():
    if os.path.exists(PERM_FILE):
        try:
            with open(PERM_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def member_has_permission(member: discord.Member, guild: discord.Guild, command) -> bool:
    if guild is None:
        return False
    if command.name == "help":
        return True
    if command.cog_name in PUBLIC_CATEGORIES:
        return True
    m = member
    if not isinstance(member, discord.Member):
        m = guild.get_member(member.id) or member
    try:
        if m.guild_permissions.administrator:
            return True
    except Exception:
        pass
    perms = load_permissions()
    guild_perms = perms.get(str(guild.id), {})
    for role in m.roles:
        role_perms = guild_perms.get(str(role.id), [])
        if command.name in role_perms:
            return True
    return False


class HelpSelect(Select):
    def __init__(self, bot, ctx):
        self.bot = bot
        self.ctx = ctx
        super().__init__(placeholder="📂 Sélectionne une catégorie", options=[])

    async def update_options(self):
        options = []
        for cog_name, cog in self.bot.cogs.items():
            cmds = [cmd for cmd in cog.get_commands() if not cmd.hidden]
            if cog_name in PUBLIC_CATEGORIES:
                options.append(discord.SelectOption(
                    label=cog_name,
                    description=(cog.__doc__ or "Aucune description.")[:100],
                    value=cog_name
                ))
                continue
            visible_for_author = False
            for cmd in cmds:
                if member_has_permission(self.ctx.author, self.ctx.guild, cmd):
                    visible_for_author = True
                    break
            if visible_for_author:
                options.append(discord.SelectOption(
                    label=cog_name,
                    description=(cog.__doc__ or "Aucune description.")[:100],
                    value=cog_name
                ))
        self.options = options

    async def callback(self, interaction: discord.Interaction):
        cog_name = self.values[0]
        cog = self.bot.get_cog(cog_name)
        embed = discord.Embed(
            title=f"⚒ Commandes {cog_name}",
            description="Voici la liste des commandes disponibles pour vous.",
            color=discord.Color(0xFFFFFF)  # Blanc pur
        )
        embed.set_thumbnail(url=ICON_URL)
        embed.set_image(url=MAIN_IMAGE_URL)
        description = ""
        guild = interaction.guild
        member = interaction.user
        for command in cog.get_commands():
            if command.hidden:
                continue
            try:
                if member_has_permission(member, guild, command):
                    description += f"`+{command.name}` — {command.help or 'Pas de description'}\n"
            except Exception:
                continue
        embed.description += "\n\n" + (description or "Aucune commande disponible.")
        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(View):
    def __init__(self, bot, ctx):
        super().__init__(timeout=None)
        self.select = HelpSelect(bot, ctx)
        self.add_item(self.select)

    async def prepare(self):
        await self.select.update_options()


class Help(commands.Cog):
    """Affiche toutes les commandes du bot"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx):
        try:
            first_cog_name = None
            for cog_name, cog in self.bot.cogs.items():
                if cog_name in PUBLIC_CATEGORIES:
                    first_cog_name = cog_name
                    break
                for cmd in cog.get_commands():
                    if cmd.hidden:
                        continue
                    if member_has_permission(ctx.author, ctx.guild, cmd):
                        first_cog_name = cog_name
                        break
                if first_cog_name:
                    break

            if not first_cog_name:
                return await ctx.send("❌ Tu n'as accès à aucune commande.")

            cog = self.bot.get_cog(first_cog_name)
            embed = discord.Embed(
                title=f"⚒ Commandes {first_cog_name}",
                description="Voici la liste des commandes disponibles pour vous.",
                color=discord.Color(0xFFFFFF)  # Blanc pur
            )
            embed.set_thumbnail(url=ICON_URL)
            embed.set_image(url=MAIN_IMAGE_URL)
            description = ""
            for command in cog.get_commands():
                if command.hidden:
                    continue
                if member_has_permission(ctx.author, ctx.guild, command):
                    description += f"`+{command.name}` — {command.help or 'Pas de description'}\n"
            embed.description += "\n\n" + (description or "Aucune commande disponible.")
            view = HelpView(self.bot, ctx)
            await view.prepare()
            await ctx.send(embed=embed, view=view)

        except Exception as e:
            tb = traceback.format_exc()
            await ctx.send(f"❌ Une erreur est survenue : `{e}`\n```py\n{tb}\n```")
            raise


async def setup(bot):
    await bot.add_cog(Help(bot))
