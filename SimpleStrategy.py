import asyncio
import time, sys
from uuid import uuid4
from decimal import Decimal

from TBankClient import TBankClient
from SQLClient import SimpleStrategySQLiteClient
from handler import OrderHandler
from Blogger import Blogger

from tinkoff.invest import (
    InstrumentIdType,
    OrderDirection,
    OrderType
)
from tinkoff.invest.utils import decimal_to_quotation, quotation_to_decimal
from tinkoff.invest.exceptions import InvestError


class SimpleStrategy:

    def __init__(self, client, blogger):
        self.client : TBankClient = client
        self.active_orders_check_interval = 5
        self.order_status_check_interval = 10
        self.token = None
        self.account_id = None
        self.filename = "strategy.xlsx"
        self.sheet_name = "strategy"
        self.blogger  : Blogger = blogger
        self.orders_handler = OrderHandler(client, blogger, self.order_status_check_interval)
        self.sql_strategy_client = SimpleStrategySQLiteClient()
        self.print_active_orders = True
        

    async def stop_loss_check(self):
        # worth implementing it? (it would check portfolio from time to time)
        pass

    async def instrument_available_check(self):
        pass

    # async def instrument_available_check(self):
    #     pass

    async def handle_strat_order(self, order):
        ticker, percentage, lots = order

        figi = await self.client.get_figi_by_ticker(ticker)

        ticker_close_price = await self.client.get_close_price(figi)
        exec_price = Decimal(ticker_close_price * (1 + percentage))

        order_type = OrderType.ORDER_TYPE_LIMIT
        order_direction = OrderDirection.ORDER_DIRECTION_BUY if percentage < 0 else OrderDirection.ORDER_DIRECTION_SELL
                    
        min_price_increment = (
            await self.client.get_instrument_by(
                id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI, 
                id=figi
            )
        ).instrument.min_price_increment

        number_digits_after_point = 9 - len(str(min_price_increment.nano)) + 1
        min_price_increment = quotation_to_decimal(min_price_increment)
        exec_price = (round(exec_price / min_price_increment) * min_price_increment)

        ticker_trading_status = await self.client.get_trading_status(figi=figi)
        if not (ticker_trading_status.market_order_available_flag and ticker_trading_status.api_trade_available_flag):
            self.blogger.ticker_trading_closed_message(ticker)
            self.print_active_orders = False
            return

        try:
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
            # print(f'Failed to post order: {order}. \nError: {error}')
            self.blogger.failed_to_post_order_message(order)
            self.print_active_orders = False
            return 
        
        handle = asyncio.create_task(
                        self.orders_handler.handle_new_order(
                            order_id=posted_order.order_id,
                            account_id=self.account_id,
                            exec_price=float(exec_price)
                        )
                    )
        
        await handle

    async def print_active_orders(self):
        if not self.print_active_orders:
            return
        while True:
            print(self.print_active_orders)
            await asyncio.sleep(self.active_orders_check_interval)
            try:
                orders = (await self.client.get_orders(account_id=self.account_id)).orders
                # print()
                # print(f"Active Orders: {len(orders)}")
                # print()
                self.blogger.active_orders_message(len(orders))
            except InvestError as error:
                # print(f'Unaible to get acrive orders! Error:\n{error}')
                self.blogger.failed_to_get_active_orders_message()
                continue


    async def main_cycle(self):

        self.blogger.start_trading_message()

        print(f"Paying in...")
        await self.client.add_money_to_sandbox_account(self.account_id, amount=5000000)

        print(f"Reading data from excel...")
        self.sql_strategy_client.add_orders_from_excel(self.filename, self.sheet_name)

        # print(f'Initial orders:\n\t{self.sql_strategy_client.get_strategy()}')
        self.blogger.list_initial_orders_message(self.sql_strategy_client.get_strategy())

        print(f"Posting initial orders...")
        self.blogger.posting_initial_orders_message()

        tasks = [asyncio.create_task(self.handle_strat_order(order))
                 for order in self.sql_strategy_client.get_strategy()
                ]
                
        # tasks.append(asyncio.create_task(self.print_active_orders()))
        await asyncio.wait(tasks)

        print('ended tasks')

        self.blogger.close_session_message()
        return

        
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

