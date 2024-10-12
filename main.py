import asyncio
from dotenv import dotenv_values
from TBankClient import TBankClient
from SimpleStrategy import SimpleStrategy
# from BlogWorker import BlogWorker
# from Blogger import Blogger

async def run():

    config = dotenv_values(".env")
    TOKEN = config['TINKOFF_TOKEN_SANDBOX']
    APP_NAME = config['APP_NAME']

    # BOT_TOKEN = config['BOT_TOKEN']
    # CHAT_ID = config['CHAT_ID']
    # messages_queue = asyncio.Queue()
    # blogger = Blogger(messages_queue=messages_queue)
    # blog_worker = BlogWorker(bot_token=BOT_TOKEN, chat_id=CHAT_ID, messages_queue=messages_queue)
    # blog_task = asyncio.create_task(blog_worker.worker())
    # await blog_task

    client = TBankClient(token=TOKEN, app_name=APP_NAME, sandbox=True)
    strategy = SimpleStrategy(client=client)

    client_task = asyncio.create_task(client.ainit())
    strategy_task = asyncio.create_task(strategy.start())

    await client_task
    await strategy_task


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(loop.create_task(run()))