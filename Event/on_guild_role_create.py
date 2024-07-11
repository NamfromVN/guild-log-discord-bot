from datetime import datetime

import disnake
import pytz  # if you don't have this, do pip install pytz, it's used for timezones
from disnake.ext import commands

from utils.ClientUser import ClientUser

HCM = pytz.timezone('Asia/Ho_Chi_Minh')

class OnGuildRoleCreate(commands.Cog):
    def __init__(self, client: ClientUser):
        self.client = client

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: disnake.Role): 
  

        data = await self.client.serverdb.get_webhook(role.guild.id)
        language = await self.client.serverdb.guild_language(role.guild.id)

        if data is None:
            return

        channel = data

        embed = disnake.Embed(
            title=self.client.handle_language.get(language["language"], 'role',"role_created"),
            description=self.client.handle_language.get(language["language"], 'role',"mention_role_created").format(role = role.mention),
            color=disnake.Color.red(),
            timestamp=datetime.now(HCM),
        )

        await self.client.webhook_utils.process_webhook(channel, embed)

def setup(client: ClientUser):
    client.add_cog(OnGuildRoleCreate(client))