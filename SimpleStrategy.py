import asyncio
import time, sys
from uuid import uuid4
from decimal import Decimal
from Errors import Errors
from datetime import datetime

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
        self.sql_strategy_client = SimpleStrategySQLiteClient()
        self.blogger = blogger
        self.account_id = None
        self.ticker = None
        self.figi = None
        self.close_price = None
        self.last_price = None
        self.min_price_increment = None
        self.lot_size = None
        self.basic_points = None
        self.tasks = []
        self.loss_check_interval = 10 # 6 requests per minute
        self.order_status_check_interval = 3 # 40 requests per minute for 1 percentage level (+&-)
        self.stop_loss_percentage = None
        self.filename = "strategy.xlsx"
        self.sheet_name = "strategy"
        self.orders_handler = OrderHandler(client, blogger, self.order_status_check_interval)
        

    async def trading_is_available(self):
        ticker_trading_status = await self.client.get_trading_status(figi=self.figi)
        if not (ticker_trading_status.market_order_available_flag and ticker_trading_status.api_trade_available_flag):
            print(f'{self.ticker} trading is closed!')
            return False
        return True


    async def handle_strat_order(self, order, reverse=False):
        
        if not reverse:
            percentage, lots = order
            
            order_type = OrderType.ORDER_TYPE_LIMIT
            order_direction = OrderDirection.ORDER_DIRECTION_BUY if percentage < 0 else OrderDirection.ORDER_DIRECTION_SELL

            exec_price = Decimal(self.close_price * (1 + percentage))       
            exec_price = (round(exec_price / self.min_price_increment) * self.min_price_increment)
            
        else:
            exec_price, lots, order_direction = order
            order_type = OrderType.ORDER_TYPE_LIMIT
               
        if not (await self.trading_is_available()):
            return Errors.TICKER_NOT_AVAILABLE

        try:
            posted_order = await self.client.post_order(
                figi=self.figi,
                quantity=lots,
                price=decimal_to_quotation(Decimal(exec_price)),
                direction=order_direction,
                account_id=self.account_id,
                order_type=order_type,
                order_id=str(uuid4()),
                instrument_id=self.figi
                )            
        except InvestError as error:
            print(f'Failed to post {order} at {datetime.now().time()}')
            return Errors.FAILED_TO_POST_ORDER
        
        handle = asyncio.create_task(
                        self.orders_handler.handle_new_order(
                            order_id=posted_order.order_id,
                            account_id=self.account_id,
                            exec_price=float(exec_price),
                            lot_size=self.lot_size
                        )
                    )
        
        actual_exec_price = await handle
        

        if actual_exec_price is Errors.FAILED_TO_HANDLE_ORDER:
            return 

        return order, reverse, actual_exec_price


    async def stop_loss_check(self):
        await asyncio.sleep(self.loss_check_interval)
        
        if not (await self.trading_is_available()):
            return True, Errors.TICKER_NOT_AVAILABLE
        
        self.last_price = float(
            quotation_to_decimal(
                (await self.client.get_last_prices(figi=[self.figi]))
                .last_prices.pop().price
                )
            )
     
        if self.last_price >= self.close_price * (1 + self.stop_loss_percentage):
            print(f'Stop loss triggered from above! Last price = {self.last_price}')
            return True, OrderDirection.ORDER_DIRECTION_BUY
        elif self.last_price <= self.close_price * (1 - self.stop_loss_percentage):
            print(f'Stop loss triggered from below! Last price = {self.last_price}')
            return True, OrderDirection.ORDER_DIRECTION_SELL

        print(f'No stop loss. Last price = {self.last_price}')
        return False, None


    async def main_cycle(self): 
        self.ticker = 'SBER'
        self.stop_loss_percentage = 0.01
        self.basic_points = 1
        
        self.figi = await self.client.get_figi_by_ticker(self.ticker)
        # self.close_price = await self.client.get_close_price(self.figi) 
        self.last_price = float(
            quotation_to_decimal(
                (await self.client.get_last_prices(figi=[self.figi]))
                .last_prices.pop().price
                )
            )
        self.close_price = self.last_price # DEBUG
        self.min_price_increment = quotation_to_decimal(
            (await self.client.get_instrument_by(
                id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI,
                id=self.figi))
                .instrument.min_price_increment
            )
        self.lot_size = (
                await self.client.get_instrument_by(
                    id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI, 
                    id=self.figi
                    )
                ).instrument.lot

        await self.client.add_money_to_sandbox_account(self.account_id, amount=5000000)

        strategies = [
            (0.0005, 1),
            (-0.0005, 1),
        ]
        self.tasks = [asyncio.create_task(self.handle_strat_order(order))
                      for order in strategies
                      ]
        stop_loss_check_task = asyncio.create_task(self.stop_loss_check())
        
        print(f'{self.ticker} close price: {self.close_price}')
        print(f'{self.ticker} last price: {self.last_price}\n')
        print(f'Started at {datetime.now().time()}\n')
        
        while self.tasks:
            done, _ = await asyncio.wait([stop_loss_check_task] + self.tasks, return_when=asyncio.FIRST_COMPLETED)
            
            if stop_loss_check_task in done:
                stop_loss, direction = await stop_loss_check_task
                done.remove(stop_loss_check_task)
                if stop_loss:
                    print("Stop loss triggered!")
                    for t in self.tasks:
                        t.cancel()
                    # TODO: close the positions at stop loss
                    print("Closing positions!")
                    if direction is OrderDirection.ORDER_DIRECTION_SELL:
                        pass
                    elif direction is OrderDirection.ORDER_DIRECTION_BUY:
                        pass
                    else:
                        pass
                    return
                else:
                    stop_loss_check_task = asyncio.create_task(self.stop_loss_check())
                    
            if len(done) > 1:
                # TODO: multiple orderes triggered during the check interval (how to handle them?)
                print(f'{len(done)=}')

            for task in done:
                result = await task
                if isinstance(result, Errors):
                    for t in self.tasks:
                        t.cancel()
                    # TODO: close the positions at posting error
                    print("Closing positions!")
                    return
                
                else:
                    completed_order, reverse, exec_price = result
                    self.tasks.remove(task)
                    
                    if reverse:
                        # reverse sell
                        if completed_order[2] == OrderDirection.ORDER_DIRECTION_SELL:
                            percentage = strategies[1][0]
                            lots = strategies[1][1]
                            new_order = (percentage, lots)
                        # reverse buy
                        else:
                            percentage = strategies[0][0]
                            lots = strategies[0][1]
                            new_order = (percentage, lots)
                    else:
                        # initial sell
                        if completed_order[0] > 0:
                            lots = strategies[1][1]
                            new_price = float(exec_price - self.min_price_increment * Decimal(self.basic_points))
                            direction = OrderDirection.ORDER_DIRECTION_BUY
                            new_order = (new_price, lots, direction)
                        # initial buy
                        else:
                            lots = strategies[0][1]
                            new_price = float(exec_price + self.min_price_increment * Decimal(self.basic_points))
                            direction = OrderDirection.ORDER_DIRECTION_SELL
                            new_order = (new_price, lots, direction)
                        
                    reverse = (not reverse)                
                    new_task = asyncio.create_task(self.handle_strat_order(new_order, reverse))
                    self.tasks.append(new_task)

        print('Closing the session!')

        
    async def start(self):
        if self.account_id is None:
            try:
                # self.account_id = (await self.client.get_accounts()).accounts.pop().id
                accounts = (await self.client.get_accounts()).accounts
                if len(accounts) != 0:
                    for account in accounts:
                        # print(f"Closing old accounts...")
                        await self.client.close_sandbox_account(account.id)
                # print(f"Opening new account...")
                self.account_id = (await self.client.open_sandbox_account()).account_id

            except InvestError as error:
                print(f"Error taking account id. Stopping strategy. {error}")
                return
        await self.main_cycle()

