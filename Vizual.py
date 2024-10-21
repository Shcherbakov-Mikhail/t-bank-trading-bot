from SQLClient import LastPricesSQLiteClient, OrderSQLiteClient
from datetime import datetime
import matplotlib.pyplot as plt
from lightweight_charts import Chart
import time, sys
from dotenv import dotenv_values
from VizBlogger import BloggerClient
import asyncio

# def plot_candles(ticker, candles):
         
#     chart = Chart()
#     chart.layout(background_color='#1E2C39', text_color='#9babba', font_size=12, font_family='Helvetica')
#     chart.grid(color='#233240')
#     chart.candle_style(
#         up_color='#14835C', 
#         down_color='#9D2B38',
#         border_up_color='#0ad18b', 
#         border_down_color='#d62035',
#         wick_up_color='#0ad18b', 
#         wick_down_color='#d62035'
#         )
#     chart.volume_config(
#         up_color='#185c4d', 
#         down_color='#652b38'
#         )
#     chart.crosshair(
#         mode='normal', 
#         vert_width=1, 
#         vert_color='#9babba', 
#         vert_style='dotted',
#         horz_color='#9babba', 
#         horz_width=1, 
#         horz_style='dotted'
#         )
#     chart.legend(
#         visible=True, 
#         color_based_on_candle=True, 
#         font_size=16
#         )    
#     chart.topbar.textbox('symbol', ticker)

#     line = chart.create_line('Price')
#     sma_data = calculate_sma(df, period=50)
#     line.set(sma_data)
    
#     chart.show(block=True)
    
async def main(blogger : BloggerClient, draw_delay=3, send_photo_delay=60, show_fig=False):
    prices_client = LastPricesSQLiteClient(debug=True)
    orders_client = OrderSQLiteClient(debug=True)   
    
    fig = plt.figure(figsize=(12, 6))
    
    if show_fig:
        plt.ion()
        fig.show()
    
    with open("init.txt", 'r') as file:
        data = file.read().split()
        start_price = float(data[0])
        upper_price = float(data[1])
        lower_price = float(data[2])
        
    send_photo_timer = 0
    
    while True:
        price_logs = prices_client.get_prices()
        # prices_tickers = [log[0] for log in price_logs]
        prices_timestamps = [datetime.strptime(log[1], '%Y-%m-%d %H:%M:%S.%f') for log in price_logs]
        prices = [log[2] for log in price_logs]

        compl_orders = [order for order in orders_client.get_orders() if order[6] != -1.0] # 'EXECUTION_REPORT_STATUS_FILL'
        # orders_tickers = [order[1] for order in compl_orders]
        # orders_directions = [order[2] for order in compl_orders]
        # orders_timestamps = [datetime.strptime(order[7], '%Y-%m-%d %H:%M:%S.%f') for order in compl_orders]
        # orders_exec_prices = [order[6] for order in compl_orders]

        compl_buy_orders = [order for order in compl_orders if order[2] == 'OrderDirection.ORDER_DIRECTION_BUY'] 
        buy_orders_timestamps = [datetime.strptime(order[7], '%Y-%m-%d %H:%M:%S.%f') for order in compl_buy_orders]
        buy_orders_exec_prices = [order[6] for order in compl_buy_orders]

        compl_sell_orders = [order for order in compl_orders if order[2] == 'OrderDirection.ORDER_DIRECTION_SELL'] 
        sell_orders_timestamps = [datetime.strptime(order[7], '%Y-%m-%d %H:%M:%S.%f') for order in compl_sell_orders]
        sell_orders_exec_prices = [order[6] for order in compl_sell_orders]
        
        price_change_to_start = (prices[-1] - start_price) / start_price
        price_change_to_start_sign = '+' if price_change_to_start >= 0 else '-'

        plt.plot(prices_timestamps, prices, color='b', label='price')
        if len(compl_orders) > 0:
            plt.scatter(buy_orders_timestamps, buy_orders_exec_prices, color='red', marker='o', label='buy order')
            plt.scatter(sell_orders_timestamps, sell_orders_exec_prices, color='green', marker='o', label='sell order')
        plt.axhline(y=upper_price, color='purple', linestyle='dashed')
        plt.axhline(y=start_price, color='purple')
        plt.axhline(y=lower_price, color='purple', linestyle='dashed')
        plt.grid(True)
        plt.xlabel('Time')
        plt.ylabel('Price')
        plt.title(f'Current price: {prices[-1]:.2f} ({price_change_to_start_sign}{price_change_to_start:.1%})')
        plt.legend()
        plt.autoscale()  
        plt.draw()
        
        if show_fig:
            plt.pause(draw_delay)
        else:
            await asyncio.sleep(draw_delay)
        
        send_photo_timer += draw_delay
        if send_photo_timer >= send_photo_delay:
            file_name = 'prices.png'
            plt.savefig(file_name)
            await blogger.send_photo(
                file_name=file_name, 
                caption=f"{datetime.now().strftime('%F %T.%f')}\nOrders completed: {len(compl_orders)}"
                )
            send_photo_timer = 0
            
        plt.clf()    

    
if __name__ == '__main__':
    config = dotenv_values(".env")
    BOT_TOKEN = config['BOT_TOKEN']
    CHAT_ID = config['CHAT_ID']
    
    blogger = BloggerClient(bot_token=BOT_TOKEN, chat_id=CHAT_ID)
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(loop.create_task(main(blogger)))