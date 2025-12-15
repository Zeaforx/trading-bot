import pandas as pd
from strategy.indicators import Indicators
from config.settings import settings


class LowRiskSwingStrategy:
    def __init__(self):
        self.indicators = Indicators()

    def calculate_indicators(self, data):
        """Calculate all required indicators"""
        df = data.copy()

        df["sma_short"] = self.indicators.sma(df, settings.SMA_SHORT)
        df["sma_long"] = self.indicators.sma(df, settings.SMA_LONG)
        df["rsi"] = self.indicators.rsi(df, settings.RSI_PERIOD)
        df["atr"] = self.indicators.atr(df)
        df["macd"], df["macd_signal"] = self.indicators.macd(df)

        return df

    def generate_signal(self, data):
        """
        Returns: (signal, score, reason, atr, debug_data)
        """
        df = self.calculate_indicators(data)
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        signal = 'HOLD'
        score = 0
        reasons = []

        # SMA Crossover
        if (
            latest["sma_short"] > latest["sma_long"]
            and prev["sma_short"] <= prev["sma_long"]
        ):
            score += 3
            reasons.append("Bullish SMA crossover")
        elif (
            latest["sma_short"] < latest["sma_long"]
            and prev["sma_short"] >= prev["sma_long"]
        ):
            score -= 3
            reasons.append("Bearish SMA crossover")

        # RSI
        if latest["rsi"] < settings.RSI_OVERSOLD:
            score += 2
            reasons.append(f"RSI oversold ({latest['rsi']:.1f})")
        elif latest["rsi"] > settings.RSI_OVERBOUGHT:
            score -= 2
            reasons.append(f"RSI overbought ({latest['rsi']:.1f})")

        # MACD
        if (
            latest["macd"] > latest["macd_signal"]
            and prev["macd"] <= prev["macd_signal"]
        ):
            score += 2
            reasons.append("MACD bullish cross")
        elif (
            latest["macd"] < latest["macd_signal"]
            and prev["macd"] >= prev["macd_signal"]
        ):
            score -= 2
            reasons.append("MACD bearish cross")

        # Determine signal
        if score >= 4:
            signal = "BUY"
        elif score <= -4:
            signal = "SELL"

        # NEW: Capture the exact values for the logs
        debug_data = {
            "Close Price": f"${latest['close']:.2f}",
            "RSI (14)":    f"{latest['rsi']:.1f}",
            "SMA Short":   f"${latest['sma_short']:.2f}",
            "SMA Long":    f"${latest['sma_long']:.2f}",
            "MACD Line":   f"{latest['macd']:.4f}",
            "ATR":         f"{latest['atr']:.2f}"
        }

        # Return the new debug_data dictionary at the end
        return signal, score, "; ".join(reasons), latest['atr'], debug_data

        # return signal, score, "; ".join(reasons), latest["atr"]
