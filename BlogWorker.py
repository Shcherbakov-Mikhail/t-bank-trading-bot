import asyncio
from telegram_service import TelegramService

class BlogWorker:
    """
    Class is represent worker (coroutine) for asyncio task.
    Checks available messages in queue and sends they asynchronously.
    """
    def __init__(self, bot_token, chat_id, messages_queue: asyncio.Queue):
        self.__messages_queue = messages_queue
        self.__tg_status = False
        self.__init_tg(bot_token, chat_id)

    def __init_tg(self, token: str, chat_id: str) -> None:
        try:
            self.__telegram_service = TelegramService(token=token, chat_id=chat_id)
            self.__tg_status = True
        except Exception as ex:
            print(f"Error init tg service {repr(ex)}")
            # Any errors with TG aren't important. Continue trading is important.
            self.__tg_status = False

    async def worker(self):
        while True:
            try:
                message = await self.__messages_queue.get()
                print(f"Get message form queue (size: {self.__messages_queue.qsize()}): {message}")

                if self.__tg_status:
                    await self.__telegram_service.send_text_message(message)

            except Exception as ex:
                print(f"TG messages worker error: {repr(ex)}")