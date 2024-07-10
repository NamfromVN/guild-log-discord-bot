import asyncio
import logging
from typing import Any

from asgiref.sync import sync_to_async as s2a
from pymongo import MongoClient

# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     from utils.ClientUser import ClientUser

logger = logging.getLogger(__name__)

# class db:
#     GuildSetting = "GuildSetting"
#
# db.GuildSetting = {
#         "guild_id": None,
#         "webhook_url": None,
#         "language": "vi",
#         "ignore_roles": []
#     }

class GuildCache():
    storage: dict[int, dict] = {}

    # Tasks
    async def __create_guild_data_remotedb__(self, guild_id: int):
        try:
            await s2a(self.database.db.language.insert_one)({"guild_id": guild_id, "language": "vi"})
            # await s2a(self.database.db.servers.insert_one)({"guild_id": guild_id, "webhook_uri": None})
        except Exception as e:
            logger.error(f"Đã xảy ra lỗi khi tạo dữ liệu guild {guild_id} trên database: {repr(e)}")

    async def __remove_guild_data_remotedb__(self, guild_id: int):
        try:
            await s2a(self.database.db.language.delete_one)({"guild_id": guild_id})
            # await s2a(self.database.db.servers.delete_one)({"guild_id": guild_id})
        except Exception as e:
            logger.error(f"Đã xảy ra lỗi khi xoá dữ liệu guild {guild_id} trên database: {repr(e)}")

    async def __commit_all__(self):
        "Automatic commit cache to database every 10 minutes"
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
                self.database.db.language.update_one({"guild_id": guild_id}, {"$set": {"language": guild["language"]}})
                # self.database.db.servers.update_one({"guild_id": guild_id}, {"$set": {"language": guild["webhook_uri"]}})
            except Exception as e:
                logger.error(f"Đã xảy ra lỗi khi cập nhật dữ liệu guild {guild_id} lên database: {repr(e)}")
            finally:
                count += 1

        logger.info(f"Đã đồng bộ cache của {count} guilds lên database")

    def get_guild(self, guild_id: int) -> dict:
        "Fetch guild data from remote database"
        guild = self.storage.get(guild_id, None)
        remote_data_exist = True
        if guild is not None: return guild
        # If no guild data in storage
        data = {
            "synced": False,
            "language": "vi",
            # "webook_uri": None
        }
        try:
            language_data = self.database.db.language.find_one({"guild_id": guild_id})
            if language_data is not None: data["language"] = language_data["language"]
            else: remote_data_exist = False
            # webhook_data = await s2a(self.database.db.servers.find_one)({"guild_id": guild})
            # if webhook_data is not None: data["webhook_uri"] = webhook_data["webhook_uri"]
            # else: remote_data_exist = False
            data["synced"] = True
        except Exception as e:
            logger.warning(f"Đồng bộ dữ liệu guild {guild_id} thất bại: {repr(e)}")
        finally:
            self.storage[guild_id] = data
            if remote_data_exist == False: asyncio.create_task(self.__create_guild_data_remotedb__(guild_id))
            return self.storage[guild_id]

    def get(self, guild_id: int, properties: str):
        "Get guild properties"
        return self.get_guild(guild_id).get(properties, None)

    def set(self, guild_id: int, properties: str, value, commit = False) -> None:
        "Set guild properties"
        guild = self.get_guild(guild_id)
        guild[properties] = value
        guild["synced"] = False
        if commit: asyncio.create_task(self.commit(guild_id, True))

    def delete(self, guild_id: int):
        "Remove guild data"
        try:
            self.storage.pop(guild_id)
            asyncio.create_task(self.__remove_guild_data_remotedb__(guild_id))
        except: pass

    async def commit(self, guild_id: int, force_sync: bool = False) -> bool:
        "Commit cache to remote database"
        guild = self.storage.get(guild_id, None)
        if guild is None: return False
        if force_sync == False and guild["synced"]: return False
        try:
            await s2a(self.database.db.language.update_one)({"guild_id": guild_id}, {"$set": {"language": guild["language"]}})
            # await s2a(self.database.db.servers.update_one)({"guild_id": guild_id}, {"$set": {"language": guild["webhook_uri"]}})
            guild["synced"] = True
            return True
        except Exception as e:
            logger.error(f"Đã xảy ra lỗi khi cập nhật dữ liệu guild {guild_id} lên database: {repr(e)}")
            guild["synced"] = False
            return False


class GuildIgnoredRoleEntity():
    id: int
    roles: set[int] = () # dùng set đi ôg, set dùng trong trường hợp này nó tối ưu lắm :yum:
    synced = False
    
    def contain(self, role_id: int) -> bool:
        "Return True if role_id contains in ignored roles, false otherwises"
        return role_id in self.roles
    
    def add(self, role_id: int) -> None:
        "Add role_id to ignored roles"
        self.roles.add(role_id)
        self.synced = False
        
    def remove(self, role_id: int) -> None:
        "Remove role_id to ignored roles"
        self.roles.discard(role_id)
        self.synced = False
        
    def get_array(self) -> list[int]:
        return list(self.roles)
        
    

class GuildIgnoredRoleCache():
    storage: dict[GuildIgnoredRoleEntity] = {}
    
    async def __commit_all__(self):
        count = 0
        for guild_id in self.collection:
            if await self.commit(guild_id): count += 1
        if count != 0: logger.info(f"Đã đồng bộ cache của {count} guilds lên database")
    
    
    async def __sync_task__(self):
        while True:
            await asyncio.sleep(600)
            await self.__commit_all__()
    
    
    def __init__(self, db_client: MongoClient):
        self.collection = db_client.db.ignored_roles
        asyncio.create_task(self.__sync_task__())
        
    
    async def get(self, guild_id: int) -> GuildIgnoredRoleEntity:
        try: return self.storage[guild_id]
        except KeyError:
            self.storage[guild_id] = GuildIgnoredRoleEntity()
            entity: GuildIgnoredRoleEntity = self.storage[guild_id]
            data = await s2a(self.collection.find_one)({"guild_id": guild_id})
            if data is not None:
                for role_id in data["role_id"]: entity.add(role_id)
                entity.synced = True
            return entity 
                
    
    async def get_ignored_roles(self, guild_id: int) -> list[int]:
        guild = await self.get(guild_id)
        return guild.get_array() 
        
    

class Server():
    def __init__(self):
        self.guilds_webhook_cache: dict[int, str] = {} # { 1234567890: "https://localhost:2002/webhook/12345678910/1234567890abcde" }
        self.role_cache: dict[int, list] = {}  # { 1234567890: [] }

    def close(self):
        self.cache.close()


    async def connect_to_MongoDB(self, serveruri = None):
        """Connect to the database, if Aval"""
        self.client = MongoClient(host=serveruri)
        self.servers = self.client.db.servers
        self.ignored_roles = self.client.db.ignored_roles
        self.language = self.client.db.language
        logger.info(f"Connected to Server Database")
        self.cache = GuildCache(self.client)
        self.ignored_roles_cache = GuildIgnoredRoleCache(self.client)


    async def guild_language(self, guild_id: int) -> dict:
        return {"status": "DataFound", "language": self.cache.get(guild_id, "language")}

    async def func_language(self, guild_id, language):
        self.cache.set(guild_id, "language", language)
        return {"status": "Done", "msg": "Đã cài đặt thành công"}

    async def replace_language(self, guild_id: int, language: str):
        self.cache.set(guild_id, "language", language)
        return {"status": "Done", "msg": "Đã cập nhật thành công"}

    async def remove_language_on_leave(self, guild_id: int):
        self.cache.delete(guild_id)

    async def get_guild_webhook(self, guild_id: int):

        guild_webhook = self.guilds_webhook_cache.get(guild_id)

        if guild_webhook == " ":
            return None # Catch value " " and return None

        if guild_webhook is None:
            guild_webhook = await self.get_webhook(guild_id)

            if guild_webhook is None:
                self.guilds_webhook_cache[guild_id] = " " # Set webhook uri value " "
                guild_webhook = None
            else:
                 self.guilds_webhook_cache[guild_id] = guild_webhook

        return guild_webhook

    async def get_role_by_guildID(self, guildID) -> list | Any:

        guild_roleID = self.role_cache.get(guildID)

        if guild_roleID == []:
            return None

        if guild_roleID is None:
            db_guild_roleID = await self.get_ignored_roles(guildID)
            if db_guild_roleID == None:
                self.role_cache[guildID] = []
                return []
            else:
                self.role_cache[guildID] = db_guild_roleID
                return db_guild_roleID

        return guild_roleID


    async def delrolecache(self, guildID):
        try:
            self.role_cache.pop(guildID)
        except KeyError:
            pass

    async def delwebhookcache(self, guild_id: int):
        try:
            self.guilds_webhook_cache.pop(guild_id)
        except KeyError:
            pass

    async def check_role(self ,guildID: int, role_id: int) -> dict:
        data = await s2a(self.ignored_roles.find_one)({"guild_id": guildID})
        if data is None:
            return {
                "info": False,
                "data": "None"
            }
        elif role_id not in data["role_id"]:
            return {
                "info": False,
                "data": "None"
            }

        elif role_id in data["role_id"]:
            return {
                "info": True,
                "data": data
            }

    async def check_mute(self, role: str, guild: int) -> bool:
        # data = await s2a(self.ignored_roles.find_one)({"guild_id": guild})

        data = await self.get_role_by_guildID(guild)
        if data is None or data == []:
            return False

        for roleData in data:
            if str(roleData) not in role:
                continue
            else:
                return True

        


    async def check_database(self, guild):
        data = await s2a(self.servers.find_one)({"guild_id": guild})
        if not data:
            return {"status": "No_Data"}
        else:
            return {"status": "Data_Found", "webhook_uri": data["webhook_uri"]}

    async def check_server_db(self, guild_id: int):
        data = await s2a(self.servers.find_one)({"guild_id": guild_id})
        if data is None:
            return False
        else:
            return True

    async def get_ignored_roles(self, guild_id: int) -> list | None:
        data = await s2a(self.ignored_roles.find_one)({"guild_id": guild_id})

        if data is None or []:
            return None
        else:
            return data["role_id"]


    async def get_webhook(self, guild_id: int):
        data = await s2a(self.servers.find_one)({"guild_id": guild_id})
        if data is None:
            return None
        else:
            return data["webhook_uri"]

    async def setupserverlog(self, guild_id: int, webhook_uri: str):
        data = await s2a(self.servers.find_one)({"guild_id": guild_id})
        if data is None:
            await s2a(self.servers.insert_one)({"guild_id": guild_id, "webhook_uri": webhook_uri})
            return {
                "status": "success"
            }
        else:
            return {
                "status": "error"
            }

    async def remove_server_log(self, guild_id: int, webhook_uri: str):
        try:
            await s2a(self.servers.delete_one)({"guild_id": guild_id, "webhook_uri": webhook_uri})
            return {
                "status": "success"
            }
        except Exception:
            return {
                "status": "failed"
            }


    async def setup_ignored_roles(self, guild_id: int, role_id: int):
        data = await s2a(self.ignored_roles.find_one)({"guild_id": guild_id})
        if data is None:
            await s2a(self.ignored_roles.insert_one)({"guild_id": guild_id, "role_id": [role_id]})
            return {
                "status": "success",
                "action": "insert"
            }
        else:
            await s2a(self.ignored_roles.update_one)({"guild_id": guild_id}, {"$push": {"role_id": role_id}})
            return {
                "status": "success",
                "action": "update_sql"
            }

    async def remove_ignore_role(self, guildID, roleID):
        await s2a(self.ignored_roles.update_one)({"guild_id": guildID}, {"$pull": {"role_id": roleID}})

    async def remove_ignored_role_data(self, guild_id: int):
        data = await self.get_ignored_roles(guild_id)
        if data is None:
            return {
                "status": "no_data"
            }
        try:
            await s2a(self.ignored_roles.delete_one)({"guild_id": guild_id})
            return {
                "status": "done"
            }
        except Exception as e:
            return {
                "status": "failed",
                "msg": f"Đã xảy ra lỗi: {e}"
            }
