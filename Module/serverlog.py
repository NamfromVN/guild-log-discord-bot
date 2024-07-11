# -*- coding: utf-8 -*-
from typing import Union

import disnake
from disnake import Option, OptionType, ApplicationCommandInteraction
from disnake.ext import commands

from utils.ClientUser import ClientUser
from utils.GenEMBED import Embed


class Serverlog(commands.Cog):
    def __init__(self, bot):
        self.bot: ClientUser = bot

    emoji = "🛠️"
    name = "Sererlog"
    desc_prefix = f"[{emoji} {name}] | "
    
    @commands.cooldown(1, 300, commands.BucketType.guild) 
    @commands.has_guild_permissions(manage_guild=True, manage_channels=True)
    @commands.bot_has_guild_permissions(send_messages=True, read_message_history=True, manage_webhooks=True)
    @commands.slash_command(name="serverlog", description=f"{desc_prefix}Set the serverlog channel", options=[Option("channel", "The channel to set the serverlog to", OptionType.channel, required=True)])
    async def serverlog(self, ctx: Union[commands.Context, ApplicationCommandInteraction], channel: disnake.TextChannel):
        await ctx.response.defer()
        check = await self.bot.serverdb.check_database(ctx.guild.id)
        language = await self.bot.serverdb.guild_language(ctx.guild_id)
        kwargs = {
            "guild_name": ctx.guild.name,
            "channel_mention": channel.mention
        }
        if check["status"] == "No_Data":    #! KHÔNG CÓ DỮ LIỆU
                    webhook = await channel.create_webhook(name="Kaillen Log")
                    await self.bot.serverdb.setupserverlog(ctx.guild.id, webhook.url)
                    embed = disnake.Embed(title="Server Log", description=f"{self.bot.handle_language.get(language['language'], 'commands','active_server_log_msg').format(**kwargs)}")
                    embed.set_thumbnail(url="https://media.discordapp.net/stickers/1039992459209490513.png")
                    embed.set_footer(text=f"{self.bot.handle_language.get(language['language'], 'commands','interact_user').format(user=ctx.author.name)}", 
                                     icon_url=ctx.author.avatar.url)
                    await ctx.edit_original_response(embed=embed)
        elif check["status"] == "Data_Found": #* CÓ DỮ LIỆU
                        old_channel_webhook = await self.bot.serverdb.get_webhook(ctx.guild_id)
                        webhook = await channel.create_webhook(name="Kaillen Log")
                        # await self.bot.serverdb.remove_server_log(ctx.guild_id, old_channel_webhook)
                        await self.bot.serverdb.setupserverlog(ctx.guild.id, webhook.url)
                        embed = disnake.Embed(title="Server Log", description=f"{self.bot.handle_language.get(language['language'], 'commands','change_server_log_channel').format(**kwargs)}")
                        embed.set_thumbnail("https://media.discordapp.net/stickers/1039992459209490513.png")
                        embed.set_footer(text=f"{self.bot.handle_language.get(language['language'], 'commands','interact_user').format(user=ctx.author.name)}", 
                                        icon_url=ctx.author.avatar.url)
                        await ctx.edit_original_response(embed=embed)

    @commands.cooldown(1, 30, commands.BucketType.guild)
    @commands.has_guild_permissions(manage_roles=True, manage_guild=True)
    @commands.slash_command(name="ignorerole", description=f"{desc_prefix} Ignore a role from serverlog", 
                            options=[disnake.Option("role", "The role to ignore", OptionType.role, required=True, max_length=20, min_length=1, max_value=20)])
    async def ignorerole(self, ctx: Union[commands.Context, ApplicationCommandInteraction], role: disnake.Role):
        await ctx.response.defer(ephemeral=True)
        if role == ctx.guild.default_role:
            await ctx.edit_original_response("Bạn không thể sử dụng role này!")
            return
        check = await self.bot.serverdb.check_database(ctx.guild.id)
        language = await self.bot.serverdb.guild_language(ctx.guild_id)
        ADD_embed = disnake.Embed(title="ADD ROLE", description=f'{self.bot.handle_language.get(language["language"], "commands","add_ignore_role_msg").format(role_name=role.name)}', color=disnake.Color.green()).set_footer(text=self.bot.handle_language.get(language['language'], 'commands','interact_user').format(user=ctx.author.name), icon_url=self.bot.user.avatar)
        REMOVE_embed = disnake.Embed(title="REMOVE ROLE", description=f'{self.bot.handle_language.get(language["language"], "commands","remove_ignore_role_msg").format(role_name=role.name)}', color=disnake.Color.green()).set_footer(text=self.bot.handle_language.get(language['language'], 'commands','interact_user').format(user=ctx.author.name), icon_url=self.bot.user.avatar)
        if check["status"] == "Data_Found":
                        role_check = await self.bot.serverdb.check_role(ctx.guild.id, role.id)
                        if role_check["info"] == False:
                            await self.bot.serverdb.setup_ignored_roles(ctx.guild.id, role.id)
                            await ctx.send(embed=ADD_embed)
                        else:
                            await self.bot.serverdb.remove_ignore_role(ctx.guild.id, role.id)
                            await ctx.edit_original_response(embed=REMOVE_embed)
        elif check["status"] == "No_Data":
            cmd = f"</serverlog:" + str(self.bot.pool.controller_bot.get_global_command_named("serverlog", cmd_type=disnake.ApplicationCommandType.chat_input).id) +">"
            await ctx.edit_original_response(embed=Embed.gen_error_embed(self.bot.handle_language.get(language["language"], "commands","server_log_not_found").format(cmd=cmd)))
            return
        
        
        
def setup(bot: ClientUser): bot.add_cog(Serverlog(bot))