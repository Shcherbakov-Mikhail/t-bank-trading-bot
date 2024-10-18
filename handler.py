import asyncio

from TBankClient import TBankClient
from SQLClient import OrderSQLiteClient
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

    def __init__(self, client, blogger, check_interval):
        self.broker_client : TBankClient = client
        self.sql_orders_client = OrderSQLiteClient()
        self.blogger = blogger
        self.check_interval = check_interval

    async def handle_new_order(self, order_id, account_id, exec_price, lot_size):

        try:
            order_state = await self.broker_client.get_order_state(
                order_id=order_id,
                account_id=account_id
            )   
        except InvestError as error:
            print(f'Failed to handle order: {order_id} at {datetime.now().time()}')
            return Errors.FAILED_TO_HANDLE_ORDER
        
        self.sql_orders_client.add_order(
            order_id=order_id,
            figi=order_state.figi,
            order_direction=str(order_state.direction),
            price=exec_price,
            quantity=order_state.lots_requested,
            status=str(order_state.execution_report_status)
        )

        print(f'Posted order: {str(order_state.direction.name)} for {exec_price} at {datetime.now().time()}')

        while order_state.execution_report_status not in FINAL_ORDER_STATUSES:
            await asyncio.sleep(self.check_interval)
            try:
                order_state = await self.broker_client.get_order_state(
                    order_id=order_id,
                    account_id=account_id
                )  
            except InvestError as error:
                print(f'Failed to get order {order_id} state. Skipping...')
        
        self.sql_orders_client.update_order_status(
            order_id=order_id, status=str(order_state.execution_report_status)
        )

        print(f'Closed Order: {str(order_state.direction.name)} {exec_price} '
              f'for {float(quotation_to_decimal(order_state.executed_order_price))/lot_size} at {datetime.now().time()}\n')
        
        return quotation_to_decimal(order_state.executed_order_price) / lot_size