from aiohttp import ClientSession
from disnake import Webhook


class Process_webhook:
    def __init__(self):
        pass

    async def process_webhook(self, webhook_uri, embed):
        """WEBHOOK MAIN"""
        if webhook_uri is None: return
        async with ClientSession() as session:
            webhok = Webhook.from_url(webhook_uri, session=session)
            await webhok.send(embed=embed, username="Kaillen Mod bot", avatar_url="https://i.ibb.co/MRxRR8h/boticon.png")

    async def test_webhook(self, webhook_uri):
        """TEST WEBHOOK"""
        async with ClientSession() as session:
            kwargs = {
                "url": webhook_uri,
                "session": session
            }
            webhook = Webhook.from_url(**kwargs)
            await webhook.send(content="Test OK")