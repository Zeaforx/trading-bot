import pandas as pd
from strategy.indicators import Indicators
from config.settings import settings


class LowRiskSwingStrategy:
    def __init__(self):
        self.indicators = Indicators()

    def calculate_indicators(self, data):
        """Calculate all required indicators"""
        df = data.copy()

        # OPTIMIZATION: Use EMA instead of SMA (Lag reduction)
        df["sma_short"] = self.indicators.ema(df, settings.SMA_SHORT)
        df["sma_long"] = self.indicators.ema(df, settings.SMA_LONG)
        # OPTIMIZATION: Volume SMA for Confirmation
        df["sma_volume"] = df["volume"].rolling(window=20).mean()

        df["rsi"] = self.indicators.rsi(df, settings.RSI_PERIOD)
        df["atr"] = self.indicators.atr(df)
        df["macd"], df["macd_signal"] = self.indicators.macd(df)

        # OPTIMIZATION: Add ADX for Regime Filter
        df["adx"] = self.indicators.adx(df, settings.ADX_PERIOD)

        return df

    def generate_signal(self, data):
        """
        Returns: (signal, score, reason, atr, debug_data)
        """
        df = self.calculate_indicators(data)
        latest = df.iloc[-1]
        prev = df.iloc[-2]

        signal = "HOLD"
        score = 0
        reasons = []

        # Regime Filter
        # ADX > Threshold = Trending. ADX < Threshold = Choppy/Range.
        is_trending = latest["adx"] > settings.ADX_THRESHOLD

        # 1. Trend Logic (EMA Crossover) - Only valid if Trending
        if is_trending:
            if (
                latest["sma_short"] > latest["sma_long"]
                and prev["sma_short"] <= prev["sma_long"]
                # OPTIMIZATION: Volume Confirmation
                and latest["volume"] > latest["sma_volume"]
            ):
                score += 3
                reasons.append("Bullish EMA crossover (Trend)")
            elif (
                latest["sma_short"] < latest["sma_long"]
                and prev["sma_short"] >= prev["sma_long"]
            ):
                score -= 3
                reasons.append("Bearish EMA crossover (Trend)")

        # 2. MACD (Momentum)
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

        # 3. RSI (Mean Reversion) - Only take Oversold buys if NOT in strong downtrend?
        # Actually, if ADX is High (Trending), RSI Overbought/Oversold can be fake (continue trending).
        # We reduce RSI weight if Trending, or reverse it?
        # Classic Mean Reversion: Trade RSI levels only when ADX is LOW (Range).

        if not is_trending:
            if latest["rsi"] < settings.RSI_OVERSOLD:
                score += 3  # Boost score for range-bound bounces
                reasons.append(f"RSI oversold in Range ({latest['rsi']:.1f})")
            elif latest["rsi"] > settings.RSI_OVERBOUGHT:
                score -= 3
                reasons.append(f"RSI overbought in Range ({latest['rsi']:.1f})")
        else:
            # If Trending, ignore Overbought (let it run) or buy dips?
            # For this simple strategy, we just ignore RSI reversals against the trend.
            pass

        # Determine signal
        if score >= 4:
            signal = "BUY"
        elif score <= -4:
            signal = "SELL"

        # NEW: Capture the exact values for the logs
        debug_data = {
            "Close Price": f"${latest['close']:.2f}",
            "RSI (14)": f"{latest['rsi']:.1f}",
            "ADX (14)": f"{latest['adx']:.1f} ({'Trend' if is_trending else 'Range'})",
            "EMA Short": f"${latest['sma_short']:.2f}",
            "EMA Long": f"${latest['sma_long']:.2f}",
            "MACD Line": f"{latest['macd']:.4f}",
            "ATR": f"{latest['atr']:.2f}",
        }

        # Return the new debug_data dictionary at the end
        return signal, score, "; ".join(reasons), latest["atr"], debug_data

        # return signal, score, "; ".join(reasons), latest["atr"]
