import pandas as pd
import numpy as np


class Indicators:
    @staticmethod
    def sma(data, period):
        """Simple Moving Average"""
        return data["close"].rolling(window=period).mean()

    @staticmethod
    def ema(data, period):
        """Exponential Moving Average"""
        return data["close"].ewm(span=period, adjust=False).mean()

    @staticmethod
    def rsi(data, period=14):
        """Relative Strength Index"""
        delta = data["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def atr(data, period=14):
        """Average True Range"""
        high_low = data["high"] - data["low"]
        high_close = np.abs(data["high"] - data["close"].shift())
        low_close = np.abs(data["low"] - data["close"].shift())

        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        return true_range.rolling(period).mean()

    @staticmethod
    def macd(data, fast=12, slow=26, signal=9):
        """MACD Indicator"""
        ema_fast = data["close"].ewm(span=fast).mean()
        ema_slow = data["close"].ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        return macd_line, signal_line

    @staticmethod
    def adx(data, period=14):
        """Average Directional Index"""
        high = data["high"]
        low = data["low"]
        close = data["close"]

        # 1. Calculate +DM and -DM
        # UpMove = High - PrevHigh
        # DownMove = PrevLow - Low
        up = high - high.shift(1)
        down = low.shift(1) - low

        plus_dm = np.where((up > down) & (up > 0), up, 0.0)
        minus_dm = np.where((down > up) & (down > 0), down, 0.0)

        plus_dm = pd.Series(plus_dm, index=data.index)
        minus_dm = pd.Series(minus_dm, index=data.index)

        # 2. True Range (same as ATR logic)
        high_low = high - low
        high_close = np.abs(high - close.shift(1))
        low_close = np.abs(low - close.shift(1))
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

        # 3. Smooth with Wilder's Smoothing (alpha=1/period) or EMA
        # Using EWM for efficiency: span=period approximates general smoothing,
        # but Wilder's uses alpha=1/n. We'll use standard EMA for simplicity.
        tr_smooth = tr.ewm(alpha=1 / period, adjust=False).mean()
        plus_dm_smooth = plus_dm.ewm(alpha=1 / period, adjust=False).mean()
        minus_dm_smooth = minus_dm.ewm(alpha=1 / period, adjust=False).mean()

        # 4. Calculate +DI and -DI
        plus_di = 100 * (plus_dm_smooth / tr_smooth)
        minus_di = 100 * (minus_dm_smooth / tr_smooth)

        # 5. Calculate DX and ADX
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.ewm(alpha=1 / period, adjust=False).mean()

        return adx
