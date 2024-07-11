from datetime import datetime

import disnake
import pytz  # if you don't have this, do pip install pytz, it's used for timezones
from disnake.ext import commands

from utils.ClientUser import ClientUser

HCM = pytz.timezone('Asia/Ho_Chi_Minh')

class OnGuildChannelCreate(commands.Cog):
    def __init__(self, client: ClientUser):
        self.client = client 

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: disnake.TextChannel):
        if channel.name.startswith("ticket"):
            return
        
        language = await self.client.serverdb.guild_language(channel.guild.id)
   

        data = await self.client.serverdb.get_webhook(channel.guild.id)

        if data is None:
            return

        logchannel = data


        embed = disnake.Embed(
            title=self.client.handle_language.get(language["language"], "channel","channel_created"),
            description=self.client.handle_language.get(language["language"], "channel","channel_created_mention").format(channel = channel.mention),
            color=disnake.Color.red(),
            timestamp=datetime.now(HCM),
        )

        # await logchannel.send(embed=embed)
        await self.client.webhook_utils.process_webhook(logchannel, embed)

def setup(client: ClientUser):
    client.add_cog(OnGuildChannelCreate(client))