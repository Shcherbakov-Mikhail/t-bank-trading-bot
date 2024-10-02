import os, sys
import datetime
import asyncio
import time
from datetime import timedelta, date
from dotenv import load_dotenv
import pandas as pd
from decimal import Decimal
from lightweight_charts import Chart

from tinkoff.invest import (
    Client,
    CandleInterval,
    MoneyValue
)
from tinkoff.invest.constants import INVEST_GRPC_API_SANDBOX, INVEST_GRPC_API
from tinkoff.invest.utils import now, decimal_to_quotation, quotation_to_decimal
from tinkoff.invest.exceptions import InvestError
from tinkoff.invest.sandbox.client import SandboxClient



class Trader():
    class_code: str
    figi: str
    ticker: str

    def __init__(self, token, ticker, account_id, sandbox = True):
        self.token = token
        self.account_id = account_id
        self.ticker = ticker
        self.target = INVEST_GRPC_API if sandbox else INVEST_GRPC_API_SANDBOX
        self.class_code, self.figi, self.name = self.set_ticker()

    def set_ticker(self):
        with Client(token=self.token, target=self.target) as client:
            for share in list(client.instruments.shares(instrument_status=1).instruments):
                if share.ticker == self.ticker:
                    return (share.class_code, share.figi, share.name)
        raise ValueError('Ticker not found!')

    def get_trading_status(self): 
        with SandboxClient(token=self.token, target=self.target ) as client:
            return client.market_data.get_trading_status(figi=self.figi).market_order_available_flag
        
    def get_portfolio_amount(self):
        with SandboxClient(token=self.token, target=self.target ) as client:
            return float(quotation_to_decimal(client.operations.get_portfolio(account_id=self.account_id).total_amount_portfolio))
        
    def get_positions(self):
        with SandboxClient(token=self.token, target=self.target ) as client:
            return client.operations.get_positions(account_id=self.account_id)
        
    def get_orders(self):
        with SandboxClient(token=self.token, target=self.target ) as client:
            return client.orders.get_orders(account_id=self.account_id).orders
        
    def get_withdraw_limit(self):
        with SandboxClient(token=self.token, target=self.target ) as client:
            return client.operations.get_withdraw_limits(account_id=self.account_id).money
        
    def get_operations(self, n_days):
        with SandboxClient(token=self.token, target=self.target ) as client:
            operatios = \
                client.operations.get_operations(account_id=self.account_id, from_=now()-timedelta(days=n_days), to=now()).operations
            return operatios
        
    def add_money(self, amount, currency = "rub"):
        with SandboxClient(token=self.token, target=self.target) as client:
            amount_quot = decimal_to_quotation(Decimal(amount))
            amount_mv = MoneyValue(units=amount_quot.units, nano=amount_quot.nano, currency=currency)
            balance_quot = client.sandbox.sandbox_pay_in(account_id=self.account_id, amount=amount_mv).balance
            balance = float(quotation_to_decimal(balance_quot))
            print(f'[+] Added: {amount}')
            print(f'[=] Current balance: {balance}')

    def load_candles(self, window_size = 30, interval = CandleInterval.CANDLE_INTERVAL_DAY):

        _dict = {
            'date': [], 
            'open': [], 
            'high': [],
            'low': [], 
            'close': [],
            'volume': []
        } 

        with SandboxClient(token=self.token, target=self.target) as client:
            for candle in list(client.get_all_candles(
                    figi=self.figi,
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

    def plot_candles(self, candles: pd.DataFrame):

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
            
            chart.topbar.textbox('symbol', self.ticker)

            chart.set(candles)
            chart.show(block=True)

    def info(self, show_operations):

        print()
        print("-"*60)
        print(f'Ticker: "{self.name}" ({self.ticker})')
        print("-"*60)

        if self.get_trading_status():
            print("\n1. Ticker is alailable to trade;")
        else:
            print("\n1. Ticker is NOT alailable to trade;")

        print("2. Positions:")
        positions = self.get_positions()
        for pos in positions.__dict__.keys():
            if pos != "limits_loading_in_progress":
                print(f'\t{pos}')
                print(f'\t\t{getattr(positions, pos)}')

        print("3. Orders:")
        print(f'\t{self.get_orders()}')

        print("4. Withdraw Limit:")
        print(f'\t{self.get_withdraw_limit()}')

        print()
        print("-"*60)

        if show_operations:
            print("\n5. Weekly Operations:")
            print(f'\t{self.get_operations(n_days=7)[0]}')
            print()
            print("-"*60)

    def __repr__(self):
        return f'\nTrading: "{self.name}" ({self.ticker})\n' 


if __name__ == '__main__':

    load_dotenv()
    TOKEN = os.getenv('TINKOFF_TOKEN_SANDBOX')
    ACCOUNT_ID = os.getenv('TINKOFF_SANDBOX_ACCOUNT')

    trader = Trader(token=TOKEN, ticker="GAZP", account_id=ACCOUNT_ID, sandbox=True)

    trader.info(show_operations=False)




    

