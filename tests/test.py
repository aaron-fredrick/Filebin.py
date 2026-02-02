import requests
import json
import asyncio
from Filebin import API  # Assuming this is the correct library


async def main():
    async with API() as api:
        bin = await api.getBin("zlpiruayaav16ra2")
        f = await bin.uploadFile("t.py")
        print(f)

# Run the async main function
asyncio.run(main())
