import discord
from discord.ext import commands

class Logs(commands.Cog):
    """Cog qui gère les logs messages et vocaux"""

    def __init__(self, bot):
        self.bot = bot
        self.log_messages_channel_id = None
        self.log_vocals_channel_id = None

    # ===================== CONFIGURATION DES SALONS =====================

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def logmessages(self, ctx):
        """Définit ce salon comme salon de logs messages"""
        self.log_messages_channel_id = ctx.channel.id
        await ctx.send(embed=discord.Embed(
            description=f"✅ Salon de logs **messages** défini sur {ctx.channel.mention}",
            color=discord.Color.green()
        ))

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def logvocals(self, ctx):
        """Définit ce salon comme salon de logs vocaux"""
        self.log_vocals_channel_id = ctx.channel.id
        await ctx.send(embed=discord.Embed(
            description=f"✅ Salon de logs **vocaux** défini sur {ctx.channel.mention}",
            color=discord.Color.green()
        ))

    # ===================== LOGS MESSAGES =====================

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        if not self.log_messages_channel_id:
            return
        
        log_channel = self.bot.get_channel(self.log_messages_channel_id)
        if not log_channel:
            return

        embed = discord.Embed(
            description=f"**Message supprimé dans {message.channel.mention}**\n{message.content or '*[Pièce jointe]*'}",
            color=discord.Color.orange()
        )
        embed.set_author(name=message.author, icon_url=message.author.display_avatar.url)
        embed.set_footer(text=f"ID: {message.author.id}")
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot:
            return
        if not self.log_messages_channel_id:
            return
        
        log_channel = self.bot.get_channel(self.log_messages_channel_id)
        if not log_channel:
            return

        embed = discord.Embed(
            description=f"**Message modifié dans {before.channel.mention}**",
            color=discord.Color.blue()
        )
        embed.set_author(name=before.author, icon_url=before.author.display_avatar.url)
        embed.add_field(name="Avant", value=before.content or "*[Vide]*", inline=False)
        embed.add_field(name="Après", value=after.content or "*[Vide]*", inline=False)
        embed.set_footer(text=f"ID: {before.author.id}")
        await log_channel.send(embed=embed)

    # ===================== LOGS VOCAUX =====================

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not self.log_vocals_channel_id:
            return
        
        log_channel = self.bot.get_channel(self.log_vocals_channel_id)
        if not log_channel:
            return

        # Connexion à un salon
        if before.channel is None and after.channel is not None:
            embed = discord.Embed(
                description=f"🎙 **{member.display_name}** a rejoint le salon vocal {after.channel.mention}",
                color=discord.Color.green()
            )
            embed.set_author(name=member, icon_url=member.display_avatar.url)
            await log_channel.send(embed=embed)

        # Déconnexion d'un salon
        elif before.channel is not None and after.channel is None:
            embed = discord.Embed(
                description=f"❌ **{member.display_name}** a quitté le salon vocal {before.channel.mention}",
                color=discord.Color.red()
            )
            embed.set_author(name=member, icon_url=member.display_avatar.url)
            await log_channel.send(embed=embed)

        # Changement de salon
        elif before.channel != after.channel:
            embed = discord.Embed(
                description=f"🔄 **{member.display_name}** est passé de {before.channel.mention} à {after.channel.mention}",
                color=discord.Color.orange()
            )
            embed.set_author(name=member, icon_url=member.display_avatar.url)
            await log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Logs(bot))
