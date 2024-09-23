from datetime import datetime

import disnake
import pytz  # if you don't have this, do pip install pytz, it's used for timezones
from disnake.ext import commands

from utils.ClientUser import ClientUser as BotCore

HCM = pytz.timezone('Asia/Ho_Chi_Minh')

class OnMessageDelete(commands.Cog):
    def __init__(self, client: BotCore):
        self.client = client

    @commands.Cog.listener()
    async def on_message_delete(self, message: disnake.Message):
        if not message.guild or message.author.bot: return

        user_role_list = []
        if message.author._roles:
            for role_ids in message.author._roles:
                user_role_list.append(role_ids)

        check = self.client.serverdb.check_ignore_role(user_role_list, message.guild.id)
        user_role_list.clear()
        if check:
            return

        data = self.client.serverdb.get_webhook(message.guild.id)
        language = self.client.serverdb.guild_language(message.guild.id)

        if data is None:
            return

        channel = data

        embed = disnake.Embed(
            title=self.client.handle_language.get(language["language"], 'user',"message_delete"),
            description=self.client.handle_language.get(language["language"], 'user',"message_delete_msg").format(mention_author=message.author.mention, channel=message.channel.mention),
            color=disnake.Color.red(),
            timestamp=datetime.now(HCM),  # Use Set time for consistency
        )
        if message.content.startswith("https://media.discordapp.net/attachments"):
            embed.set_image(url=message.content)
        elif message.content.startswith("https://cdn.discordapp.com/attachments"):
            embed.set_image(url=message.content)
        elif message.content.startswith("https://tenor.com/view"):
            embed.set_image(url=message.content)
        elif message.content.startswith("https://giphy.com/gifs"):
            embed.set_image(url=message.content)
        elif message.content.startswith("https://imgur.com"):
            embed.set_image(url=message.content)
        elif message.attachments:
            embed.set_image(url=message.attachments[0].url)
        else:
            embed.add_field(name=self.client.handle_language.get(language["language"], 'user',"message_delete"), value=message.content, inline=False)
        

        await self.client.webhook_utils.process_webhook(channel, embed)

def setup(client: BotCore):
    client.add_cog(OnMessageDelete(client))