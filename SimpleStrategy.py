import asyncio
import time, sys
from uuid import uuid4
from decimal import Decimal

from TBankClient import TBankClient
from SQLClient import SimpleStrategySQLiteClient
from Handler import OrderHandler
# from Blogger import Blogger

from tinkoff.invest import (
    InstrumentIdType,
    OrderDirection,
    OrderType
)
from tinkoff.invest.utils import decimal_to_quotation, quotation_to_decimal
from tinkoff.invest.exceptions import InvestError


class SimpleStrategy:

    def __init__(self, client, blogger=None):
        self.client : TBankClient = client
        self.client_check_interval = 5
        self.order_status_check_interval = 1
        self.token = None
        self.account_id = None
        self.filename = "strategy.xlsx"
        self.sheet_name = "strategy"
        self.blogger = blogger
        self.orders_handler = OrderHandler(client, blogger, self.order_status_check_interval)
        self.sql_strategy_client = SimpleStrategySQLiteClient()
        self.print_active_orders = True
        self.print_last_price = True
        

    # async def stop_loss_check(self, last_price):
    #     positions = (await self.client.get_portfolio(account_id=self.account_id)).positions
    #     position = get_position(positions, self.figi)
    #     if position is None or quotation_to_float(position.quantity) == 0:
    #         return
    #     position_price = quotation_to_float(position.average_position_price)
    #     if last_price <= position_price - position_price * self.config.stop_loss_percent:
    #         logger.info(f"Stop loss triggered. Last price={last_price} figi={self.figi}")
    #         try:
    #             quantity = int(quotation_to_float(position.quantity)) / self.instrument_info.lot
    #             if not is_quantity_valid(quantity):
    #                 raise ValueError(f"Invalid quantity for posting an order. quantity={quantity}")
    #             posted_order = await client.post_order(
    #                 order_id=str(uuid4()),
    #                 figi=self.figi,
    #                 direction=ORDER_DIRECTION_SELL,
    #                 quantity=int(quantity),
    #                 order_type=ORDER_TYPE_MARKET,
    #                 account_id=self.account_id,
    #             )
    #         except Exception as e:
    #             logger.error(f"Failed to post sell order. figi={self.figi}. {e}")
    #             return
    #         asyncio.create_task(
    #             self.stats_handler.handle_new_order(
    #                 order_id=posted_order.order_id, account_id=self.account_id
    #             )
    #         )
    #     return

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

        # if not (ticker_trading_status.market_order_available_flag and ticker_trading_status.api_trade_available_flag):
        #     # self.blogger.ticker_trading_closed_message(ticker)
        #     # self.print_active_orders = False
        #     print(f'{ticker} trading is closed!')
        #     return

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
            # self.blogger.failed_to_post_order_message(order)
            # self.print_active_orders = False
            print(f'Failed to post {order}\nError: {error}')
            return
        
        handle = asyncio.create_task(
                        self.orders_handler.handle_new_order(
                            order_id=posted_order.order_id,
                            account_id=self.account_id,
                            exec_price=float(exec_price)
                        )
                    )
        
        await handle

        return order

    # async def print_active_orders(self):
    #     if not self.print_active_orders:
    #         return
    #     while True:
    #         await asyncio.sleep(self.active_orders_check_interval)
    #         try:
    #             orders = (await self.client.get_orders(account_id=self.account_id)).orders
    #             # self.blogger.active_orders_message(len(orders))
    #             print(f'Active orders: {len(orders)}')
    #         except InvestError as error:
    #             print(f'Failed to get active orders!\nError:\n{error}')
    #             # self.blogger.failed_to_get_active_orders_message()
    #             continue


    # async def print_last_price(self, ticker, figi):
    #     # if not self.print_last_price:
    #     #     return
    #     while True:
    #         await asyncio.sleep(self.print_last_price_interval)
    #         try:
    #             last_price = (await self.client.get_last_prices(figi=[figi])).last_prices.pop().price
    #             # self.blogger.last_price_message(ticker, last_price)
    #             print(f'Last price: {last_price}')
    #         except InvestError as error:
    #             print(f'Failed to get the last price! Error:\n{error}')
    #             # self.blogger.failed_to_get_last_price_message(ticker)
    #             continue


    async def main_cycle(self):

        ticker = 'SBER'
        stop_loss_perc = 0.05

        figi = await self.client.get_figi_by_ticker(ticker)
        ticker_close_price = await self.client.get_close_price(figi)
        last_price = (await self.client.get_last_prices(figi=[figi])).last_prices.pop().price
        last_price = float(quotation_to_decimal(last_price))

        # self.blogger.start_trading_message()
        print('Starting trading')

        print(f"Paying in...")
        await self.client.add_money_to_sandbox_account(self.account_id, amount=5000000)

        print(f"Reading data from excel...")
        # self.sql_strategy_client.add_orders_from_excel(self.filename, self.sheet_name)
        # strategies = self.sql_strategy_client.get_strategy()

        strategies = [
            ('SBER', 0.001, 1),
            ('SBER', -0.001, 1),
        ]


        # self.blogger.close_price_message(ticker, ticker_close_price)
        print(f'{ticker} close price: {ticker_close_price}')
        # self.blogger.last_price_message(ticker, last_price)
        print(f'{ticker} last price: {last_price}')

        # print(f'Initial orders:\n\t{self.sql_strategy_client.get_strategy()}')
        # self.blogger.list_initial_orders_message(self.sql_strategy_client.get_strategy())

        print(f"Posting initial orders...")
        # self.blogger.posting_initial_orders_message()
        tasks = [asyncio.create_task(self.handle_strat_order(order))
                 for order in strategies
                ]

        # print_active_orders_task = asyncio.create_task(self.print_active_orders())
        # tasks.append(print_active_orders_task)
        # print_last_price_task = asyncio.create_task(self.print_last_price(ticker, figi))
        # tasks.append(print_last_price_task)
        
        while tasks:

        for done_task in asyncio.as_completed(tasks):
            order = await done_task
            print(f'Completed: {order}')



        # while True:
        #     try:
        #         done, pending = await asyncio.wait(tasks)
        #         order_triggered = done.pop().result()
        #         print(f'First completed: {order_triggered}')
        #         print(1)
        #     except InvestError as error:
        #         print(f'Client error:\n{error}')
            # await asyncio.sleep(self.client_check_interval)

        # min_price_increment = (
        #     await self.client.get_instrument_by(
        #         id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI, 
        #         id=figi
        #     )
        # ).instrument.min_price_increment

        # min_price_increment = quotation_to_decimal(min_price_increment)
        # minus_bp_price = (round(exec_price / min_price_increment) * min_price_increment)


        # minus_bp_order = ()
        # minus_bp_order_task = asyncio.create_task(self.handle_strat_order(minus_bp_order))
        # tasks.append(minus_bp_order_task)

        # done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        # print(done.pop().result())

        # self.blogger.close_session_message()
        print('Closing the session!')

        
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

