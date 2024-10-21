from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import FSInputFile
import asyncio

class BloggerClient:
    def __init__(self, bot_token, chat_id):
        self.session = AiohttpSession()
        self.__bot = Bot(token=bot_token, session=self.session)
        self.__chat_id = chat_id

    async def send_text_message(self, text: str):
        await self.__bot.send_message(chat_id=self.__chat_id, text=text)
        
    async def send_photo(self, file_name : str, caption=None):
        await self.__bot.send_photo(chat_id=self.__chat_id, photo=FSInputFile(file_name), caption=caption)