import os, sys
from dotenv import dotenv_values
import asyncio
from datetime import timedelta
from uuid import uuid4
from decimal import Decimal
import pandas as pd
import time

from tinkoff.invest import (
    AsyncClient,
    InstrumentIdType,
    CandleInterval,
    MoneyValue
)
from tinkoff.invest.utils import now, decimal_to_quotation, quotation_to_decimal
from tinkoff.invest.exceptions import InvestError


class TBankClient:

    def __init__(self, token, app_name, sandbox = False):
        self.token = token
        self.app_name = app_name
        self.sandbox = sandbox
        self.client = None

    async def ainit(self):
        self.client = await AsyncClient(token=self.token, app_name=self.app_name).__aenter__()

    async def get_orders(self, account_id):
        if self.sandbox:
            return await self.client.sandbox.get_sandbox_orders(account_id=account_id).orders
        return await self.client.orders.get_orders(account_id=account_id).orders

    async def get_portfolio(self, account_id):
        if self.sandbox:
            return await self.client.sandbox.get_sandbox_portfolio(account_id=account_id)
        return await self.client.operations.get_portfolio(account_id=account_id)

    async def get_accounts(self):
        if self.sandbox:
            return await self.client.sandbox.get_sandbox_accounts()
        return await self.client.users.get_accounts()
    
    async def get_trading_status(self, figi):
        return await self.client.market_data.get_trading_status(figi=figi)

    async def get_instrument_by(self, id_type : InstrumentIdType, id):
        return await self.client.instruments.get_instrument_by(id_type=id_type, id=id)
    
    async def get_positions(self, account_id):
        if self.sandbox:
            return await self.client.sandbox.get_sandbox_positions(account_id=account_id)
        return await self.client.operations.get_positions(account_id=self.account_id)
    
    async def get_lot_size(self, figi):
        return await self.client.instruments.share_by(id_type=InstrumentIdType(1), id=figi).instrument.lot
    
    async def get_last_close_price(self, figi): # in-built method returns wrong value (TODO: investigate)
        close_price_quot = list(
            await self.client.get_all_candles(
                figi=figi,
                from_=now() - timedelta(days=1),
                interval=CandleInterval.CANDLE_INTERVAL_DAY,
            ))[0].close
        close_price = float(quotation_to_decimal(close_price_quot))    
        return close_price
    
    async def get_figi_by_ticker(self, ticker): # refactor using GetInstrument
        for share in list( await self.client.instruments.shares(instrument_status=1).instruments ):
            if share.ticker == ticker:
                return share.figi
        raise ValueError('Ticker not found!')
    
    async def ticker_by_figi(self, figi):
        return await self.client.instruments.find_instrument(query=figi).instruments[0].ticker
    
    async def print_positions(self, account_id):

        print("• Positions:")
        positions = await self.get_positions(account_id=account_id)
        print(f'\t- Money')
        print(f'\t\t{float(quotation_to_decimal(positions.money[0])):.2f}')
        print(f'\t- Blocked')
        print(f'\t\t{float(quotation_to_decimal(positions.blocked[0]))}')
        print(f'\t- Securities')
        for sec in positions.securities:
            sec_name = self.ticker_by_figi(sec.figi)
            print(f'\t\t‣ Ticker: {sec_name} | Blocked: {sec.blocked} | Balance: {sec.balance} | Type: {sec.instrument_type}')

    async def account_info(self, account_id):

        print()
        print("-"*60)
        print(f'Account Information')
        print("-"*60)
        await self.positions_info(account_id=account_id)
        print()
        print("-"*60)
        print("-"*60)
        print()

    async def open_sandbox_account(self):
        return await self.client.sandbox.open_sandbox_account().account_id
    
    async def close_sandbox_account(self, account_id): # (TODO: add account related database removal)
        await self.client.sandbox.close_sandbox_account(account_id=account_id)
    
    async def add_money_to_sandbox_account(self, account_id, amount, currency = "rub"):
        amount_quot = decimal_to_quotation(Decimal(amount))
        amount_mv = MoneyValue(units=amount_quot.units, nano=amount_quot.nano, currency=currency)
        balance_quot = await self.client.sandbox.sandbox_pay_in(account_id=account_id, amount=amount_mv).balance
        balance = float(quotation_to_decimal(balance_quot))
        print(f'[+] Added: {amount}')
        print(f'[=] Current balance: {balance}')

    async def post_order(self, figi, quantity, price, direction, account_id, order_type, order_id, instrument_id):
        if self.sandbox:
            return await self.client.sandbox.post_sandbox_order(
                figi=figi,
                quantity=quantity,
                price=price,
                direction=direction,
                account_id=account_id,
                order_type=order_type,
                order_id=order_id,
                instrument_id=instrument_id
            )
        return await self.client.orders.post_order(
            figi=figi,
            quantity=quantity,
            price=price,
            direction=direction,
            account_id=account_id,
            order_type=order_type,
            order_id=order_id,
            instrument_id=instrument_id
            )
    
    async def get_order_state(self, account_id, order_id):
        if self.sandbox:
            return await self.client.sandbox.get_sandbox_order_state(account_id=account_id, order_id=order_id)
        return await self.client.orders.get_order_state(account_id=account_id, order_id=order_id)

    
# ----------------------------------------------------------------------------------------------


async def test():

    config = dotenv_values(".env")
    TOKEN = config['TINKOFF_TOKEN_SANDBOX']

    client = TBankClient(token=TOKEN, sandbox=True)

    await client.ainit()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(loop.create_task(test()))