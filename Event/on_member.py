from disnake.ext.commands import Cog
from disnake import Member, Embed
from utils.ClientUser import ClientUser

class OnMemberJoin(Cog):
    def __init__(self, bot):
        self.bot: ClientUser = bot

    @Cog.listener("on_member_join")
    async def on_member_join(self, member: Member):
        db = self.bot.serverdb
        lang_handle = self.bot.handle_language

        language = db.guild_language(member.guild.id)

        webhook_url = db.get_webhook(member.guild.id)
        embed = Embed(
            description=lang_handle.get(language["language"], "user", "member_join").format(name=member.mention)
        )
        await self.bot.webhook_utils.process_webhook(webhook_url, embed=embed)

    @Cog.listener("on_member_remove")
    async def on_member_leave(self, member: Member):
        db = self.bot.serverdb
        lang_handle = self.bot.handle_language

        language = db.guild_language(member.guild.id)

        webhook_url = db.get_webhook(member.guild.id)
        embed =     Embed(
            description=lang_handle.get(language["language"], "user", "member_leave").format(name=member.mention)
        )
        await self.bot.webhook_utils.process_webhook(webhook_url, embed=embed)


def setup(bot: ClientUser):
    bot.add_cog(OnMemberJoin(bot))