from config import (
    GMX_SUPPORTED_ASSETS_DICT,
    LONG_POSITION_HOURLY_FEE,
    LONG_TRADE_OPEN_FEE_AS_PER_POSITION,
    MIN_COLLATERAL_USDC,
    POSITIONS,
    SHORT_POSITION_HOURLY_FEE,
    SHORT_TRADE_OPEN_FEE_AS_PER_POSITION,
    NETWORK_FEE,
    CURRENT_PRICE_INFO,
    get_balance_usdc,
    get_positions,
    set_balance_usdc,
    set_total_transaction_fees,
    get_total_transaction_fees,
)
from log_type import Analysis


class TradingHelper:
    def __init__(self, on_order_success, on_order_error):
        self.on_order_success = on_order_success
        self.on_order_error = on_order_error

    def get_previous_tickers(self, asset: str, previous_tickers: int):
        global CURRENT_PRICE_INFO

        asset_tickers = [
            {
                "timestamp": ticker[asset]["timestamp"],
                "open": ticker[asset]["open"],
                "high": ticker[asset]["high"],
                "low": ticker[asset]["low"],
                "close": ticker[asset]["close"],
            }
            for ticker in CURRENT_PRICE_INFO[:previous_tickers]
            if asset in ticker
        ]
        return asset_tickers

    def get_open_positions(self):
        return get_positions()

    def get_usd_balance(self):
        return get_balance_usdc()

    def open_position(
        self,
        asset: str,
        long: bool,
        collateral_usd: float,
        leverage: float,
        slippage_percent: float = 0.03,
    ):
        try:
            balance_usdc = get_balance_usdc()
            ticker = self.get_previous_tickers(asset, 1)[0]
            asset_price = ticker["close"]

            # Check if collateral is less than min collateral
            if collateral_usd < MIN_COLLATERAL_USDC:
                raise Exception(f"Collateral {collateral_usd} is less than min collateral {MIN_COLLATERAL_USDC}")

            # Check if the asset exists in the supported assets dictionary
            if asset not in GMX_SUPPORTED_ASSETS_DICT:
                raise Exception(f"Asset {asset} not in GMX_SUPPORTED_ASSETS")

            asset_info = GMX_SUPPORTED_ASSETS_DICT[
                asset
            ]  # Get asset info from the dictionary

            if leverage > asset_info["max_leverage"] or leverage <= 0:
                raise Exception(
                    f"Leverage {leverage} should be between 0 and {asset_info['max_leverage']} for asset {asset}"
                )
            if collateral_usd <= 0:
                raise Exception(
                    f"Collateral {collateral_usd} is less than or equal to 0"
                )

            position_size_usd = collateral_usd * leverage
            if balance_usdc <= NETWORK_FEE:
                return None

            balance_usdc -= NETWORK_FEE
            tx_fee_percent = (
                LONG_TRADE_OPEN_FEE_AS_PER_POSITION
                if long
                else SHORT_TRADE_OPEN_FEE_AS_PER_POSITION
            )

            max_position_size = balance_usdc / (1 / leverage + tx_fee_percent)
            if max_position_size < position_size_usd:
                position_size_usd = max_position_size
            tx_fee = tx_fee_percent * position_size_usd

            balance_usdc -= tx_fee
            balance_usdc -= position_size_usd / leverage

            if max_position_size == position_size_usd:
                balance_usdc = 0

            set_total_transaction_fees(
                get_total_transaction_fees() + tx_fee + NETWORK_FEE
            )

            position_key = f"{asset}_{'long' if long else 'short'}"
            position = {
                "chain": "arbitrum",
                "index_token_symbol": asset,
                "collateral_token_symbol": "USDC",
                "start_token_symbol": "USDC",
                "is_long": long,
                "size_delta_usd": position_size_usd,
                "leverage": leverage,
                "slippage_percent": slippage_percent,
                "timestamp": ticker["timestamp"],
                "asset_price_at_open": asset_price,
                "fee": tx_fee + NETWORK_FEE,
            }

            if position_key in POSITIONS:
                existing_position = POSITIONS[position_key]

                existing_size = existing_position["size_delta_usd"]
                existing_leverage = existing_position["leverage"]
                existing_asset_price = existing_position["asset_price_at_open"]

                existing_collateral = existing_size / existing_leverage
                trade_collateral = position_size_usd / leverage

                existing_position["size_delta_usd"] += position_size_usd
                existing_position["leverage"] = (
                    existing_collateral * existing_leverage
                    + trade_collateral * leverage
                ) / (existing_collateral + trade_collateral)
                existing_position["asset_price_at_open"] = (
                    existing_size + position_size_usd
                ) / (
                    existing_size / existing_asset_price
                    + position_size_usd / asset_price
                )

            else:
                POSITIONS[position_key] = position

            set_balance_usdc(balance_usdc)
            Analysis(
                timestamp=ticker["timestamp"],
                success=True,
                message="Order Success",
                action="OPEN",
                sub_action="LONG" if long else "SHORT",
                balance_usd=self.get_usd_balance(),
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
                    for position in self.get_open_positions().values()
                ],
                asset_symbol=asset,
                asset_current_price=asset_price,
                position_size_usd=position_size_usd,
                leverage=leverage,
                transaction_fee=tx_fee,
            ).log()
            self.on_order_success()
            return position

        except Exception as e:
            Analysis(
                timestamp=ticker["timestamp"],
                success=False,
                message=str(e),
                action="OPEN",
                sub_action="LONG" if long else "SHORT",
                balance_usd=self.get_usd_balance(),
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
                    for position in self.get_open_positions().values()
                ],
                asset_symbol=asset,
                asset_current_price=asset_price,
                position_size_usd=collateral_usd * leverage,
                leverage=leverage,
                transaction_fee=0,
            ).log()
            self.on_order_error(e)

    def close_position(
        self,
        asset: str,
        long: bool,
        position_percent_to_close: float = 100,
        slippage_percent: float = 0.03,
    ):
        try:
            global CURRENT_PRICE_INFO
            balance_usdc = get_balance_usdc()
            ticker = self.get_previous_tickers(asset, 1)[0]
            current_price = ticker["close"]

            # Check if the asset exists in the supported assets dictionary
            if asset not in GMX_SUPPORTED_ASSETS_DICT:
                raise Exception(f"Asset {asset} not in GMX_SUPPORTED_ASSETS")
            if position_percent_to_close < 0 or position_percent_to_close > 100:
                raise Exception(
                    f"Position percent to close {position_percent_to_close} should be between 0 and 100"
                )

            positions = self.get_open_positions()

            position_key = f"{asset}_long" if long else f"{asset}_short"

            if position_key not in positions:
                raise ValueError(
                    f"Position for asset '{asset}' {'LONG' if long else 'SHORT'} not found in open positions."
                )

            position = positions[position_key]
            position_to_close = 0
            if long:
                # Logic for closing a long position
                if position_percent_to_close == 100:
                    position_to_close = position["size_delta_usd"]
                    initialBalance = position["size_delta_usd"] / position["leverage"]
                    finalProfit = (
                        current_price / position["asset_price_at_open"] - 1
                    ) * position["size_delta_usd"]
                    balance_usdc += initialBalance + finalProfit
                    del POSITIONS[position_key]
                else:
                    position_to_close = position["size_delta_usd"] * (
                        position_percent_to_close / 100
                    )
                    initialBalance = position["size_delta_usd"] / position["leverage"]
                    finalProfit = (
                        current_price / position["asset_price_at_open"] - 1
                    ) * position["size_delta_usd"]
                    balance_usdc += (position_percent_to_close / 100) * (
                        initialBalance + finalProfit
                    )
                    position["size_delta_usd"] -= position_to_close
            else:
                # Logic for closing a short position
                if position_percent_to_close == 100:
                    position_to_close = position["size_delta_usd"]
                    initialBalance = position["size_delta_usd"] / position["leverage"]
                    finalProfit = (
                        1 - current_price / position["asset_price_at_open"]
                    ) * position["size_delta_usd"]
                    balance_usdc += initialBalance + finalProfit
                    del POSITIONS[position_key]
                else:
                    position_to_close = position["size_delta_usd"] * (
                        position_percent_to_close / 100
                    )
                    initialBalance = position["size_delta_usd"] / position["leverage"]
                    finalProfit = (
                        1 - current_price / position["asset_price_at_open"]
                    ) * position["size_delta_usd"]
                    balance_usdc += (position_percent_to_close / 100) * (
                        initialBalance + finalProfit
                    )
                    position["size_delta_usd"] -= position_to_close

            tx_fee = get_total_transaction_fees()
            balance_usdc -= NETWORK_FEE
            set_total_transaction_fees(tx_fee + NETWORK_FEE)

            set_balance_usdc(balance_usdc)
            Analysis(
                timestamp=ticker["timestamp"],
                success=True,
                message="Order Success",
                action="CLOSE",
                sub_action="LONG" if long else "SHORT",
                balance_usd=self.get_usd_balance(),
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
                    for position in self.get_open_positions().values()
                ],
                asset_symbol=asset,
                asset_current_price=current_price,
                position_size_usd=position_to_close,
                leverage=position["leverage"],
                transaction_fee=NETWORK_FEE,
            ).log()
            self.on_order_success()
            return position

        except Exception as e:
            Analysis(
                timestamp=ticker["timestamp"],
                success=False,
                message=str(e),
                action="CLOSE",
                sub_action="LONG" if long else "SHORT",
                balance_usd=self.get_usd_balance(),
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
                    for position in self.get_open_positions().values()
                ],
                asset_symbol=asset,
                asset_current_price=current_price,
                # position_size_usd=position["size_delta_usd"] * (position_percent_to_close / 100),
                # leverage=position["leverage"],
                position_size_usd = position_percent_to_close,
                leverage = 1,
                transaction_fee=NETWORK_FEE,
            ).log()
            self.on_order_error(e)

    def close_all_positions(self):
        try:
            assets_of_open_positions = self.get_open_positions()
            positions_to_close = list(
                assets_of_open_positions.keys()
            )  # Create a list of keys

            for asset in positions_to_close:
                asset, is_long = asset.split("_")
                if is_long == "long":
                    self.close_position(asset, long=True, position_percent_to_close=100)
                else:
                    self.close_position(
                        asset, long=False, position_percent_to_close=100
                    )
        except Exception as e:
            pass

    def deduct_hourly_fee(self, hours: int):
        global POSITIONS
        positions = dict(self.get_open_positions())  # Create a copy for safe iteration
        for position in positions.values():
            fee_to_cut = 0
            if position["is_long"]:
                fee_to_cut += (
                    LONG_POSITION_HOURLY_FEE * hours * position["size_delta_usd"]
                )
            else:
                fee_to_cut += (
                    SHORT_POSITION_HOURLY_FEE * hours * position["size_delta_usd"]
                )
            position["size_delta_usd"] -= fee_to_cut
            set_total_transaction_fees(get_total_transaction_fees() + fee_to_cut)

            if position["size_delta_usd"] < 0:
                asset = position["index_token_symbol"]
                isLong = position["is_long"]
                position_key = f"{asset}_{'long' if isLong else 'short'}"
                del POSITIONS[position_key]
                Analysis(
                    timestamp=CURRENT_PRICE_INFO[0][asset]["timestamp"],
                    success=True,
                    message="Closed by Hourly Fees",
                    action="LIQUIDATION",
                    sub_action="LONG" if isLong else "SHORT",
                    balance_usd=self.get_usd_balance(),
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
                        for position in self.get_open_positions().values()
                    ],
                    asset_symbol=asset,
                    asset_current_price=CURRENT_PRICE_INFO[0][asset]["close"],
                    position_size_usd=position["size_delta_usd"],
                    leverage=position["leverage"],
                    transaction_fee=NETWORK_FEE,
                ).log()

    # need to revisit
    def check_for_liquidation(self):
        global POSITIONS, CURRENT_PRICE_INFO

        positions_to_liquidate = []
        positions_copy = dict(POSITIONS)  # Create a copy for safe iteration
        
        for position_key, position in positions_copy.items():
            asset = position["index_token_symbol"]
            current_price = CURRENT_PRICE_INFO[0][asset]["close"]
            is_long = position["is_long"]
            position_size_usd = position["size_delta_usd"]
            leverage = position["leverage"]
            at_risk = False

            # Calculate the liquidation price
            if is_long:
                liquidation_price = position["asset_price_at_open"] * (
                    1 - 1 / leverage - 1 / position_size_usd
                )
                at_risk = current_price <= liquidation_price
            else:
                liquidation_price = position["asset_price_at_open"] * (
                    1 + 1 / leverage - 1 / position_size_usd
                )
                at_risk = current_price >= liquidation_price

            if at_risk:
                Analysis(
                    timestamp=CURRENT_PRICE_INFO[0][asset]["timestamp"],
                    success=True,
                    message="Asset Liquidated",
                    action="LIQUIDATION",
                    sub_action="LONG" if is_long else "SHORT",
                    balance_usd=self.get_usd_balance(),
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
                        for position in self.get_open_positions().values()
                    ],
                    asset_symbol=asset,
                    asset_current_price=current_price,
                    position_size_usd=position_size_usd,
                    leverage=leverage,
                    transaction_fee=NETWORK_FEE,
                ).log()
                positions_to_liquidate.append(position_key)

        for position_key in positions_to_liquidate:
            del POSITIONS[position_key]  # Example: remove the position
