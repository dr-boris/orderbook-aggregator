import argparse
import aiohttp
import asyncio
from datetime import datetime
from decimal import Decimal, getcontext
import functools
from pathlib import Path

from common.defaults import *


# Script specific settings
log = logging.getLogger('aggregator')
getcontext().prec = 30
DECIMAL_ZERO = Decimal(0)
RATES_FILE = './rates.lock'


async def get_coinbase_data() -> (list[list], list[list]):
    """Returns positionally encoded arrays of [[price, quantity], ...]"""
    async with aiohttp.ClientSession() as session:
        async with session.get(COINBASE_URL, timeout=TIMEOUT_SECONDS, ssl=False) as response:
            try:
                data = await response.json()
                if response.status != 200:
                    raise Exception(f'Got responsestatus {response.status}')
                log.info('Coinbase data received')
                auction_mode = data.get('auction_mode')
                if auction_mode:
                    log.warning(data)
                    raise Exception('Auction mode is active!')
                # list of lists with [price, qty, num_orders]
                bids = data.get('bids')
                asks = data.get('asks')
                bids = [ [Decimal(x),Decimal(y)] for x,y,z in bids ]
                asks = [ [Decimal(x),Decimal(y)] for x,y,z in asks ]
                validate(bids, asks, 'Coinbase')
                return bids, asks
            except Exception as e:
                log.error(f'Coinbase fetch failed: {e}')
                return [], []


async def get_gemini_data():
    """Returns positionally encoded arrays of [[price, quantity], ...]"""
    async with aiohttp.ClientSession() as session:
        async with session.get(GEMINI_URL, timeout=TIMEOUT_SECONDS, ssl=False, params={'limit_bids': 0, 'limit_asks': 0}) as response:
            try:
                data = await response.json()
                if response.status != 200:
                    raise Exception(f'Got responsestatus {response.status}')
                log.info('Gemini data received')
                # list of dict with {price, amount, timestamp} as keys
                bids = data.get('bids')
                asks = data.get('asks')
                bids = [ [Decimal(bid['price']), Decimal(bid['amount'])] for bid in bids ]
                asks = [ [Decimal(ask['price']), Decimal(ask['amount'])] for ask in asks ]
                validate(bids, asks, 'Gemini')
                return bids, asks
            except Exception as e:
                log.error(f'Gamini fetch failed: {e}')
                return [], []


def validate(bids: list, asks: list, specifier: str):
    if len(bids) == 0:
        raise Exception(f'No bids received from {specifier}!')
    if len(asks) == 0:
        raise Exception(f'No asks received from {specifier}!')


def calculate_price_inorder(data: list[list], qty: Decimal) -> Decimal:
    """Traverses the data in-order and calculates the total price

    There are multiple assumptions necessary:
      - data needs to contain a list of [price, quantity] pairs.
      - qty needs to be positive!
    """
    to_cover = qty  # How much quantity is left 'to cover'
    acc_price = Decimal(0)  # Current aggregated price
    pos = 0
    size = len(data)
    while pos < size:
        price = data[pos][0]
        q = data[pos][1]
        if q < to_cover:
            acc_price += price * q
            to_cover -= q
            pos += 1
        else:
            acc_price += price * to_cover
            return acc_price
    raise Exception(f'Desired quantity of {qty} BTC can not be achieved!')


def RateLimit(func):
    """The Rate Limit decorator wraps the execution around a time-check.

    A file is used to track elapsed time between subsequent successful executions.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        rates_file = Path(RATES_FILE)
        if rates_file.exists():
            with open(rates_file, "r", encoding="utf-8") as f:
                timestamp = f.readline().strip()
            prev = datetime.fromtimestamp(float(timestamp))
            now = datetime.now()
            if (now - prev).seconds < RATE_LIMIT_SECONDS:
                print(f'Rate-limit enforced: subsequent executions allowed every {RATE_LIMIT_SECONDS} seconds')
                return 1
        result = await func(*args, **kwargs)
        if result == 0:
            with open(rates_file, "w", encoding="utf-8") as f:
                f.write(str(datetime.now().timestamp()))
        return result
    return wrapper


@RateLimit
async def main(qty: Decimal = Decimal(QTY_DEFAULT)):
    log.info(f'Starting Order Book Aggregator for {qty} BTC')
    bid_price = None
    ask_price = None
    try:
        data_coinbase, data_gemini = await asyncio.gather(get_coinbase_data(), get_gemini_data())
        # Merge data from exchanges
        bids = data_coinbase[0] + data_gemini[0]
        asks = data_coinbase[1] + data_gemini[1]
        # Sort all data
        bids.sort(key=lambda x: x[0], reverse=True)
        asks.sort(key=lambda x: x[0])
        # Calculate prices
        bid_price = calculate_price_inorder(bids, qty)
        ask_price = calculate_price_inorder(asks, qty)
        log.info('Calculation finished')
    except asyncio.TimeoutError:
        log.error(f'Request timeout after {TIMEOUT_SECONDS} seconds')
        return 1
    except Exception as e:
        log.error(f'Data Aggregation failed: {e}')
        return 1
    print(f'To buy {qty} BTC: ${ask_price:,.2f}')
    print(f'To sell {qty} BTC: ${bid_price:,.2f}')
    return 0


def get_decimal_or_exit(qty):
    try:
        qty = Decimal(qty)
        if qty < DECIMAL_ZERO:
            print(f'Provided --qty ({qty}) is negative!')
            exit(1)
        return qty
    except Exception:
        print(f'Provided --qty ({qty}) is not a number!')
        exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Order Book Aggregator')
    parser.add_argument('--qty', help='Specify quantity of BTC, e.g. 20', required=False)
    parser.parse_args()
    args = parser.parse_args()
    if args.qty is None:
        asyncio.run(main())
    else:
        qty = get_decimal_or_exit(args.qty)
        asyncio.run(main(qty))
