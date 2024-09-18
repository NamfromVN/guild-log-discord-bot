from __future__ import annotations

import asyncio
import logging
import os
from asyncio import create_task

import disnake
from disnake.ext import commands

from utils.server.databases import Databases
from utils.loc import loc
from utils.server.process_webhook import Process_webhook

logger = logging.getLogger(__name__)

class ClientUser(commands.AutoShardedBot):
    
    def __init__(self, *args, intents, command_sync_flag, command_prefix: str, **kwargs) -> None:
        super().__init__(*args, **kwargs, intents=intents, command_sync_flags=command_sync_flag, command_prefix=command_prefix)
        self.uptime = disnake.utils.utcnow()
        self.serverdb = Databases()
        self.db =None
        self.handle_language = loc
        self.webhook_utils = Process_webhook()
        self.remote_git_url = os.environ.get("SOURCE")
        self.task = asyncio
        self.environ = os.environ
    
    async def on_ready(self):
            logger.info(f" Client: {self.user.name} - {self.user.id} Ready")
            await self.process_rpc()

    async def process_rpc(self):
        activity = disnake.Activity(
                        type=disnake.ActivityType.watching,
                        name="Guild log",
                    )
        logger.info('Load RPC')
        await ClientUser.change_presence(self, activity=activity)
        
    async def close(self):
        self.serverdb.close()
        return await super().close()


    def load_modules(self):

        modules_dir = ["Module", "ModuleDEV", "Event"]


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


def start():
    logger.info("> Booting Client....")
    
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
    create_task(bot._watchdog())


    if not os.environ.get("MONGOSERVER"):
        logger.warning(f"No MongoDB database connected, abort")
        exit()

    bot.task.run(bot.serverdb.loadDB(os.environ.get("MONGOSERVER")))

    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        if  "LoginFailure" in str(e):
            logger.error("An Error occured:", repr(e))
