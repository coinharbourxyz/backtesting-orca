import pandas as pd
import os
import json
import gc

def process_crypto_data(output_dir="./"):
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    parquet_file_path = os.path.join(output_dir, "combined_data.parquet")
    mapping_file_path = os.path.join(output_dir, "timestamp_mapping.json")

    # Define asset paths
    assets_and_paths = {
        "ape": "/home/shubham/Downloads/APEUSDT.csv",
        "doge": "/home/shubham/Downloads/DOGEUSDT.csv",
        "eigen": "/home/shubham/Downloads/EIGENUSDT.csv",
        "ltc": "/home/shubham/Downloads/LTCUSDT.csv",
        "shib": "/home/shubham/Downloads/SHIBUSDT.csv",
        "sol": "/home/shubham/Downloads/SOLUSDT.csv",
        "stx": "/home/shubham/Downloads/STXUSDT.csv",
        "uni": "/home/shubham/Downloads/UNIUSDT.csv",
        "link": "/home/shubham/Downloads/LINKUSDT.csv",
        "arb": "/home/shubham/Downloads/ARBUSDT.csv",
        "xrp": "/home/shubham/Downloads/XRPUSDT.csv",
        "bnb": "/home/shubham/Downloads/BNBUSDT.csv",
        "atom": "/home/shubham/Downloads/ATOMUSDT.csv",
        "near": "/home/shubham/Downloads/NEARUSDT.csv",
        "aave": "/home/shubham/Downloads/AAVEUSDT.csv",
        "avax": "/home/shubham/Downloads/AVAXUSDT.csv",
        "op": "/home/shubham/Downloads/OPUSDT.csv",
        "ordi": "/home/shubham/Downloads/ORDIUSDT.csv",
        "gmx": "/home/shubham/Downloads/GMXUSDT.csv",
        "wif": "/home/shubham/Downloads/WIFUSDT.csv",
        "pepe": "/home/shubham/Downloads/PEPEUSDT.csv",
        "sats": "/home/shubham/Downloads/1000SATSUSDT.csv",
        "pol": "/home/shubham/Downloads/POLUSDT.csv",
        "eth": "/home/shubham/Downloads/ETHUSDT.csv",
        "btc": "/home/shubham/Downloads/BTCUSDT.csv",
    }

    combined_df = None
    timestamp_mapping = {}

    print("Processing files...")
    for asset, file_path in assets_and_paths.items():
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}. Skipping...")
            continue

        print(f"Processing {asset}...")
        
        # Process file in chunks
        chunk = pd.read_csv(
            file_path,
            delimiter='|',
            header=None,
            usecols=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            names=['timestamp', 'open', 'high', 'low', 'close', 'volume',
                  'taker_buy_quote_volume', 'taker_buy_base_volume',
                  'quote_volume', 'trades'],
            dtype={'timestamp': 'int64', 'open': 'float32', 'high': 'float32',
                  'low': 'float32', 'close': 'float32', 'volume': 'float32',
                  'taker_buy_quote_volume': 'float32',
                  'taker_buy_base_volume': 'float32',
                  'quote_volume': 'float32', 'trades': 'int32'},
        )

        # Rename columns with asset prefix
        chunk.rename(columns={
            'open': f'{asset}_open',
            'high': f'{asset}_high',
            'low': f'{asset}_low',
            'close': f'{asset}_close',
            'volume': f'{asset}_volume',
            'quote_volume': f'{asset}_quote_volume',
            'trades': f'{asset}_trades',
            'taker_buy_base_volume': f'{asset}_taker_buy_base_volume',
            'taker_buy_quote_volume': f'{asset}_taker_buy_quote_volume'
        }, inplace=True)

        # Base the timestamps to minute level ie hardcode the seconds to 00
        chunk['timestamp'] = chunk['timestamp'].apply(lambda x: x - x % 60)

        # Merge with existing data
        if combined_df is None:
            combined_df = chunk
        else:
            combined_df = pd.merge(combined_df, chunk, on='timestamp', how='outer')

        # Sort and remove duplicates to keep memory usage down
        combined_df = combined_df.sort_values('timestamp').drop_duplicates(subset=['timestamp'])
        
        # Force garbage collection
        gc.collect()

        print(f"Processed {asset}: {combined_df.shape if combined_df is not None else 'No data'}")

    if combined_df is not None:
        # Convert timestamp to datetime
        combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'], unit='s')
        
        # Save to parquet
        print("Saving to Parquet...")
        combined_df.to_parquet(parquet_file_path, index=False)
        print(f"Saved to {parquet_file_path}")

        # Generate timestamp mapping
        print("Generating timestamp mapping...")
        timestamp_mapping = {str(int(ts.timestamp())): idx for idx, ts in enumerate(combined_df['timestamp'])}

        # Save mapping
        with open(mapping_file_path, 'w') as f:
            json.dump(timestamp_mapping, f, indent=4)
        print(f"Mapping saved to {mapping_file_path}")

        # Clear memory
        del combined_df
        gc.collect()

    print("Processing complete!")

if __name__ == "__main__":
    process_crypto_data()