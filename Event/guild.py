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

    @commands.Cog.listener("on_guild_join")
    async def guild_join(self, guild: disnake.Guild):

        logger.info(f"Đã được thêm vào máy chủ mới: {guild.name} - [{guild.id}] | Số máy chủ: {len(self.client.guilds)}")

        if self.client.guilds.__len__() == 100 and self.client.application_flags.gateway_message_content_limited:
            logger.warning("Số máy chủ đã đạt 100 nhưng bạn chưa được nhận message intent, điều này có thể gây ra một số vấn đề khi sử dụng!")



def setup(bot: ClientUser): bot.add_cog(GuildEntry(bot))
