from __future__ import annotations

import asyncio
import logging
from typing import Optional
from asgiref.sync import sync_to_async as s2a
from pymongo import MongoClient

logger = logging.getLogger(__name__)

class Cache():
    storage: dict[int, dict] = {}

    async def setupdefault(self, guildID = None):
        if guildID is None: return
        await s2a(self.database.db.guild.insert_one)({"guild_id": guildID,
                                          "language": "vi", 
                                          "webhook_url": None, 
                                          "ignoreroles": []})

    # Tasks
    async def __create_guild_data_remotedb__(self, guild_id: int):
        await self.setupdefault(guild_id)

    async def __remove_guild_data_remotedb__(self, guild_id: int):
        try:
            await s2a(self.database.db.guild.delete_one)({"guild_id": guild_id})
        except Exception as e:
            logger.error(f"Đã xảy ra lỗi khi xoá dữ liệu guild {guild_id} trên database: {repr(e)}")

    async def __commit_all__(self):
        """Automatic commit cache to database every 10 minutes"""
        while True:
            await asyncio.sleep(600)
            count = 0
            for guild_id in self.storage:
                if await self.commit(guild_id): count += 1
            if count != 0: logger.info(f"Đã đồng bộ cache của {count} guilds lên database")


    def __init__(self, mongo_client: MongoClient):
        self.database = mongo_client
        asyncio.create_task(self.__commit_all__())

    def close(self):
        logger.info("Đang lưu tất cả dữ liệu vào database")
        count = 0
        for guild_id in self.storage:
            guild = self.storage.get(guild_id, None)
            if guild is None: continue
            if guild["synced"]: continue
            try:
                self.database.db.guild.update_one({"guild_id": guild_id}, {"$set": {"webhook_url": guild["webhook_url"], "language": guild["language"], "ignoreroles": guild["ignoreroles"]}})
            except Exception as e:
                logger.error(f"Đã xảy ra lỗi khi cập nhật dữ liệu guild {guild_id} lên database: {repr(e)}")
            finally:
                count += 1

        logger.info(f"Đã đồng bộ cache của {count} guilds lên database")

    def get_guild(self, guild_id: int) -> dict:
        """Fetch guild data from remote database"""
        guild = self.storage.get(guild_id, None)
        if guild is not None: return guild
        # If no guild data in storage
        data = {
            "synced": False,
            "language": "vi",
            "webook_url": None,
            "ignoreroles": []
        }
        if not data["synced"]:
            logger.info(f"Đang lấy dữ liệu cho guildID: {guild_id}")
            try:
                guild_data = self.database.db.guild.find_one({"guild_id": guild_id})
                data["language"] = guild_data["language"]
                data["ignoreroles"] = guild_data["ignoreroles"]
                data["webhook_url"] = guild_data["webhook_url"]
                data["synced"] = True
            except TypeError:
                asyncio.create_task(self.__create_guild_data_remotedb__(guild_id))
            except Exception as e:
                logger.warning(f"Đồng bộ dữ liệu guild {guild_id} thất bại: {repr(e)}")
            finally:
                self.storage[guild_id] = data
                return self.storage[guild_id]

    def get(self, guild_id: int, properties: str):
        """Get guild properties"""
        return self.get_guild(guild_id).get(properties, None)

    def set(self, guild_id: int, properties: str, value, commit = False) -> None:
        """Set guild properties"""
        guild = self.get_guild(guild_id)
        guild[properties] = value
        guild["synced"] = False
        if commit: asyncio.create_task(self.commit(guild_id, True))

    def role_cache(self, guild_id: int, role_id: int, commit = False) -> None:
        """role cache func"""
        guildData = self.get_guild(guild_id)
        if role_id not in guildData["ignoreroles"]:
            guildData["ignoreroles"].append(role_id)
        else:
            guildData["ignoreroles"].remove(role_id)
        if commit: asyncio.create_task(self.commit(guild_id, True))

    def delete(self, guild_id: int):
        """Remove guild data"""
        try:
            self.storage.pop(guild_id)
            asyncio.create_task(self.__remove_guild_data_remotedb__(guild_id))
        except: pass

    async def commit(self, guild_id: int, force_sync: bool = False) -> bool:
        """Commit cache to remote database"""
        guild = self.storage.get(guild_id, None)
        if guild is None: return False
        if force_sync == False and guild["synced"]: return False
        try:
            await s2a(self.database.db.guild.update_one)({"guild_id": guild_id}, {"$set": {"webhook_url": guild["webhook_url"], "language": guild["language"], "ignoreroles": guild["ignoreroles"]}})
            guild["synced"] = True
            logger.info(f"Đã cập nhật dữ liệu của guildID: {guild_id} lên database")
            return True
        except Exception as e:
            logger.error(f"Đã xảy ra lỗi khi cập nhật dữ liệu guild {guild_id} lên database: {repr(e)}")
            guild["synced"] = False
            return False


class Databases:
    def __init__(self) -> None:
        self.dbclient: Optional[MongoClient] = None
        self.cache = None
        self.guild = None

    async def loadDB(self, serveruri = None):
        self.dbclient = MongoClient(host=serveruri)
        self.guild = self.dbclient.db.guild
        self.cache = Cache(self.dbclient)
        logger.info("Database init ok")


    def close(self):
        self.cache.close()


    async def get_webhook(self, guild_id: int):
        return self.cache.get(guild_id, "webhook_url") 

    async def setupserverlog(self, guildID, webhook_url):
        try:
            await  self.get_webhook(guildID)
            self.cache.set(guildID, "webhook_url", webhook_url)
        except TypeError:
            await self.cache.setupdefault(guildID)
            self.cache.set(guildID, "webhook_url", webhook_url)
             
    async def get_ignored_roles(self, guild_id: int) -> list | None:
        return self.cache.get(guild_id, "ignoreroles")
    
    async def guild_language(self, guild_id: int) -> dict:
        return {"status": "DataFound", "language": self.cache.get(guild_id, "language")}

    async def func_language(self, guild_id, language):
        self.cache.set(guild_id, "language", language)
        return {"status": "Done", "msg": "Đã cài đặt thành công"}

    async def replace_language(self, guild_id: int, language: str):
        self.cache.set(guild_id, "language", language)
        return {"status": "Done", "msg": "Đã cập nhật thành công"}
        
    async def setup_ignored_roles(self, guild_id: int, role_id: int):
        self.cache.role_cache(guild_id, role_id, commit=True)
        return {"status": "Done", "msg": "Đã cập nhật thành công"}
                
    async def remove_ignore_role(self, guildID, roleID):
        self.cache.role_cache(guildID, roleID, commit=True)

    async def check_mute(self, roles, guild: int) -> bool:
                data = self.cache.get(guild, "ignoreroles") or []
                if not data:
                    return False
                for roleData in data:
                    if int(roleData) in roles:
                        return True
                    return False

    async def check_role(self, guildID, roleID):
        data = self.cache.get(guildID, "ignoreroles")
        if data is None:
            return {
                "info": False,
                "data": "None"
            }
        elif roleID not in data:
            return {
                    "info": False,
                        "data": "None"
                                }

        elif roleID in data:
            return {
                "info": True,
                "data": data
            }
        
    async def check_database(self, guildID):
        raw_Data = await self.get_webhook(guildID)
        if raw_Data is None:
            return {"status": "No_Data"}
        else:
            return {"status": "Data_Found", "webhook_uri": raw_Data}

    async def remove_server_data(self, guild_id: int):
        self.cache.delete(guild_id)
