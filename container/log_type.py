from dataclasses import dataclass, field
import json
from typing import Dict, Any, Optional


@dataclass
class Analysis:
    # Metadata
    identifier: Optional[str] = "Analysis"
    timestamp: Optional[int] = None
    action: Optional[str] = None
    sub_action: Optional[str] = None
    success: Optional[bool] = None
    message: Optional[str] = None

    # State Variables
    balance_usd: Optional[float] = None
    total_transaction_fees: Optional[float] = None
    open_positions: Dict[str, Dict[str, Any]] = field(
        default_factory=dict
    )  # No need to pass

    # Logs
    asset_symbol: Optional[str] = None
    asset_current_price: Optional[float] = None
    position_size_usd: Optional[float] = None
    leverage: Optional[float] = None
    transaction_fee: Optional[float] = None  # No need to pass

    def calculate_total_value(self):
        totalValue = self.balance_usd
        distribution = {}
        distribution["USD"] = self.balance_usd
        if self.open_positions is None:
            return totalValue, distribution

        for position in self.open_positions:
            token_value = 0
            if position["is_long"]:
                initialPrice = (
                    position["total_position_size"] / position["avg_leverage"]
                )
                profitIfClosed = (
                    position["token_current_price"]
                    / position["avg_price_at_trade_open"]
                    - 1
                ) * position["total_position_size"]
                token_value = initialPrice + profitIfClosed
                totalValue += token_value
            else:
                initialPrice = (
                    position["total_position_size"] / position["avg_leverage"]
                )
                profitIfClosed = (
                    1
                    - position["token_current_price"]
                    / position["avg_price_at_trade_open"]
                ) * position["total_position_size"]
                token_value = initialPrice + profitIfClosed
                totalValue += initialPrice + profitIfClosed

            if position["token"] in distribution:
                distribution[position["token"]] += token_value
            else:
                distribution[position["token"]] = token_value

        return totalValue, distribution

    def log(self):
        self.total_value, self.distribution = self.calculate_total_value()
        analysis_json = json.dumps(self.__dict__)
        print(analysis_json)
