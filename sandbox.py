import os, sys
import datetime
import asyncio
import time
from datetime import timedelta, date
from dotenv import load_dotenv, dotenv_values
import pandas as pd
from decimal import Decimal
from lightweight_charts import Chart
import uuid

from tinkoff.invest import (
    Client,
    CandleInterval,
    MoneyValue,
    InstrumentIdType,
    OrderDirection,
    OrderType,
)
from tinkoff.invest.constants import INVEST_GRPC_API_SANDBOX, INVEST_GRPC_API
from tinkoff.invest.utils import now, decimal_to_quotation, quotation_to_decimal
from tinkoff.invest.exceptions import InvestError
from tinkoff.invest.sandbox.client import SandboxClient


class Trader():

    def __init__(self, token, account_id, sandbox = True):
        self.token = token
        self.account_id = account_id
        self.target = INVEST_GRPC_API if sandbox else INVEST_GRPC_API_SANDBOX
        self.strategy = None
        

    def get_trading_status(self, figi): 
        with SandboxClient(token=self.token, target=self.target ) as client:
            return client.market_data.get_trading_status(figi=figi).market_order_available_flag
        
    def get_portfolio_amount(self):
        with SandboxClient(token=self.token, target=self.target ) as client:
            return float(quotation_to_decimal(client.operations.get_portfolio(account_id=self.account_id).total_amount_portfolio))
        
    def get_positions(self):
        with SandboxClient(token=self.token, target=self.target) as client:
            return client.operations.get_positions(account_id=self.account_id)
                
    def get_withdraw_limit(self):
        with SandboxClient(token=self.token, target=self.target ) as client:
            return client.operations.get_withdraw_limits(account_id=self.account_id).money
        
    def get_operations(self, n_days):
        with SandboxClient(token=self.token, target=self.target ) as client:
            operatios = \
                client.operations.get_operations(account_id=self.account_id, from_=now()-timedelta(days=n_days), to=now()).operations
            return operatios
        
    def get_lot_size(self, figi):
        with SandboxClient(token=self.token, target=self.target) as client:
            lot_size = client.instruments.share_by(id_type=InstrumentIdType(1), id=figi).instrument.lot
            return lot_size

    def get_last_close_price(self, figi):

        with SandboxClient(token=self.token, target=self.target) as client:
            close_price_quot = list(client.get_all_candles(
                    figi=figi,
                    from_=now() - timedelta(days=1),
                    interval=CandleInterval.CANDLE_INTERVAL_DAY,
                ))[0].close
            close_price = float(quotation_to_decimal(close_price_quot))
                
        return close_price

    def get_orders(self):
        with SandboxClient(token=self.token, target=self.target ) as client:
            return client.orders.get_orders(account_id=self.account_id).orders

    def load_candles(self, ticker, window_size = 30, interval = CandleInterval.CANDLE_INTERVAL_DAY):

        _dict = {
            'date': [], 
            'open': [], 
            'high': [],
            'low': [], 
            'close': [],
            'volume': []
        } 

        figi = self.get_ticker_figi(ticker)

        with SandboxClient(token=self.token, target=self.target) as client:
            for candle in list(client.get_all_candles(
                    figi=figi,
                    from_=now() - timedelta(days=window_size),
                    interval=interval,
                )):
                    _dict["date"].append(date(candle.time.year, candle.time.month, candle.time.day))
                    _dict["volume"].append(candle.volume)
                    _dict["open"].append(float(quotation_to_decimal(candle.open)))
                    _dict["high"].append(float(quotation_to_decimal(candle.high)))
                    _dict["low"].append(float(quotation_to_decimal(candle.low)))
                    _dict["close"].append(float(quotation_to_decimal(candle.close)))
                
        return pd.DataFrame(_dict)  

    def plot_candles(self, ticker, candles: pd.DataFrame):

            chart = Chart()
            chart.layout(background_color='#1E2C39', text_color='#9babba', font_size=12,
                        font_family='Helvetica')
            chart.grid(color='#233240')
            chart.candle_style(up_color='#14835C', down_color='#9D2B38',
                            border_up_color='#0ad18b', border_down_color='#d62035',
                            wick_up_color='#0ad18b', wick_down_color='#d62035')
            chart.volume_config(up_color='#185c4d', down_color='#652b38')
            chart.crosshair(mode='normal', vert_width=1, vert_color='#9babba', vert_style='dotted',
                            horz_color='#9babba', horz_width=1, horz_style='dotted')
            chart.legend(visible=True, color_based_on_candle=True, font_size=16)
            
            chart.topbar.textbox('symbol', ticker)

            chart.set(candles)
            chart.show(block=True)

    def read_strategy(self, filename, sheet_name):
        self.strategy = pd.read_excel(
            filename, 
            sheet_name=sheet_name, 
            header=0, 
            dtype={
                'Ticker': str,
                'Percentage': float,
                'Lots': int
                }
            )

    def show_strategy(self):
        print("Strategy:")
        print(self.strategy)
        print()
        print("-"*60)
        print()

    def get_ticker_figi(self, ticker):
        with SandboxClient(token=self.token, target=self.target) as client:
            for share in list(client.instruments.shares(instrument_status=1).instruments):
                if share.ticker == ticker:
                    return share.figi
        raise ValueError('Ticker not found!')

    def place_limit_orders(self):
        
        for i in range(self.strategy.shape[0]):

            ticker = self.strategy.iloc[i][0]
            percentage = self.strategy.iloc[i][1]
            lots = self.strategy.iloc[i][2]

            print(f'Placing order #{i}: {ticker} / {percentage} / {lots}', end=" <--- ")

            figi = self.get_ticker_figi(ticker)
            close_price = Decimal(self.get_last_close_price(figi) * (1 + percentage))

            order_type = OrderType.ORDER_TYPE_LIMIT
            order_direction = OrderDirection.ORDER_DIRECTION_BUY if percentage < 0 else OrderDirection.ORDER_DIRECTION_SELL
            order_direction_str = "Short" if percentage < 0 else "Long"
            order_imp_id = str(uuid.uuid4())

            with SandboxClient(token=self.token, target=self.target) as client:
                min_price_increment = client.instruments.get_instrument_by(
                id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI, id=figi
                ).instrument.min_price_increment

                number_digits_after_point = 9 - len(str(min_price_increment.nano)) + 1
                min_price_increment = quotation_to_decimal(min_price_increment)
                exec_price = (round(close_price / min_price_increment) * min_price_increment)
                
                try:
                    order_response = client.orders.post_order(
                        figi=figi,
                        quantity=lots,
                        price=decimal_to_quotation(Decimal(exec_price)),
                        direction=order_direction,
                        account_id=self.account_id,
                        order_type=order_type,
                        order_id=order_imp_id, # for uniqueness
                        instrument_id=figi
                    )

                    order_status = order_response.execution_report_status.value
                    order_id = order_response.order_id

                    with open("orders.txt", "a") as file:
                        file.write(f'{ticker} {order_direction_str} {exec_price} {lots} {order_id} {order_status}\n')

                    print("Done")
            
                except InvestError as error:
                    print("Failed\n")
                    print(f"Failed ({error})\n")

    def show_all_orders(self):
        print()
        print("All Orders:")
        print("-"*60)
        with open("orders.txt", "r") as file:
            data = file.readlines()
            for order in data:
                print(order)
        print("-"*60)
        print()

    def ticker_by_figi(self, figi):
        with SandboxClient(token=self.token, target=self.target) as client:
            return client.instruments.find_instrument(query=figi).instruments[0].ticker

    def get_order_state(self, order_id):
        with SandboxClient(token=self.token, target=self.target) as client:
            print(client.orders.get_order_state(account_id=self.account_id, order_id=order_id))
    
    def cancel_active_orders(self):
        new_data = ""
        with SandboxClient(token=self.token, target=self.target) as client:
            with open("orders.txt", "r") as file:
                data = file.readlines()
                for order in data:
                    order_status = order.split()[-1]
                    if order_status != '1':
                        order_id = order.split()[-2]
                        client.sandbox.cancel_sandbox_order(account_id=self.account_id, order_id =order_id)
                    else:
                        new_data += order
        
        with open('orders.txt', 'w') as file:
            file.write(new_data)

    def info(self):

        print()
        print("-"*60)
        print(f'Trader Account Information')
        print("-"*60)

        print("1. Positions:")
        positions = self.get_positions()

        print(f'\tMoney')
        print(f'\t\t{float(quotation_to_decimal(positions.money[0])):.2f}') # currency positions list

        print(f'\tBlocked')
        print(f'\t\t{float(quotation_to_decimal(positions.blocked[0]))}') # blocked currency positions list

        print(f'\tSecurities')
        for sec in positions.securities:
            sec_name = self.ticker_by_figi(sec.figi)
            print(f'\t\tTicker: {sec_name} | Blocked: {sec.blocked} | Balance: {sec.balance} | Type: {sec.instrument_type}')

        print("\n2. Active Orders:")
        for order in self.get_orders():
            print(f'\tType: {"long" if order.direction == 1 else "short"}'
                f' | Price: {float(quotation_to_decimal(order.initial_security_price)):.2f}'
                f' | Lots: {order.lots_requested}')

        print()
        print("-"*60)
        print()

    def open_account(self):
        with SandboxClient(token=self.token, target=self.target) as client:
            self.account_id = client.sandbox.open_sandbox_account().account_id
            print(self.account_id)

    def close_account(self):
        with SandboxClient(token=self.token, target=self.target) as client:
            client.sandbox.close_sandbox_account(account_id=self.account_id)
            open("orders.txt", "w").close()

    def add_money(self, amount, currency = "rub"):
        with SandboxClient(token=self.token, target=self.target) as client:
            try:
                amount_quot = decimal_to_quotation(Decimal(amount))
                amount_mv = MoneyValue(units=amount_quot.units, nano=amount_quot.nano, currency=currency)
                balance_quot = client.sandbox.sandbox_pay_in(account_id=self.account_id, amount=amount_mv).balance
                balance = float(quotation_to_decimal(balance_quot))
                print(f'[+] Added: {amount}')
                print(f'[=] Current balance: {balance}')
            except InvestError as error:
                print(f"\nPay in [{amount}] failed. \nException: {error}\n")


if __name__ == '__main__':

    config = dotenv_values(".env")
    TOKEN = config['TINKOFF_TOKEN_SANDBOX']
    ACCOUNT_ID = config['TINKOFF_SANDBOX_ACCOUNT']  

    # with SandboxClient(TOKEN) as client:
    #     response = client.users.get_accounts()
    #     accounts = [account.id for account in response.accounts]
    #     for response in client.operations_stream.positions_stream(accounts=accounts):
    #         print(response.subscriptions.accounts[0]) 

    trader = Trader(token=TOKEN, account_id=ACCOUNT_ID, sandbox=True)

    trader.info()

    trader.read_strategy(filename="strategy.xlsx", sheet_name="strategy")

    # trader.place_limit_orders()
    trader.show_all_orders()

    # trader.cancel_active_orders()
    
    



    

