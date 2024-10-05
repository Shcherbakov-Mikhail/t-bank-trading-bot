from SQLClient import OrderSQLiteClient, SimpleStrategySQLiteClient
from tinkoff.invest.exceptions import InvestError
import asyncio

class SimpleStrategy:

    def __init__(self, client):
        self.client = client
        self.check_interval = 60
        self.token = None
        self.account_id = None
        self.filename = "strategy.xlsx"
        self.sheet_name = "strategy"
        # OrderHander here

    async def post_orders(self):
        # post here and send to handler to track execution
        pass

    async def stop_loss_check(self):
        # worth implementing it? (it would check portfolio from time to time)
        pass

    async def market_opened_check(self):
        pass

    # async def instrument_available_check(self):
    #     pass

    async def post_strategy_orders(self):
        print(f"Reading data from excel...")
        strategy_db = SimpleStrategySQLiteClient(db_name="simple_strategy")
        strategy_db.add_orders_from_excel(self.filename, self.sheet_name)
        for item in strategy_db.get_strategy():
            print(item)

    async def main_cycle(self):

        print(f"Starting Simple Strategy")
        try:
            # await self.market_opened_check()
            
            await self.post_strategy_orders()

        except InvestError as error:
            print(f"Initial Posting error: {error}")

        # TODO: this can check stop loss after posting, but not now
        # while true:
        # await self.stop_loss_check()
        # await asyncio.sleep(self.check_interval) 

    
    async def start(self):
        if self.account_id is None:
            try:
                self.account_id = (await self.client.get_accounts()).accounts.pop().id
            except InvestError as error:
                print(f"Error taking account id. Stopping strategy. {error}")
                return
        await self.main_cycle()

