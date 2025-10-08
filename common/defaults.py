import logging.config

logging.config.fileConfig(
    'log/logger.ini',
    disable_existing_loggers=False,
    defaults={'logfilename': 'log/last_run.log'}
)

# GEMINI_URL = 'https://api.gemini.com/v1/book/BTCUSD'
GEMINI_URL = 'https://api.gemini.com/v1/book/ETHUSD'
# COINBASE_URL = 'https://api.exchange.coinbase.com/products/BTC-USD/book?level=2'
COINBASE_URL = 'https://api.exchange.coinbase.com/products/ETH-USD/book?level=2'
QTY_DEFAULT = 10
TIMEOUT_SECONDS = 5
RATE_LIMIT_SECONDS = 2
GEMINI_DATA_LIMITS = 0  # Number of bids/asks to be returned. 0 for all
