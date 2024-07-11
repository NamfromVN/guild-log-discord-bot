from datetime import datetime

import disnake
import pytz  # if you don't have this, do pip install pytz, it's used for timezones
from disnake.ext import commands

from utils.ClientUser import ClientUser

HCM = pytz.timezone('Asia/Ho_Chi_Minh')

class OnGuildChannelUpdate(commands.Cog):
    def __init__(self, client: ClientUser):
        self.client = client 

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: disnake.TextChannel, after: disnake.TextChannel):
        if before.name.startswith("ticket"): #! Ingore ticket channel
            return

        if after is not disnake.TextChannel:
            return

        if before.name != after.name:
            data = await self.client.serverdb.get_webhook(before.guild.id)

            if data is None:
                return
            
            language = await self.client.serverdb.guild_language(before.guild.id)

            try:
                channel = data
            except KeyError:
                return

            embed = disnake.Embed(
                title=self.client.handle_language.get(language["language"], 'channel',"channel_updated"),
                description=self.client.handle_language.get(language["language"], 'channel',"channel_updated_mention").format(channel=before.mention),
                color=disnake.Color.red(),
                timestamp=datetime.now(HCM),
            )

            embed.add_field(name=self.client.handle_language.get(language["language"], 'commands',"before"), value=before.name, inline=False)
            embed.add_field(name=self.client.handle_language.get(language["language"], 'commands',"after"), value=after.name, inline=False)

            await self.client.webhook_utils.process_webhook(channel, embed)

def setup(client: ClientUser):
    client.add_cog(OnGuildChannelUpdate(client))