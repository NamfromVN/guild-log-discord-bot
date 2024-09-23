import logging

import disnake
from disnake.ext import commands

from utils.ClientUser import ClientUser

logger = logging.getLogger(__name__)

class GuildEntry(commands.Cog):
    def __init__(self, bot: ClientUser):
        self.client = bot
        
        
    @commands.Cog.listener("on_guild_remove")
    async def remove_data(self, guild: disnake.Guild):

        logger.info(f"Bị xóa khỏi máy chủ: {guild.name} - [{guild.id}]")
        data = self.client.serverdb.get_webhook(guild.id)
        
        if data is None:
            return

        try:
            self.client.serverdb.remove_server_data(guild.id)
        except Exception as e:
            logger.error(f"Đã xảy ra lỗi {e}")


def setup(bot: ClientUser): bot.add_cog(GuildEntry(bot))
