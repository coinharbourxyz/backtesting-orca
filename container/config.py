import os

################################ OS ENV VARIABLES ################################
INTERVAL_IN_SECONDS = int(os.getenv("INTERVAL", "604800"))

# ASSETS = os.getenv("ASSETS", "BTC,ETH").split(",")
ASSETS = os.getenv("ASSETS", "ETH,BTC").split(",")

# Backtest Input Parameters
start_time = os.getenv("START_TIME", "2017-01-01")
end_time = os.getenv("END_TIME", "2024-12-31")
initial_balance = float(os.getenv("INITIAL_BALANCE", "1000"))

################################ GLOBAL VARIABLES #########################

POSITIONS = {}
BALANCE_USDC: float = initial_balance  # CAN DEDUCT SWAP FEES LATER HERE
CURRENT_PRICE_INFO = []
CURRENT_TIMESTAMP = 0
TOTAL_TRANSACTION_FEES = 0

def get_positions():
    return POSITIONS

def set_positions(value):
    global POSITIONS
    POSITIONS = value

def get_balance_usdc():
    return BALANCE_USDC

def set_balance_usdc(value):
    global BALANCE_USDC
    BALANCE_USDC = value


def get_current_timestamp():
    return CURRENT_TIMESTAMP


def set_current_timestamp(value):
    global CURRENT_TIMESTAMP
    CURRENT_TIMESTAMP = value


def get_total_transaction_fees():
    return TOTAL_TRANSACTION_FEES


def set_total_transaction_fees(value):
    global TOTAL_TRANSACTION_FEES
    TOTAL_TRANSACTION_FEES = value


# FEE RATES AS PER 21-10-2024
SWAP_FEE = 0.15  # FLAT ONE TIME IN USD
NETWORK_FEE = 0.1  # PER TRADE FEE IN USD

LONG_POSITION_HOURLY_FEE = 0.000 / 100  # OF POSITION VALUE PER HOUR, 0.0042
SHORT_POSITION_HOURLY_FEE = 0.00 / 100  # OF POSITION VALUE PER HOUR, 0.0041

LONG_TRADE_OPEN_FEE_AS_PER_POSITION = 0.06 / 100  # OPEN FEE 0.07% OF POSITION VALUE
SHORT_TRADE_OPEN_FEE_AS_PER_POSITION = 0.06 / 100  # OPEN FEE 0.05% OF POSITION VALUE

################################ GMX ################################
MIN_COLLATERAL_USDC = 3
GMX_SUPPORTED_ASSETS = [  # As per 21-10-2024 via https://arbitrum-api.gmxinfra.io/tokens
    {
        "name": "APE",
        "start_date": "2022-03-18",
        "max_leverage": 50,
    },
    {
        "name": "ETH",
        "start_date": "2017-08-17",
        "max_leverage": 100,
    },
    {
        "name": "BTC",
        "start_date": "2017-08-17",
        "max_leverage": 100,
    },
    {
        "name": "DOGE",
        "start_date": "2019-07-06",
        "max_leverage": 100,
    },
    {
        "name": "EIGEN",
        "start_date": "2024-10-02",
        "max_leverage": 50,
    },
    {
        "name": "LTC",
        "start_date": "2017-12-20",
        "max_leverage": 100,
    },
    {
        "name": "SHIB",
        "start_date": "2021-05-11",
        "max_leverage": 50,
    },
    {
        "name": "SOL",
        "start_date": "2020-08-12",
        "max_leverage": 100,
    },
    {
        "name": "STX",
        "start_date": "2019-10-26",
        "max_leverage": 50,
    },
    {
        "name": "UNI",
        "start_date": "2020-09-18",
        "max_leverage": 60,
    },
    {
        "name": "LINK",
        "start_date": "2019-01-17",
        "max_leverage": 100,
    },
    {
        "name": "ARB",
        "start_date": "2023-03-24",
        "max_leverage": 75,
    },
    {
        "name": "XRP",
        "start_date": "2018-05-05",
        "max_leverage": 100,
    },
    {
        "name": "BNB",
        "start_date": "2017-11-07",
        "max_leverage": 100,
    },
    {
        "name": "ATOM",
        "start_date": "2019-04-30",
        "max_leverage": 60,
    },
    {
        "name": "NEAR",
        "start_date": "2020-10-15",
        "max_leverage": 50,
    },
    {
        "name": "AAVE",
        "start_date": "2020-10-16",
        "max_leverage": 50,
    },
    {
        "name": "AVAX",
        "start_date": "2020-09-23",
        "max_leverage": 60,
    },
    {
        "name": "OP",
        "start_date": "2022-06-02",
        "max_leverage": 50,
    },
    {
        "name": "ORDI",
        "start_date": "2023-11-08",
        "max_leverage": 50,
    },
    {
        "name": "GMX",
        "start_date": "2022-10-06",
        "max_leverage": 50,
    },
    {
        "name": "WIF",
        "start_date": "2024-03-06",
        "max_leverage": 50,
    },
    {
        "name": "PEPE",
        "start_date": "2023-05-06",
        "max_leverage": 50,
    },
    # {
    #     "name": "SATS", # Not on Binance for Live Trading
    #     "start_date": "2023-12-13",
    #     "max_leverage": 50,
    # },
    {
        "name": "POL",
        "start_date": "2024-09-14",
        "max_leverage": 50,
    },
]

# Convert GMX_SUPPORTED_ASSETS to a dictionary for fast lookup
GMX_SUPPORTED_ASSETS_DICT = {asset["name"]: asset for asset in GMX_SUPPORTED_ASSETS}
