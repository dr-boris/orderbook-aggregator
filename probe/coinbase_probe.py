import asyncio
import aiohttp
import json
from datetime import datetime
import pandas as pd

COINBASE_URL = 'https://api.exchange.coinbase.com/products/BTC-USD/book?level=2'
# DOC https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-book
# Level2 - Full order book (aggregated) and auction info
# Quantity is already aggregated, no need to multiply by num_orders
# DataStructure is price / qty / num_orders
# Auction state is transmitted as well:
#   collection, opening, complete or 'False'
#   These have affect whether new orders can be executed, or queued
# Use this in the Python Console to get the results:
#   bid_df, ask_df = asyncio.run(probe())

async def probe_cb() -> (pd.DataFrame, pd.DataFrame):
    """Returns bids and asks as DataFrame for analysis"""

    async with aiohttp.ClientSession() as session:
        async with session.get(COINBASE_URL, ssl=False) as response:
            try:
                data = await response.json()
                if response.status != 200:
                    raise Exception(f'Data fetching failed with status {response.status}')
                print('Data received!')
                time: str = data.get('time')
                timestamp = datetime.fromisoformat(time) if time else None
                auction = data.get('auction')
                auction_mode = data.get('auction_mode')
                sequence = data.get('sequence', -1)
                print(f'timestamp: {timestamp}')
                print(f'auction: {auction}')
                print(f'auction_mode: {auction_mode}')
                print(f'sequence: {sequence}')
                if auction_mode:
                    print(data)
                    raise Exception('Auction mode is active!')
                bids: list = data.get('bids')
                asks: list = data.get('asks')
                bid_data = []
                ask_data = []
                for bid in bids:
                    entry = {}
                    entry['Price'] = bid[0]
                    entry['Qty'] = bid[1]
                    entry['NumOrders'] = bid[2]
                    bid_data.append(entry)
                for ask in asks:
                    entry = {}
                    entry['Price'] = ask[0]
                    entry['Qty'] = ask[1]
                    entry['NumOrders'] = ask[2]
                    ask_data.append(entry)
                # Warning: Final data is in string format, should be converted to Decimal
                return (pd.DataFrame(bid_data), pd.DataFrame(ask_data))
            except Exception as e:
                print(f'Error: {e}')
                return (pd.DataFrame(), pd.DataFrame())
