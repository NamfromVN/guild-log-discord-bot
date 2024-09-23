import disnake

from disnake.ext import commands
                                

from utils.ClientUser import ClientUser


class Language(commands.Cog):
    def __init__(self, client):
        self.client: ClientUser = client
        # self.Language = ["Tiếng Việt", "English"]
        
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.has_guild_permissions(manage_guild=True)
    @commands.slash_command(name="change_language", description="Change the language that the bot will response in this server", dm_permission=False, 
                                                options=[disnake.Option(name="language", 
                                                description="Ngôn ngữ cần đổi", 
                                                required=True, 
                                                choices=[disnake.OptionChoice(name="Tiếng Việt", value="vi"), 
                                                        disnake.OptionChoice(name="English", value="en")
                                ]
                            )
                        ]
                      )
    async def language_handle(self, ctx: disnake.ApplicationCommandInteraction, language: str):
        await ctx.response.defer()
        old_setting = self.client.serverdb.guild_language(ctx.guild_id)
        if old_setting["status"] == "DataFound":
            s = self.client.serverdb.replace_language(ctx.guild_id, language)
            if s["status"] == "Failed": 
                await ctx.edit_original_response(s["msg"]) 
                return
            up_embed = disnake.Embed()
            up_embed.description = self.client.handle_language.get(language, "commands",'languageChange')
            await ctx.edit_original_response(embed=up_embed)    
        else:
            setting = self.client.serverdb.func_language(ctx.guild_id, language)
            if setting["status"] != "Done":
                await ctx.edit_original_response(setting["msg"])
                return
            txt = self.client.handle_language.get(language, "commands","languageChange")
            embed = disnake.Embed()
            embed.description = txt
            await ctx.edit_original_response(embed=embed)
        
def setup(client: ClientUser): client.add_cog(Language(client))
