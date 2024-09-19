import asyncio
import random

timers = [[2, 10], [3, 10], [6, 10], [6, 10]]

id = random.randint(13, 78)
async def init_async_fetch():
    async def run(duration):
        await asyncio.sleep(duration)

    print(f"ID: {id} working on {timers}")
    await asyncio.gather(*[run(duration) for duration in timers])

loop = asyncio.get_event_loop()
try:
    print(f'ID: {id} loop running')
    loop.run_until_complete(init_async_fetch())
except Exception as e:
    raise e
finally:
    loop.close()
# print([link for link in duration])
# time.sleep(duration)