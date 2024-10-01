import os
import datetime
from datetime import timedelta, date
from dotenv import load_dotenv
import pandas as pd
from lightweight_charts import Chart

from tinkoff.invest import (
    Client,
    CandleInterval
)
from tinkoff.invest.constants import INVEST_GRPC_API_SANDBOX, INVEST_GRPC_API
from tinkoff.invest.utils import now, decimal_to_quotation, quotation_to_decimal
from tinkoff.invest.exceptions import InvestError



class Trader():
    """
    """

    def __init__(self, token, sandbox = True, account_id = None):
        self.token = token
        self.account_id = account_id
        self.target = INVEST_GRPC_API if sandbox else INVEST_GRPC_API_SANDBOX

    def load_candles(self, figi, window_size = 30, interval = CandleInterval.CANDLE_INTERVAL_DAY):

        _dict = {
            'date': [], 
            'open': [], 
            'high': [],
            'low': [], 
            'close': [],
            'volume': []
        } 

        with Client(token=self.token, target=self.target) as client:
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
    
    @staticmethod
    def plot_candles(ticket, candles: pd.DataFrame):
         
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
            
            chart.topbar.textbox('symbol', ticket)

            chart.set(candles)
            chart.show(block=True)
         


if __name__ == '__main__':

    load_dotenv()
    TOKEN = os.getenv('TINKOFF_TOKEN_SANDBOX')

    trader = Trader(token=TOKEN, sandbox=True)

    candles = trader.load_candles(figi="BBG004730RP0", window_size=365)
    print(candles)

    trader.plot_candles("GAZP", candles)



 