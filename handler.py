import asyncio

from TBankClient import TBankClient
from SQLClient import OrderSQLiteClient

from tinkoff.invest import OrderExecutionReportStatus
from tinkoff.invest.exceptions import InvestError
from tinkoff.invest.utils import quotation_to_decimal
# from Blogger import Blogger

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

    async def handle_new_order(self, order_id, account_id, exec_price):

        try:
            order_state = await self.broker_client.get_order_state(
                order_id=order_id,
                account_id=account_id
            )   
        except InvestError as error:
            # self.blogger.failed_to_post_order_message(order_id)
            print(f'Failed to post order: {order_id}')
            return
        
        self.sql_orders_client.add_order(
            order_id=order_id,
            figi=order_state.figi,
            order_direction=str(order_state.direction),
            price=exec_price,
            quantity=order_state.lots_requested,
            status=str(order_state.execution_report_status)
        )

        # self.blogger.posted_order_message(order_id)
        print(f'Posted order: {order_id}')

        while order_state.execution_report_status not in FINAL_ORDER_STATUSES:
            await asyncio.sleep(self.check_interval)
            try:
                order_state = await self.broker_client.get_order_state(
                    order_id=order_id,
                    account_id=account_id
                )  
                last_price = (await self.broker_client.get_last_prices(figi=[order_state.figi])).last_prices.pop().price
                # self.blogger.order_status_message(
                #     str(order_state.direction.name), 
                #     exec_price, 
                #     str(order_state.execution_report_status.name) ,
                #     float(quotation_to_decimal(last_price))
                #     )
                # print(f'Order: { str(order_state.direction.name)} {exec_price} {str(order_state.execution_report_status.name)}'
                #       f' | Last price={float(quotation_to_decimal(last_price))}')
            except InvestError as error:
                print(f'Failed to get order {order_id} state. Skipping...')
                # self.blogger.failed_to_get_order_status_message(order_id)
        
        self.sql_orders_client.update_order_status(
            order_id=order_id, status=str(order_state.execution_report_status)
        )

        print(f'\nClosed Order: {str(order_state.direction)} {exec_price} {str(order_state.execution_report_status.name)}\n')
        # self.blogger.order_closed_message(
        #     str(order_state.direction),
        #     exec_price,
        #     str(order_state.execution_report_status.name)
        #     )