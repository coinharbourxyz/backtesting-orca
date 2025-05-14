import signal
from config import (
    ASSETS,
    POSITIONS,
    CURRENT_PRICE_INFO,
    get_current_timestamp,
    get_total_transaction_fees,
)
from helpers import TradingHelper
from input import MyAlgorithm
from log_type import Analysis
from ticker import get_current_ticker, get_latest_start_time


class TradingAlgorithm:
    def __init__(self, global_vars=None):
        self.global_vars = global_vars if global_vars else {}
        self.running = False
        self.trading_helper = TradingHelper(
            self._on_order_success, self._on_order_error
        )
        self.my_algorithm = MyAlgorithm(self.trading_helper)
        self.previous_ticker = None
        self.nav_data = []
        self.last_nav_timestamp = None

    # def _setup_signals(self):
    #     signal.signal(signal.SIGTERM, self._handle_sigterm)
    #     signal.signal(signal.SIGINT, self._handle_sigterm)

    def _handle_sigterm(self, signum, frame):
        self.running = False
        self._on_algo_stop()

    def _on_algo_start(self):
        Analysis(
            timestamp=int(get_latest_start_time(ASSETS).timestamp()),
            success=True,
            message="Algorithm Started",
            action="START",
            sub_action="",
            balance_usd=self.trading_helper.get_usd_balance(),
            total_transaction_fees=0,
            open_positions=None,
            asset_symbol="",
            asset_current_price=None,
            position_size_usd=None,
            leverage=None,
            transaction_fee=get_total_transaction_fees(),
        ).log()
        self.my_algorithm.on_algo_start()

    def _on_algo_stop(self):
        """Stop the algorithm."""
        self.my_algorithm.on_algo_stop()
        self.trading_helper.close_all_positions()
        Analysis(
            timestamp=get_current_timestamp(),
            success=True,
            message="Algorithm Stopped",
            action="STOP",
            sub_action="",
            balance_usd=self.trading_helper.get_usd_balance(),
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

    def on_ticker_recd(self, ticker_data: dict):
        self.my_algorithm.on_ticker_recd(ticker_data)

    def _on_order_success(self):
        self.my_algorithm.on_order_success()

    def _on_order_error(self, error):
        self.my_algorithm.on_order_error(error)

    def _deduct_hourly_fee(self, hours: int):
        self.trading_helper.deduct_hourly_fee(hours)

    def run(self):
        # self._setup_signals()
        self.running = True
        self._on_algo_start()
        try:
            while self.running:
                current_ticker = get_current_ticker(assets=ASSETS)
                if self.previous_ticker:
                    hours_passed = (
                        current_ticker[ASSETS[0]]["timestamp"]
                        - self.previous_ticker[ASSETS[0]]["timestamp"]
                    ) / 3600
                    self._deduct_hourly_fee(hours_passed)
                    self.trading_helper.check_for_liquidation()
                self.previous_ticker = current_ticker

                current_timestamp = get_current_timestamp()
                if self.last_nav_timestamp == None:
                    self.last_nav_timestamp = current_timestamp - 604800

                while current_timestamp >= self.last_nav_timestamp + 604800:
                    current_value, _ = Analysis(
                        timestamp= current_timestamp,
                        balance_usd=self.trading_helper.get_usd_balance(),
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
                        ]
                    ).calculate_total_value()
                    # self.nav_data.append([current_timestamp, current_value])
                    self.nav_data.append(current_value)
                    self.last_nav_timestamp += 604800

                self.on_ticker_recd(current_ticker)
            return self.nav_data

        except (KeyboardInterrupt, SystemExit):
            self.running = False
            self._on_algo_stop()
            # print("NAV_DATA ", self.nav_data)
            return self.nav_data
