from SQLClient import OrderSQLiteClient, SimpleStrategySQLiteClient
from tinkoff.invest.exceptions import InvestError
import asyncio
from TBankClient import TBankClient
import time, sys
from handler import OrderHandler
from uuid import uuid4
from decimal import Decimal
from datetime import timedelta

from tinkoff.invest import (
    InstrumentIdType,
    OrderDirection,
    OrderType,
    MoneyValue
)

from tinkoff.invest.utils import now, decimal_to_quotation, quotation_to_decimal

class SimpleStrategy:

    def __init__(self, client):
        self.client : TBankClient = client
        self.check_interval = 5
        self.token = None
        self.account_id = None
        self.filename = "strategy.xlsx"
        self.sheet_name = "strategy"
        self.orders_handler = OrderHandler(client)
        self.sql_strategy_client = SimpleStrategySQLiteClient()

    async def stop_loss_check(self):
        # worth implementing it? (it would check portfolio from time to time)
        pass

    async def market_opened_check(self):
        pass

    # async def instrument_available_check(self):
    #     pass

    async def handle_strat_order(self, order):
        ticker, percentage, lots = order

        try:
            figi = await self.client.get_figi_by_ticker(ticker)

            ticker_close_price = await self.client.get_close_price(figi)
            exec_price = Decimal(ticker_close_price * (1 + percentage))

            order_type = OrderType.ORDER_TYPE_LIMIT
            order_direction = OrderDirection.ORDER_DIRECTION_BUY if percentage < 0 else OrderDirection.ORDER_DIRECTION_SELL
            order_direction_str = "Short" if percentage < 0 else "Long"
                    
            min_price_increment = (
                await self.client.get_instrument_by(
                    id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI, 
                    id=figi
                )
            ).instrument.min_price_increment

            number_digits_after_point = 9 - len(str(min_price_increment.nano)) + 1
            min_price_increment = quotation_to_decimal(min_price_increment)
            exec_price = (round(exec_price / min_price_increment) * min_price_increment)

            posted_order = await self.client.post_order(
                figi=figi,
                quantity=lots,
                price=decimal_to_quotation(Decimal(exec_price)),
                direction=order_direction,
                account_id=self.account_id,
                order_type=order_type,
                order_id=str(uuid4()),
                instrument_id=figi
                        )
            
        except InvestError as error:
            print(f'Failed to post order: {order}. \nError: {error}')
            return 
        
        blog = asyncio.create_task(
                        self.orders_handler.handle_new_order(
                            order_id=posted_order.order_id,
                            account_id=self.account_id
                        )
                    )
        
        await blog


    async def main_cycle(self):

        print(f"Paying in...")
        await self.client.add_money_to_sandbox_account(self.account_id, amount=100000)

        print(f"Reading data from excel...")
        self.sql_strategy_client.add_orders_from_excel(self.filename, self.sheet_name)
        print(self.sql_strategy_client.get_strategy())

        # print(f"Posting initial orders...")
        # await asyncio.wait([
        #     asyncio.create_task(self.handle_strat_order(order))
        #     for order in self.sql_strategy_client.get_strategy()
        # ])

    
    async def start(self):
        if self.account_id is None:
            try:
                # self.account_id = (await self.client.get_accounts()).accounts.pop().id
                accounts = (await self.client.get_accounts()).accounts
                if len(accounts) != 0:
                    for account in accounts:
                        print(f"Closing old accounts...")
                        await self.client.close_sandbox_account(account.id)
                print(f"Opening new account...")
                self.account_id = (await self.client.open_sandbox_account()).account_id

            except InvestError as error:
                print(f"Error taking account id. Stopping strategy. {error}")
                return
        await self.main_cycle()

