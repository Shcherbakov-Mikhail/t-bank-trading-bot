import asyncio
import random
from datetime import datetime


async def post_order(order):
    await asyncio.sleep(0)
    print(f'Posted order: {order} at {datetime.now()}')
    return order
    
async def handler(order):
    await asyncio.sleep(order[2])
    print(f'Closed order: {order} at {datetime.now()}')

async def handle_strat_order(order):
    posted_order = await post_order(order)         
    handle = asyncio.create_task(handler(posted_order))
    await handle
    return order

async def monitor_tasks():
    
    strategies = [
            ('SBER', 1, 2),
        ]
    check_interval = 2
    tasks = [asyncio.create_task(handle_strat_order(order)) for order in strategies]
    time_check_task = asyncio.create_task(asyncio.sleep(check_interval))
    
    print(f'Started at {datetime.now()}')
    while tasks:
        done, _ = await asyncio.wait([time_check_task] + tasks, return_when=asyncio.FIRST_COMPLETED)
        
        if time_check_task in done:
            done.remove(time_check_task)
            # print(f'Checking time: {datetime.now()}')                
            if datetime.now().hour == 3 and datetime.now().minute == 0:
                print("It's time!")
                for t in tasks:
                    t.cancel()
                return
            else:
                time_check_task = asyncio.create_task(asyncio.sleep(check_interval))
                
        if len(done) > 1:
            # multiple orderes triggered during the check interval (how to handle them?)
            print(f'{len(done)=}')
            

        for task in done:
            result = await task
            tasks.remove(task)
            
            new_order = ('SBER', -result[1], result[2]+1)
            new_task = asyncio.create_task(handle_strat_order(new_order))
            tasks.append(new_task)


async def main():
    await monitor_tasks()
    
    
if __name__ == "__main__":
    asyncio.run(main())
