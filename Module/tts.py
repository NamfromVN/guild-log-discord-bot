import disnake
from gtts import gTTS
from disnake.ext import commands
from disnake import FFmpegPCMAudio

import re
import platform
import traceback
import sqlite3

import os
from utils.ClientUser import ClientUser as Client

LANGUAGE_LIST = ["English", "Tiếng Việt", "日本語", "русский", "中国人"]


def check_voice():

    async def predicate(inter):

        
        guild = inter.guild

        try:
            if not inter.author.voice:
                await inter.send("Nya Nya nyan, pliz join a voice channel")
                return
        except AttributeError:
            pass

        if not guild.me.voice:

            perms = inter.author.voice.channel.permissions_for(guild.me)

            if not perms.connect:
                await inter.send("Nya! 💢, I dont have perm to connect to your channel")
                return 

        try:
            if inter.author.id not in guild.me.voice.channel.voice_states:
                return
        except AttributeError:
            pass

        return True

    return commands.check(predicate)

async def save_lang_tts(guildID, language):
    comm = sqlite3.connect("langDB.sql")
    mouse = comm.cursor()
    mouse.execute("""INSERT INTO guildLang (guildID, language) VALUES (?, ?)""", (guildID, language))
    comm.commit()
    comm.close
    
async def get_tts_lang(guildID):
    comm = sqlite3.connect("langDB.sql")
    try:
        mouse = comm.cursor()
        mouse.execute("SELECT language FROM guildLang WHERE guildID = ?", (guildID,))
        data = mouse.fetchone()
        if not data:
            return "vi"
        
        return data[0]
    finally:
        mouse.close()
        comm.close()

async def on_init():
    comm = sqlite3.connect("langDB.sql")
    mouse = comm.cursor()
    mouse.execute("""CREATE TABLE IF NOT EXISTS guildLang (
                                                guildID INTERGER,
                                                language TEXT DEFAULT)""")
    comm.commit()
    comm.close()


async def check_lang(lang):
    pattern = r"^[a-z]{2}$"
    return bool(re.match(pattern, lang))


async def convert_language(lang):
    langlist = {"English": "en", 
                "Tiếng Việt": "vi", 
                "日本語": "ja", 
                "русский": "ru", 
                "中国人": "zh"
                }
    return langlist.get(lang)

async def process_tts(text, guild_id, channel_id, lang):
    tts = gTTS(text, lang=lang)
    if not os.path.exists(f'./data_tts/{guild_id}'):
        os.makedirs(f'./data_tts/{guild_id}')
    tts.save(f'./data_tts/{guild_id}/{channel_id}_tts.mp3')

class TTS(commands.Cog):
    emoji = "🔊"
    name = "TTS"
    desc_prefix = f"[{emoji} {name}] | "

    def __init__(self, bot: Client):
        self.bot = bot
        on_init()

    @check_voice()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.member, wait=False)
    @commands.command(description=f"{desc_prefix}Tạo âm thanh từ văn bản", aliases=["s", "speak"])
    async def say(self, ctx: disnake.AppCommandInteraction, *, content = None):
            if platform.system() == "Windows":
                await ctx.channel.send("Hãy xài WSL hoặc chỉnh sửa lại cấu trúc code để module này hoạt động!")
                return

            if not ctx.author.voice:
                await ctx.send("Nya Nya nyan, pliz join a voice channel")
                return

            # Xử lý dữ liệu ngôn ngữ
            lang = await get_tts_lang(ctx.author.guild.id)
            convlang = await convert_language(lang)
            await process_tts(content, ctx.guild.id, ctx.channel.id, convlang)
            
            channel = ctx.author.voice.channel
            
            try:
                vc = await channel.connect()
            except Exception as e:
                if "Already connected to a voice channel" in str(e):
                    vc = ctx.author.guild.voice_client
                else:
                    vc = ctx.author.guild.voice_client

            global channel_id, guild_id

            channel_id = ctx.channel.id
            guild_id = ctx.guild.id

            if vc.is_playing():
                return


            try:
                vc.play(FFmpegPCMAudio(f"./data_tts/{guild_id}/{channel_id}_tts.mp3"))
                

                   
            except Exception as e:
                # if "ffmepg was not found" in str(e):
                #     await ctx.channel.send("Không tìm thấy ffmpeg, hãy chắc chắn rằng bạn đã chạy tệp `autoinstall.sh`")
                #     traceback.print_exc()
                #     return
                # else:
                    traceback.print_exc()
                    await ctx.channel.send(f"Nya! 💢")
                    return

    @check_voice()
    @commands.command(description=f"{desc_prefix}Disconnect", aliases=["stoptts"])
    async def tts_stop(self, ctx: disnake.ApplicationCommandInteraction):
        vc = ctx.author.guild.voice_client
        if vc:
            
            await vc.disconnect()
            await ctx.channel.send("Đã ngắt kết nối với kênh thoại.")
            try:
                os.remove(f"./data_tts/{guild_id}/{channel_id}_tts.mp3")
            except FileNotFoundError:
                print("Error at line 122: File Not Found :<")
                pass
            except Exception as e:
                await ctx.channel.send(f"Đã xảy ra lỗi: {repr(e)}")
        else:
            await ctx.channel.send("Tôi đang không kết nối với kênh thoại nào.")
    
    @commands.cooldown(1, 15, commands.BucketType.guild)
    @commands.has_guild_permissions(manage_channels=True)
    @commands.slash_command("tts_language", description=f"{desc_prefix} Change language for tts module", options=[disnake.Option('language', description='Language')])
    async def tts_language(self, ctx: disnake.ApplicationCommandInteraction, language: str = None):
        await ctx.response.defer(ephemeral=True)
        await save_lang_tts(ctx.author.guild.id, language)
        await ctx.edit_original_response(f"Language changed to: {language}")
        
    @tts_language.autocomplete('language')
    async def get_lang(inter: disnake.Interaction, lang: str):
        lang = lang.lower()
        return [lang for lang in LANGUAGE_LIST]
        

def setup(bot: Client):
    bot.add_cog(TTS(bot))
