# Async/Async Operations
import asyncio
import omni.kit.app
import omni.client
from omni.kit.async_engine import run_coroutine


async def my_task():
	print(f"my task begin")

	# Wait few updates:
	for i in range(5):
		e = await omni.kit.app.get_app().next_update_async()
		print(f"{i}: {e}")

	# Native asyncio.sleep
	await asyncio.sleep(2)

	# Async List using Client Library
	LIST_PATH = "omniverse://ov-sandbox/Users/"
	(result, entries) = await omni.client.list_async(LIST_PATH)
	for e in entries:
		print(e)

	print(f"my task end")


# Start task
run_coroutine(my_task())
