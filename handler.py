import asyncio

from TBankClient import TBankClient
from SQLClient import OrderSQLiteClient, LastPricesSQLiteClient
from datetime import datetime

from tinkoff.invest import OrderExecutionReportStatus
from tinkoff.invest.exceptions import InvestError
from tinkoff.invest.utils import quotation_to_decimal
from decimal import Decimal
# from Blogger import Blogger
from Errors import Errors

FINAL_ORDER_STATUSES = [
    OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_CANCELLED,
    OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_REJECTED,
    OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_FILL,
]


class OrderHandler():

    def __init__(self, client, blogger, prices_logger, check_interval):
        self.broker_client : TBankClient = client
        self.sql_orders_client = OrderSQLiteClient()
        self.prices_logger : LastPricesSQLiteClient = prices_logger
        self.blogger = blogger
        self.check_interval = check_interval

    async def handle_new_order(self, order_id, account_id, exec_price, lot_size):

        try:
            order_state = await self.broker_client.get_order_state(
                order_id=order_id,
                account_id=account_id
            )   
        except InvestError as error:
            print(f'Failed to handle order: {order_id}')
            return Errors.FAILED_TO_HANDLE_ORDER
        
        self.sql_orders_client.add_order(
            order_id=order_id,
            ticker='SBER',
            order_direction=str(order_state.direction),
            price=exec_price,
            quantity=order_state.lots_requested,
            status=str(order_state.execution_report_status),
            exec_price=-1,
            timestamp=datetime.now().strftime('%F %T.%f')
        )

        print(f'Posted order: {str(order_state.direction.name)} for {exec_price}')

        while order_state.execution_report_status not in FINAL_ORDER_STATUSES:
            await asyncio.sleep(self.check_interval)
            try:
                order_state = await self.broker_client.get_order_state(
                    order_id=order_id,
                    account_id=account_id
                )  
                self.sql_orders_client.update_order_status(
                    order_id, 
                    str(order_state.execution_report_status), 
                    datetime.now().strftime('%F %T.%f')
                    )
                last_price = float(
                    quotation_to_decimal(
                        (await self.broker_client.get_last_prices(figi=[order_state.figi]))
                        .last_prices.pop().price
                        )
                    )
                
                self.prices_logger.add_price('SBER', datetime.now().strftime('%F %T.%f'), last_price)
            except InvestError as error:
                print(f'Failed to get order {order_id} state. Skipping...')
        
        real_exec_price = quotation_to_decimal(order_state.executed_order_price) / lot_size
        commission = quotation_to_decimal(order_state.executed_commission)

        self.sql_orders_client.update_order_status(
                    order_id, 
                    str(order_state.execution_report_status), 
                    datetime.now().strftime('%F %T.%f')
                    )
        self.sql_orders_client.update_order_exec_price(
                    order_id, 
                    float(real_exec_price), 
                    datetime.now().strftime('%F %T.%f')
                    )

        print(f'Closed Order: {str(order_state.direction.name)} {exec_price} '
              f'for {float(real_exec_price)} with commission {float(commission):.2f}\n')
        
        return real_exec_price, commission