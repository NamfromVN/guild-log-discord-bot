from __future__ import annotations

import asyncio
import logging
import os

import disnake
from disnake.ext import commands

from utils.server.language_handle import LocalizationManager
from utils.server.process_webhook import Process_webhook
from utils.server.databases import Server
from utils.server.newdb import Databases

logger = logging.getLogger(__name__)

class ClientUser(commands.AutoShardedBot):
    
    def __init__(self, *args, intents, command_sync_flag, command_prefix: str, **kwargs) -> None:
        super().__init__(*args, **kwargs, intents=intents, command_sync_flags=command_sync_flag, command_prefix=command_prefix)
        self.uptime = disnake.utils.utcnow()
        self.serverdb = Databases()
        self.db =None
        self.handle_language = LocalizationManager()
        self.webhook_utils = Process_webhook()
        self.remote_git_url = os.environ.get("SOURCE")
        self.task = asyncio
        
    
    async def on_ready(self):
            logger.info(f"Client: {self.user.name} - {self.user.id} Ready")
            await self.process_rpc()


            
    async def on_resume(self):
        logger.info(f"Client Resumed")
        
 
            
    async def process_rpc(self):
        activity = disnake.Activity(
                        type=disnake.ActivityType.watching,
                        name="Guild log",
                    )
        logger.info('Load RPC')
        await ClientUser.change_presence(self, activity=activity)
        
    def close(self):
        self.serverdb.close()
        self.serverdb.guilds_webhook_cache.clear()
        return super().close()


    def load_modules(self):

        modules_dir = ["Module", "ModuleDEV"]


        for module_dir in modules_dir:
        
            for item in os.walk(module_dir):
                files = filter(lambda f: f.endswith('.py'), item[-1])
                for file in files:
                    filename, _ = os.path.splitext(file)
                    module_filename = os.path.join(module_dir, filename).replace('\\', '.').replace('/', '.')
                    try:
                        self.reload_extension(module_filename)
                        logger.info(f'Module {file} Đã tải lên thành công')
                    except (commands.ExtensionAlreadyLoaded, commands.ExtensionNotLoaded):
                        try:
                            self.load_extension(module_filename)
                            logger.info(f'Module {file} Đã tải lên thành công')
                        except Exception as e:
                            logger.error(f"Đã có lỗi xảy ra với Module {file}: Lỗi: {repr(e)}")
                            continue
                    except Exception as e:
                            logger.error(f"Đã có lỗi xảy ra với Module {file}: Lỗi: {repr(e)}")
                            break
                
                


    
    def load_events(self):

        eventdir =  ["Event", "EventDEV"]

        for events_dir in eventdir:

            for item in os.walk(events_dir):
                files = filter(lambda f: f.endswith('.py'), item[-1])
                for file in files:
                    filename, _ = os.path.splitext(file)
                    module_filename = os.path.join(events_dir, filename).replace('\\', '.').replace('/', '.')
                    try:
                        self.reload_extension(module_filename)
                        logger.info(f'Event {file} Đã tải lên thành công')

                    except (commands.ExtensionAlreadyLoaded, commands.ExtensionNotLoaded):
                        try:
                            self.load_extension(module_filename)
                            logger.info(f'Event {file} Đã tải lên thành công')

                        except Exception as e:
                            logger.error(f"Đã có lỗi xảy ra với Event {file}: Lỗi: {repr(e)}")

                            continue
                    except Exception as e:
                        logger.error(f"Đã có lỗi xảy ra với Event {file}: Lỗi: {repr(e)}")

                        break

def start():
    logger.info("Booting Client....")
    
    DISCORD_TOKEN = os.environ.get("TOKEN")
    
    
    intents = disnake.Intents()
    intents.voice_states = True
    intents.message_content = True
    intents.guilds = True
    intents.moderation = True
    intents.messages = True
    intents.members = True
        
    sync_cfg = True
    command_sync_config = commands.CommandSyncFlags(
                        allow_command_deletion=sync_cfg,
                        sync_commands=sync_cfg,
                        sync_commands_debug=sync_cfg,
                        sync_global_commands=sync_cfg,
                        sync_guild_commands=sync_cfg
                    )  
    
    bot  = ClientUser(intents=intents, command_prefix="k!", command_sync_flag=command_sync_config)
    
    bot.load_modules()
    
    bot.load_events()

    bot.handle_language.load_localizations()

    if not os.environ.get("MONGOSERVER"):
        logger.warning(f"No MongoDB database connected, abort")
        exit()

    bot.task.run(bot.serverdb.connect_to_MongoDB(os.environ.get("MONGOSERVER")))

    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        if  "LoginFailure" in str(e):
            logger.error("An Error occured:", repr(e))
