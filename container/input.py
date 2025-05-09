from config import ASSETS


class MyAlgorithm:
    def __init__(self, trading_helper):
        self.prices = []
        self.trading_helper = trading_helper

    def on_ticker_recd(self, ticker_data):
        current_price = ticker_data["BTC"]["close"]
        self.prices.append(current_price)

        if len(self.prices) > 5:
            self.prices.pop(0)

        if len(self.prices) == 5:
            sma_5 = sum(self.prices) / 5
            balance = self.trading_helper.get_usd_balance()

            if balance > 0 and current_price > sma_5:
                self.trading_helper.open_position(
                    asset="BTC",
                    long=True,
                    collateral_usd=balance,
                    leverage=1,
                    slippage_percent=0.03,
                )
            else:
                if len(self.trading_helper.get_open_positions()) > 0:
                    self.trading_helper.close_position(
                        asset="BTC",
                        long=True,
                        position_percent_to_close=100,
                        slippage_percent=0.01,
                    )

    def on_algo_start(self):
        pass

    def on_algo_stop(self):
        pass

    def on_order_success(self):
        pass

    def on_order_error(self, error):
        pass
