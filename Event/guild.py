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
        data = await self.client.serverdb.get_guild_webhook(guild.id)
        
        if data["status"] == "No_Data":
            return
        
        guild_webhook = data
        
        try:
            self.client.serverdb.cache.delete(guild.id)
        except Exception as e:
            logger.error(f"Đã xảy ra lỗi {e}")


def setup(bot: ClientUser): bot.add_cog(GuildEntry(bot))
