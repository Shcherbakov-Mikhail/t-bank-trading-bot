import asyncio

from TBankClient import TBankClient
from SQLClient import OrderSQLiteClient

from tinkoff.invest import OrderExecutionReportStatus
from tinkoff.invest.exceptions import InvestError
from tinkoff.invest.utils import quotation_to_decimal

FINAL_ORDER_STATUSES = [
    OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_CANCELLED,
    OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_REJECTED,
    OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_FILL,
]


class OrderHandler():

    def __init__(self, client):
        self.broker_client : TBankClient = client
        self.sql_orders_client = OrderSQLiteClient()

    async def handle_new_order(self, order_id, account_id, exec_price):

        try:
            order_state = await self.broker_client.get_order_state(
                order_id=order_id,
                account_id=account_id
            )   
        except InvestError as error:
            print(f'Failed to get order {order_id} state. \nError: {error}')
            return
        
        self.sql_orders_client.add_order(
            order_id=order_id,
            figi=order_state.figi,
            order_direction=str(order_state.direction),
            price=exec_price,
            quantity=order_state.lots_requested,
            status=str(order_state.execution_report_status)
        )

        print(f'Added order {str(order_state.direction)}')

        while order_state.execution_report_status not in FINAL_ORDER_STATUSES:
            await asyncio.sleep(10)
            try:
                order_state = await self.broker_client.get_order_state(
                    order_id=order_id,
                    account_id=account_id
                )  
                print(f'Order: {str(order_state.direction.name)} {exec_price} {str(order_state.execution_report_status.name)}', end="")
                last_price = (await self.broker_client.get_last_prices(figi=[order_state.figi])).last_prices.pop().price
                print(f' | Last price={float(quotation_to_decimal(last_price))}')
            except InvestError as error:
                print(f'Failed to get order {order_id} state. Skipping...')
        
        self.sql_orders_client.update_order_status(
            order_id=order_id, status=str(order_state.execution_report_status)
        )

        print(f'Closed Order: {str(order_state.direction)} {exec_price} {str(order_state.execution_report_status.name)}')