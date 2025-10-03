import asyncio
import aiohttp
import json
from datetime import datetime
import pandas as pd

from decimal import Decimal, getcontext
getcontext().prec = 30

GEMINI_URL = 'https://api.gemini.com/v1/book/BTCUSD'
# DOC https://docs.gemini.com/rest/market-data#get-current-order-book
# The data has only 2 lists of bids and asks with each entry in (amount / price / timestamp) format
# All data is as string => use Decimal for highest precision without conversion losses
# Use this in the Python Console to get the results:
#   bid_df, ask_df = asyncio.run(probe())

async def probe() -> (pd.DataFrame, pd.DataFrame):
    """Returns bids and asks as DataFrame for analysis"""

    async with aiohttp.ClientSession() as session:
        async with session.get(GEMINI_URL, ssl=False, params={'limit_bids': 0, 'limit_asks': 0}) as response:
            try:
                data = await response.json()
                if response.status != 200:
                    raise Exception(f'Data fetching failed with status {response.status}')
                print('Data received!')
                bids: list = data.get('bids')
                asks: list = data.get('asks')
                bid_data = []
                ask_data = []
                for bid in bids:
                    entry = {}
                    entry['Price'] = Decimal(bid['price'])
                    entry['Qty'] = Decimal(bid['amount'])
                    entry['Timestamp'] = datetime.fromtimestamp(int(bid['timestamp']))
                    bid_data.append(entry)
                for ask in asks:
                    entry = {}
                    entry['Price'] = Decimal(ask['price'])
                    entry['Qty'] = Decimal(ask['amount'])
                    entry['Timestamp'] = datetime.fromtimestamp(int(ask['timestamp']))
                    ask_data.append(entry)
                return (pd.DataFrame(bid_data), pd.DataFrame(ask_data))
            except Exception as e:
                print(f'Error: {e}')
                return (pd.DataFrame(), pd.DataFrame())
