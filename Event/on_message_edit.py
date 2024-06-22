from datetime import datetime

import disnake
import pytz  # if you don't have this, do pip install pytz, it's used for timezones
from disnake.ext import commands

from utils.ClientUser import ClientUser as BotCore

HCM = pytz.timezone('Asia/Ho_Chi_Minh')

class OnMessageEdit(commands.Cog):
    def __init__(self, client: BotCore):
        self.client = client

    @commands.Cog.listener()
    async def on_message_edit(self, before: disnake.Member, after):
        if not before.guild or before.author.bot: return
        check = await self.client.serverdb.check_mute(before.author.roles, before.guild.id)
        if check == True: return
        if before.content == after.content:
            return #! Ignore if the message is the same
        language = await self.client.serverdb.guild_language(before.guild.id)

        data = await self.client.serverdb.get_guild_webhook(before.guild.id)

        if data is None:
            return

        channel = data
        message = after.jump_url

        embed = disnake.Embed(
            title=self.client.handle_language.get(language["language"], 'user',"message_edit"),
            description=self.client.handle_language.get(language["language"], 'user',"message_edit_msg").format(mention_author=before.author.mention, channel=before.channel.mention),
            color=disnake.Color.red(),
            timestamp=datetime.now(HCM),
        )
        try:
         embed.add_field(name="", value=f"[Message]({message})", inline=False)
        except Exception as e:
            print(e)
        embed.add_field(name=self.client.handle_language.get(language["language"], "commands","before"), value=before.content, inline=False)
        embed.add_field(name=self.client.handle_language.get(language["language"], "commands","after"), value=after.content, inline=False)

        await self.client.webhook_utils.process_webhook(channel, embed)

def setup(client: BotCore):
    client.add_cog(OnMessageEdit(client))