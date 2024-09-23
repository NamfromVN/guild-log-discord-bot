from datetime import datetime

import disnake
import pytz  # if you don't have this, do pip install pytz, it's used for timezones
from disnake.ext import commands

from utils.ClientUser import ClientUser

HCM = pytz.timezone('Asia/Ho_Chi_Minh')

class OnGuildChannelDelete(commands.Cog):
    def __init__(self, client: ClientUser):
        self.client = client

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: disnake.TextChannel):

        if channel.name.startswith("ticket"): #! Ingore ticket channel
            return

        language = self.client.serverdb.guild_language(channel.guild.id)

        data = self.client.serverdb.get_webhook(channel.guild.id)

        if data is None:
            return


        logchannel = data

        
        embed = disnake.Embed(
            title=self.client.handle_language.get(language["language"], "channel","channel_deleted"),
            description=self.client.handle_language.get(language["language"], 'channel',"channel_deleted_mention").format(channel=channel.name),
            color=disnake.Color.red(),
            timestamp=datetime.now(HCM),
        )

        # await logchannel.send(embed=embed)
        await self.client.webhook_utils.process_webhook(logchannel, embed)

def setup(client: ClientUser):
    client.add_cog(OnGuildChannelDelete(client))