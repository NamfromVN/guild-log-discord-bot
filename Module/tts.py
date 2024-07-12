import logging
import os
import platform
import re
import sqlite3
import traceback

import disnake
from disnake import FFmpegPCMAudio
from disnake.ext import commands
from gtts import gTTS

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
    comm.close()
    
async def get_tts_lang(guildID):
    comm = sqlite3.connect("langDB.sql")
    try:
        mouse = comm.cursor()
        mouse.execute("SELECT language FROM guildLang WHERE guildID = ?", (guildID,))
        data = mouse.fetchone()
        if not data:
            return "Tiếng Việt"
        
        return data[0]
    finally:
        comm.close()

def inittable():
    comm = sqlite3.connect("langDB.sql")
    mouse = comm.cursor()
    mouse.execute("""CREATE TABLE IF NOT EXISTS guildLang(
                                                guildID INTERGER,
                                                language TEXT DEFAULT 'Tiếng Việt')""")
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
        inittable()

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(description=f"{desc_prefix}Tạo âm thanh từ văn bản", aliases=["s", "speak"])
    async def say(self, ctx: disnake.AppCommandInteraction, *, content = None):
            if platform.system() == "Windows":
                await ctx.channel.send("Hãy xài WSL hoặc chỉnh sửa lại cấu trúc code để module này hoạt động!")
                return

            if not ctx.author.voice:
                await ctx.send("Nya Nya nyan, pliz join a voice channel")
                return

            if not ctx.guild.me.voice:

                perms = ctx.author.voice.channel.permissions_for(ctx.guild.me)

                if not perms.connect:
                    await ctx.send("Nya! 💢, I dont have perm to connect to your channel")
                    return

            # Xử lý dữ liệu ngôn ngữ
            lang = await get_tts_lang(ctx.author.guild.id)
            convlang = await convert_language(lang)

            # Task
            
            channel = ctx.author.voice.channel
            
            try:
                vc = await channel.connect()
            except Exception as e:
                if "Already connected to a voice channel" in str(e):
                    vc = ctx.author.guild.voice_client
                else:
                    traceback.print_exc()
                    await ctx.channel.send(f"Nya! 💢")
                    return
                    
            channel_id = ctx.guild.me.voice.channel.id
            guild_id = ctx.guild.id
            
            await process_tts(content, guild_id, channel_id, convlang)


            try:
                vc.play(FFmpegPCMAudio(f"./data_tts/{guild_id}/{channel_id}_tts.mp3"))
                
            except Exception as e:
                    traceback.print_exc()
                    await ctx.channel.send(f"Nya! 💢")



    @commands.command(description=f"{desc_prefix}Disconnect", aliases=["stoptts"])
    async def tts_stop(self, ctx: disnake.ApplicationCommandInteraction):
        
        vc = ctx.author.guild.voice_client
        if vc:
            if ctx.author.id not in ctx.guild.me.voice.channel.voice_states:
                await ctx.send("Nya! 💢, you are not on my channel.")
                return
            try:
                os.remove(f"./data_tts/{ctx.guild.id}/{ctx.guild.me.voice.channel.id}_tts.mp3")
            except FileNotFoundError:
                pass
            except Exception as e:
                await ctx.channel.send(f"Nya! 💢")
                logging.error(f"Error {e}")
            
            await vc.disconnect()
            await ctx.send("Disconnected.", delete_after=3)
        else:
            await ctx.channel.send("Nya! 💢, I'm not connected to any voice channel.")
    
    @commands.cooldown(1, 15, commands.BucketType.guild)
    @commands.has_guild_permissions(manage_channels=True)
    @commands.slash_command(name = "tts_language", description=f"{desc_prefix} Change language for tts module", options=[disnake.Option('language', description='Language')])
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
