from datetime import datetime

import disnake
import pytz  # if you don't have this, do pip install pytz, it's used for timezones
from disnake.ext import commands

from utils.ClientUser import ClientUser as BotCore

HCM = pytz.timezone('Asia/Ho_Chi_Minh')

class ONUNBAN(commands.Cog):
    def __init__(self, client: BotCore):
        self.client = client

    @commands.Cog.listener()
    async def on_member_unban(self, guild: disnake.Guild, user: disnake.User):


        data = await self.client.serverdb.get_webhook(guild.id)
        language = await self.client.serverdb.guild_language(guild.id)
        

        if data is None:
            return

        channel = data


        embed = disnake.Embed(
            title=self.client.handle_language.get(language["language"], 'user',"unban_user"),
            description=self.client.handle_language.get(language["language"], 'user',"mention_user_unban").format(user=user.name),
            color=disnake.Color.red(),
            timestamp=datetime.now(HCM),
        )

        await self.client.webhook_utils.process_webhook(channel, embed)

def setup(client: BotCore):
    client.add_cog(ONUNBAN(client))