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

    def close_price_message(self, ticker, price):
        self.__send_text_message(f"Close price of {ticker} was {price}")

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

    def last_price_message(self, ticker, price):
        self.__send_text_message(f"Last price of {ticker} was {price}")

    def failed_to_get_last_price_message(self, ticker):
        self.__send_text_message(f'Failed to get last price for {ticker}.')

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

