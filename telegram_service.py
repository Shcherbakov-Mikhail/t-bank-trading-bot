from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession

class TelegramService:

    def __init__(self, token: str, chat_id: str):
        self.session = AiohttpSession()
        self.__bot = Bot(token=token, session=self.session)
        self.__chat_id = chat_id

    async def send_text_message(self, text: str):
        await self.__bot.send_message(chat_id=self.__chat_id, text=text)

    async def close_bot_session(self):
        await self.session.close()

