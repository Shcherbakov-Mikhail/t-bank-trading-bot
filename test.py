import asyncio
import random
from datetime import datetime


async def post_order(order):
    await asyncio.sleep(order[2])
    print(f'Posted order: {order} at {datetime.now()}')
    return order
    
async def handler(order):
    await asyncio.sleep(5)
    print(f'Closed order: {order} at {datetime.now()}')

async def handle_strat_order(order):
    posted_order = await post_order(order)         
    handle = asyncio.create_task(handler(posted_order))
    await handle
    return order

async def monitor_tasks():
    
    strategies = [
            ('SBER', 1, 2),
            ('SBER', 2, 50),
        ]
    tasks = [asyncio.create_task(handle_strat_order(order)) for order in strategies]
    
    # TODO: add stop loss
    # check_interval = 2
    # time_check_task = asyncio.create_task(asyncio.sleep(check_interval))
    # if completed_task.done():
    #             print(f'Checking time: {datetime.now()}')
    #             current_time = datetime.now()
    #             if current_time.hour == 1 and current_time.minute == 11:
    #                 print("It's time!")
    #                 for task in tasks:
    #                     task.cancel()
    #                 return
    
    print(f'Started at {datetime.now()}')
    while tasks:

        for completed_task in asyncio.as_completed(tasks):

            result = await completed_task
            print(result)
            
            for task in tasks:
                if task.done() and task.result() == result:
                    tasks.remove(task)
                
            if result == ('SBER', 1, 2):
                new_order = ('SBER', 3, 6)
                print(f'Posting {new_order}')
                new_task = asyncio.create_task(handle_strat_order(new_order))
                tasks.append(new_task)
                
        # await asyncio.sleep(0.1)


async def main():
    await monitor_tasks()
    
    
if __name__ == "__main__":
    asyncio.run(main())
