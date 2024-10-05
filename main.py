import asyncio
from dotenv import dotenv_values
from TBankClient import TBankClient
from SimpleStrategy import SimpleStrategy

async def run():

    config = dotenv_values(".env")
    TOKEN = config['TINKOFF_TOKEN_SANDBOX']
    APP_NAME = config['APP_NAME']

    client = TBankClient(token=TOKEN, app_name=APP_NAME, sandbox=True)
    await client.ainit()

    strategy = SimpleStrategy(client)
    await strategy.start()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(loop.create_task(run()))