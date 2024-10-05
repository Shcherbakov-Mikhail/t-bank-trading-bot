from aiogram import Bot

class TelegramService:

    def __init__(self, token: str, chat_id: str) -> None:
        self.__bot = Bot(token=token)
        self.__chat_id = chat_id

    async def send_text_message(self, text: str) -> None:
        print(f"TG API send text message: '{text}'")

        await self.__bot.send_message(chat_id=self.__chat_id, text=text)

        print(f"TG message has been sent.")