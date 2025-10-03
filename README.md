
# CoinRoutes Coding Assignment

We need to get aggregated order books from CoinBase 
and Gemini for BTC-USD. We aggregate the data either
up to 10 BTC, or up to a provided `qty` parameter.

## Quick Setup

Requires Python and pip. Tested with with 3.11 and 3.13.

```
git clone https://github.com/dr-boris/orderbook-aggregator.git
python3 -m venv .env
. .env/bin/activate
pip install -r requirements.txt
```

## Run

```commandline
python ob_aggregator.py
```
or
```commandline
python ob_aggregator.py --qty 100
```

### Notes

To simulate the rate limits between subsequent script executions, we automatically create a 
local file `rates.lock` containing a timestamp denoting when was the script executed last time.
You must wait until the rate-limit interval expires (2 seconds by default)
until you can run the script again.

Using a Redis cache, a dedicated rates-server or a global memory-map might be a better
solution to align between executions, and depending on use-case.

The configuration (timeouts, limits, ...) can be modified in `common/defaults.py`.

### Observations

Sometimes, for low volumes, the sell price is higher than buy! This is probably
due to discrepancy between different exchanges.
This indicates **arbitrage opportunities**.

## Probe

We needed to reverse-engineer and probe the data endpoints, so we create a `probe` package
which returns 2 data frames with all the data. The code has been iteratively modified until
all data is fully understood and extracted.

To probe the endpoints, go to python console and run the following commands and analyze the dataframes:

```
from probe.gemini_probe import *
bid_df, ask_df = asyncio.run(probe())
```
or
```
from probe.coinbase_probe import *
bid_df, ask_df = asyncio.run(probe())
```

## In-Depth Analysis

Before we implement the solution, we need to 
understand everything about the provided endpoints.

### Gemini Endpoint

We need to use `https://api.gemini.com/v1/book/BTCUSD`

The documentation can be found 
[online](https://docs.gemini.com/rest/market-data#get-current-order-book).

Data provides bids and asks as JSON arrays.
DataStructure (verified) is a JsonObject with `(price / amount / timestamp)` nodes.
All entries are as unrounded strings. They need to be converted to decimals without
loss of precision.

The endpoint return 50 entries only, unless `limit_bids` and `limit_asks` query parameter
are provided. We can set them to `0` to get all the data.

### Coinbase Endpoint

We need to use `https://api.exchange.coinbase.com/products/BTC-USD/book?level=2`

The documentation can be found 
[online](https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-book).

We use Level2, which is 'Full order book (aggregated) and auction info'.
The `Quantity` is already **aggregated**, so we don't need to multiply by `num_orders`.

Data provides bids and asks as JSON arrays.
DataStructure (reverse-engineered) is `(price / qty / num_orders)`.

#### Auction State

Should never occur, as BTC-USD is not supposed
to enter an auction state, unless a major outage
happens.

However, the data supports it. 
It can be `collection`, `opening`, `complete`,
or `False` if no auction is active at the moment.
These have affect whether new orders can be executed, 
or queued.

Here is an excerpt from the CoinBase doc:

- The **collection** state indicates the auction is currently accepting orders and cancellations within the book. During this state, orders do not match and the book may appear crossed in the market data feeds.
- The **opening** state indicates the book transitions towards full trading or limit only. During opening state any buy orders at or over the open price and any sell orders at or below the open price may cross during the opening phase. Matches in this stage are charged taker fees. Any new orders or cancels entered while in the opening phase get queued and processed when the market resumes trading.
- The **complete** state indicates the dissemination of opening trades is finishing, and immediately after that the book goes into the next mode (either full trading or limit only).

If we have an auction, it will be difficult
to calculate an aggregated price, so n this case
we just output the summary:

```
{
  "indicative_open_price": "333.99",
  "indicative_open_size": "0.193",
  "indicative_bid_price": "333.98",
  "indicative_bid_size": "4.39088265",
  "indicative_ask_price": "333.99",
  "indicative_ask_size": "25.23542881",
  "auction_status": "CAN_OPEN"
}
```

