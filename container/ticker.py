import pandas as pd
import math
import msgspec
import datetime

from config import (
    ASSETS,
    GMX_SUPPORTED_ASSETS,
    INTERVAL_IN_SECONDS,
    POSITIONS,
    get_balance_usdc,
    set_current_timestamp,
    start_time,
    end_time,
    CURRENT_PRICE_INFO,
    get_total_transaction_fees,
)

from log_type import Analysis

# Paths to parquet and timestamp mapping JSON
PARQUET_PATH = "combined_data.parquet"
MAPPING_JSON_PATH = "timestamp_mapping.json"

# Global variables
current_index = 0
current_year = None

# Load the timestamp-to-row-index mapping from JSON using msgspec
with open(MAPPING_JSON_PATH, "rb") as f:
    # Decode the JSON file into a dictionary
    timestamp_mapping = msgspec.json.decode(f.read(), type=dict[str, int])


# Update start_time to be the latest start time of the assets passed
def get_latest_start_time(assets: list[str]):
    asset_start_times = [
        pd.to_datetime(asset["start_date"])
        for asset in GMX_SUPPORTED_ASSETS
        if asset["name"] in assets
    ]
    latest_start_time = max(asset_start_times) if asset_start_times else None
    return latest_start_time


# Load Parquet data and filter based on the timestamp range
def load_filtered_data(assets: list[str]):
    global start_time_dt
    latest_start_time = get_latest_start_time(assets)

    # Ensure both start_time and latest_start_time are Timestamps
    start_time_converted = pd.to_datetime(start_time)
    latest_start_time_converted = pd.to_datetime(latest_start_time)

    start_time_dt = max(start_time_converted, latest_start_time_converted)
    end_time_dt = pd.to_datetime(end_time)

    # Read only necessary columns if possible
    base_df = pd.read_parquet(
        PARQUET_PATH,
        columns=["timestamp"]
        + [
            f"{asset.lower()}_{col}"
            for asset in assets
            for col in ["open", "high", "low", "close", "volume", "quote_volume", "trades", "taker_buy_base_volume", "taker_buy_quote_volume"]
        ],
    )

    # Convert timestamp column once
    base_df["timestamp"] = pd.to_datetime(base_df["timestamp"], unit="s")

    # Use boolean indexing for filtering
    mask = (base_df["timestamp"] >= start_time_dt) & (
        base_df["timestamp"] <= end_time_dt
    )
    base_df = base_df.loc[mask].reset_index(drop=True)

    if base_df.empty:
        raise KeyboardInterrupt

    # Set timestamp as index for easier lookups
    base_df.set_index("timestamp", inplace=True)

    return base_df


base_df = load_filtered_data(ASSETS)
interval_td = pd.to_timedelta(INTERVAL_IN_SECONDS, unit="s")


# Update the fetch_candle_data function to use the filtered data
def fetch_candle_data(assets: list[str]):
    global current_index, base_df, interval_td, current_year

    if current_index >= len(base_df):
        raise KeyboardInterrupt

    # Get the current row data
    current_data = base_df.iloc[current_index]
    new_price_info = {}

    for asset in assets:
        if (
            math.isnan(current_data[f"{asset.lower()}_open"])
            or math.isnan(current_data[f"{asset.lower()}_high"])
            or math.isnan(current_data[f"{asset.lower()}_low"])
            or math.isnan(current_data[f"{asset.lower()}_close"])
            or math.isnan(current_data[f"{asset.lower()}_volume"])
            or math.isnan(current_data[f"{asset.lower()}_quote_volume"])
            or math.isnan(current_data[f"{asset.lower()}_trades"])
            or math.isnan(current_data[f"{asset.lower()}_taker_buy_base_volume"])
            or math.isnan(current_data[f"{asset.lower()}_taker_buy_quote_volume"])
        ):
            raise KeyboardInterrupt

        timestamp = int(base_df.index[current_index].timestamp())
        new_price_info[asset] = {
            "timestamp": timestamp,
            "open": (float(current_data[f"{asset.lower()}_open"])),
            "high": (float(current_data[f"{asset.lower()}_high"])),
            "low": (float(current_data[f"{asset.lower()}_low"])),
            "close": (float(current_data[f"{asset.lower()}_close"])),
            "volume": (float(current_data[f"{asset.lower()}_volume"])),
            "quote_volume": (float(current_data[f"{asset.lower()}_quote_volume"])),
            "trades": (int(current_data[f"{asset.lower()}_trades"])),
            "taker_buy_base_volume": (float(current_data[f"{asset.lower()}_taker_buy_base_volume"])),
            "taker_buy_quote_volume": (float(current_data[f"{asset.lower()}_taker_buy_quote_volume"])),
        }

    new_year = datetime.datetime.fromtimestamp(timestamp).year
    if current_year is None:
        current_year = new_year
    elif new_year != current_year:
        Analysis(
            timestamp=timestamp,
            success=True,
            message=f"Year changed to {new_year}",
            action="YEAR_CHANGE",
            sub_action=str(new_year),
            balance_usd=get_balance_usdc(),
            total_transaction_fees=get_total_transaction_fees(),
            open_positions=[
                {
                    "is_long": position["is_long"],
                    "token": position["index_token_symbol"],
                    "avg_leverage": position["leverage"],
                    "total_position_size": position["size_delta_usd"],
                    "token_current_price": CURRENT_PRICE_INFO[0][
                        position["index_token_symbol"]
                    ]["close"],
                    "avg_price_at_trade_open": position["asset_price_at_open"],
                }
                for position in POSITIONS.values()
            ],
            asset_symbol="",
            asset_current_price=None,
            position_size_usd=None,
            leverage=None,
            transaction_fee=None,
        ).log()
        current_year = new_year

    # Append the new price data to `current_price_info`
    CURRENT_PRICE_INFO.insert(0, new_price_info)
    set_current_timestamp(new_price_info[assets[0]]["timestamp"])

    # Calculate the next timestamp based on the interval
    next_timestamp = base_df.index[current_index] + interval_td

    # Use the mapping JSON to get the new index efficiently
    next_index = timestamp_mapping.get(str(next_timestamp.value))

    if next_index is not None:
        current_index = next_index
    else:
        # Find the next index based on the next_timestamp in base_df
        next_index_array = base_df.index.get_indexer([next_timestamp], method="bfill")
        if next_index_array.size > 0 and next_index_array[0] != -1:
            current_index = next_index_array[0]
        else:
            raise KeyboardInterrupt

    return CURRENT_PRICE_INFO


def get_current_ticker(assets: list[str] = None):
    if len(assets) == 0:
        assets = [asset["name"] for asset in GMX_SUPPORTED_ASSETS]

    try:
        ticker_data = fetch_candle_data(assets)[0]
        return ticker_data
    except KeyboardInterrupt:
        raise
