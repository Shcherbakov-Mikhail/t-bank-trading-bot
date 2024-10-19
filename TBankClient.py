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
    MoneyValue,
    OrderDirection,
    OrderType,
    InstrumentClosePriceRequest,
    
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
            return await self.client.sandbox.get_sandbox_orders(account_id=account_id)
        return await self.client.orders.get_orders(account_id=account_id)

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
        return await self.client.operations.get_positions(account_id=account_id)
    
    # TODO: move to Strategy 
    async def get_lot_size(self, figi): 
        return (await self.client.instruments.share_by(id_type=InstrumentIdType(1), id=figi)).instrument.lot
    
    # TODO: move to Strategy
    async def get_figi_by_ticker(self, ticker): # refactor using GetInstrument
        for share in list( (await self.client.instruments.shares(instrument_status=1)).instruments ):
            if share.ticker == ticker:
                return share.figi
        raise ValueError('Ticker not found!')
    
    # TODO: move to Strategy 
    async def ticker_by_figi(self, figi):
        return (await self.client.instruments.find_instrument(query=figi)).instruments[0].ticker
    
    async def get_close_price(self, figi):
        instrument = (await self.client.instruments.find_instrument(query=figi)).instruments.pop().uid
        price = (await self.client.market_data.get_close_prices(instruments=[InstrumentClosePriceRequest(instrument)])).close_prices.pop().price
        return float(quotation_to_decimal(price))
    
    async def print_positions(self, account_id): 

        print("• Positions:")
        positions = await self.get_positions(account_id=account_id)
        print(f'\t- Money')
        print(f'\t\t{float(quotation_to_decimal(positions.money[0])):.2f}')
        print(f'\t- Blocked')
        print(f'\t\t{float(quotation_to_decimal(positions.blocked[0]))}')
        print(f'\t- Securities')
        for sec in positions.securities:
            sec_name = (await self.ticker_by_figi(sec.figi))
            print(f'\t\t‣ Ticker: {sec_name} | Blocked: {sec.blocked} | Balance: {sec.balance} | Type: {sec.instrument_type}')

    async def account_info(self, account_id): 

        print()
        print("-"*60)
        print(f'Account Information')
        print("-"*60)
        await self.print_positions(account_id=account_id)
        print()
        print("-"*60)
        print("-"*60)
        print()

    async def open_sandbox_account(self): 
        return await self.client.sandbox.open_sandbox_account()
    
    async def close_sandbox_account(self, account_id): # (TODO: add account related database removal)
        await self.client.sandbox.close_sandbox_account(account_id=account_id)
    
    async def add_money_to_sandbox_account(self, account_id, amount, currency = "rub"):
        amount_quot = decimal_to_quotation(Decimal(amount))
        amount_mv = MoneyValue(units=amount_quot.units, nano=amount_quot.nano, currency=currency)
        balance_quot = (await self.client.sandbox.sandbox_pay_in(account_id=account_id, amount=amount_mv)).balance
        balance = float(quotation_to_decimal(balance_quot))
        print(f'Added: {amount}. Current balance: {balance}')

    async def get_last_prices(self, figi):
        return await self.client.market_data.get_last_prices(figi=figi)

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