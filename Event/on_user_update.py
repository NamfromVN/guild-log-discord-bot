import disnake
from disnake.ext import commands

from utils.ClientUser import ClientUser


class OnMemberUpdate(commands.Cog):
    def __init__(self, client: ClientUser):
        self.client = client
    
    @commands.Cog.listener()
    async def on_member_update(self, before: disnake.Member, after: disnake.Member):
        # Bỏ qua bot
        if after.bot or before.bot:
            return
    
        # Kiểm tra thay đổi vai trò
        if before.roles != after.roles:
            
            roleUpdate = list(set(after.roles) - set(before.roles))
            if roleUpdate:
                roleChange = ", ".join([role.mention for role in roleUpdate])
                loc = "user_added_role"
            else:
                removed_roles = list(set(before.roles) - set(after.roles))
                if removed_roles:
                    roleChange = ", ".join([role.mention for role in removed_roles])
                    loc = "user_removed_role"
                else:
                    return
                
            kwargs = {
                "userName": after.name,
                "role": roleChange
            }

            language = self.client.serverdb.guild_language(after.guild.id)

            webhook_uri = self.client.serverdb.get_webhook(after.guild.id)

            if webhook_uri is None:
                return

            embed = disnake.Embed()
            txt = self.client.handle_language.get(language["language"], 'user', loc)
            embed.description = txt.format(**kwargs)

            await self.client.webhook_utils.process_webhook(webhook_uri, embed)
    
def setup(bot: ClientUser): bot.add_cog(OnMemberUpdate(bot))
