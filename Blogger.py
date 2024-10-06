import asyncio

class Blogger:
    """
    Class formats and sends messages to telegram chat.
    """
    def __init__(self, messages_queue):
        self.__messages_queue : asyncio.Queue = messages_queue

    def __send_text_message(self, text: str):
        try:
            print(f"Put message to telegram messages queue: {text}")
            self.__messages_queue.put_nowait(text)
        except Exception as ex:
            print(f"Error put message to telegram messages queue: {repr(ex)}")

    def start_trading_message(self):
        self.__send_text_message("Opening the session!")

    def initial_orders_message(self, orders):
        print('HERE')
        message = "Starting Orders:\n\n"
        for order in orders:
            message += f"Ticker : {order[0]}, Percentage : {order[1]:.4f}, Lots : {order[2]}\n"
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