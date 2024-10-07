import asyncio

class Blogger:
    """
    Class formats and sends messages to telegram chat.
    """
    def __init__(self, messages_queue):
        self.__messages_queue : asyncio.Queue = messages_queue

    def __send_text_message(self, text: str):
        try:
            # print(f"Put message to telegram messages queue: {text}")
            self.__messages_queue.put_nowait(text)
        except Exception as ex:
            print(f"Error put message to telegram messages queue: {repr(ex)}")

    def start_trading_message(self):
        self.__send_text_message("Opening the session!")

    def posting_initial_orders_message(self):
        self.__send_text_message("Posting initial orders...")

    def posted_order_message(self, order_id):
        self.__send_text_message(f'Posted order {order_id}')

    def failed_to_post_order_message(self, order_id):
        self.__send_text_message(f'Failed to post order {order_id}.')

    def order_status_message(self, direction, exec_price, status, last_price):
        self.__send_text_message(f'Order: {direction} {exec_price} {status} | Last price={last_price}')

    def failed_to_get_order_status_message(self, order_id):
        self.__send_text_message(f'Failed to get order {order_id} state. Skipping...')

    def order_closed_message(self, direction, exec_price, status):
        self.__send_text_message(f'Closed Order: {direction} {exec_price} {status}')

    def active_orders_message(self, n_orders):
        self.__send_text_message(f"Active Orders: {n_orders}")

    def failed_to_get_active_orders_message(self):
        self.__send_text_message(f'Unaible to get acrive orders.')

    def ticker_trading_closed_message(self, ticker):
        self.__send_text_message(f'Ticker {ticker} trading closed')

    def list_initial_orders_message(self, orders):
        message = "Starting Orders:\n\n"
        for order in orders:
            message += f"Ticker: {order[0]}, Perc: {order[1]:.2%}, Lots: {order[2]}\n"
        self.__send_text_message(message)
                                 
    def close_session_message(self):
        self.__messages_queue.put_nowait("Closing the session!")
        self.__messages_queue.put_nowait("close session")

    # def finish_trading_message(self) -> None:
    #     """
    #     The method sends information that trading is stopping.
    #     """
    #     if self.__blog_status:
    #         self.__send_text_message("We are closing trading day.")

    # def close_position_message(self, trade_order: TradeOrder) -> None:
    #     """
    #     The method sends information about closed position.
    #     """
    #     if self.__blog_status and trade_order:
    #         signal_type = Blogger.__signal_type_to_message_test(trade_order.signal.signal_type)
    #         self.__send_text_message(
    #             f"{self.__trade_strategies[trade_order.signal.figi].ticker} position {signal_type} has been closed."
    #         )

    # def open_position_message(self, trade_order: TradeOrder) -> None:
    #     """
    #     The method sends information about opened position.
    #     """
    #     if self.__blog_status and trade_order:
    #         signal_type = Blogger.__signal_type_to_message_test(trade_order.signal.signal_type)
    #         self.__send_text_message(
    #             f"{self.__trade_strategies[trade_order.signal.figi].ticker} position {signal_type} has been opened. "
    #             f"Take profit level: {trade_order.signal.take_profit_level:.2f}. "
    #             f"Stop loss level: {trade_order.signal.stop_loss_level:.2f}."
    #         )

    # def trading_depo_summary_message(
    #         self,
    #         rub_before_trade_day: Decimal,
    #         current_rub_on_depo: Decimal
    # ) -> None:
    #     """
    #     The method sends information about trading day summary.
    #     """
    #     if self.__blog_status:
    #         self.__send_text_message(
    #             f"Start depo: {rub_before_trade_day:.2f} close depo:{current_rub_on_depo:.2f}."
    #         )

    #         today_profit = current_rub_on_depo - rub_before_trade_day
    #         today_percent_profit = (today_profit / rub_before_trade_day) * 100
    #         self.__send_text_message(f"Today leverage: {today_profit:.2f} rub ({today_percent_profit:.2f} %)")

    # def fail_message(self):
    #     """
    #     The method sends information about emergency situation in bot.
    #     """
    #     if self.__blog_status:
    #         self.__send_text_message(
    #             f"Something went wrong. We are trying to close all positions. "
    #             f"If we fail, please try to do it himself."
    #         )

    # def summary_message(self):
    #     """
    #     The method sends just summary title.
    #     """
    #     if self.__blog_status:
    #         self.__send_text_message(f"Trading day summary:")

    # def final_message(self):
    #     """
    #     The method sends just goodbye title.
    #     """
    #     if self.__blog_status:
    #         self.__send_text_message(f"Trading has been completed. See you on next trade day!")

    # def summary_open_signal_message(self, trade_order: TradeOrder, open_order_state: OrderState):
    #     """
    #     The method sends summary information about only open positions (not closed)
    #     """
    #     if self.__blog_status:
    #         signal_type = Blogger.__signal_type_to_message_test(trade_order.signal.signal_type)
    #         summary_commission = moneyvalue_to_decimal(open_order_state.executed_commission) + \
    #                              moneyvalue_to_decimal(open_order_state.service_commission)
    #         self.__send_text_message(
    #             f"Open {signal_type} position for {self.__trade_strategies[trade_order.signal.figi].ticker}. "
    #             f"Lots executed: {open_order_state.lots_executed}. "
    #             f"Average price: "
    #             f"{moneyvalue_to_decimal(open_order_state.average_position_price):.2f}. "
    #             f"Total order price: "
    #             f"{moneyvalue_to_decimal(open_order_state.total_order_amount):.2f}. "
    #             f"Total commissions: "
    #             f"{summary_commission:.2f}. "
    #             f"You have to close position manually."
    #         )

    # def summary_closed_signal_message(self,
    #                                   trade_order: TradeOrder,
    #                                   open_order_state: OrderState,
    #                                   close_order_state: OrderState
    #                                   ) -> None:
    #     """
    #     The method sends summary information about closed positions
    #     """
    #     if self.__blog_status:
    #         signal_type = Blogger.__signal_type_to_message_test(trade_order.signal.signal_type)
    #         summary_commission = moneyvalue_to_decimal(open_order_state.executed_commission) + \
    #                              moneyvalue_to_decimal(open_order_state.service_commission) + \
    #                              moneyvalue_to_decimal(close_order_state.executed_commission) + \
    #                              moneyvalue_to_decimal(close_order_state.service_commission)
    #         self.__send_text_message(
    #             f"Close {signal_type} position for {self.__trade_strategies[trade_order.signal.figi].ticker}. "
    #             f"Lots executed: {close_order_state.lots_executed}. "
    #             f"Average open price: "
    #             f"{moneyvalue_to_decimal(open_order_state.average_position_price):.2f}. "
    #             f"Average close price: "
    #             f"{moneyvalue_to_decimal(close_order_state.average_position_price):.2f}. "
    #             f"Summary: "
    #             f"{moneyvalue_to_decimal(close_order_state.total_order_amount) - moneyvalue_to_decimal(open_order_state.total_order_amount):.2f}. "
    #             f"Total commissions: "
    #             f"{summary_commission:.2f}."
    #         )

    # @staticmethod
    # def __signal_type_to_message_test(signal_type: SignalType) -> str:
    #     return "long" if signal_type == SignalType.LONG else "short"