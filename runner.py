import ccxt
import pandas as pd
import numpy as np
import talib
import time

class CryptoTrader:
    def __init__(self, api_key, api_secret):
        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True
        })

    def fetch_ohlcv(self, symbol, timeframe, limit):
        ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df

    def calculate_indicators(self, df):
        df['SMA_50'] = talib.SMA(df['close'], timeperiod=50)
        df['SMA_200'] = talib.SMA(df['close'], timeperiod=200)
        df['RSI'] = talib.RSI(df['close'], timeperiod=14)
        return df

    def generate_signals(self, df):
        df['signal'] = 0
        df.loc[(df['SMA_50'] > df['SMA_200']) & (df['RSI'] < 30), 'signal'] = 1
        df.loc[(df['SMA_50'] < df['SMA_200']) & (df['RSI'] > 70), 'signal'] = -1
        return df

    def backtest(self, df):
        df['position'] = df['signal'].shift(1)
        df['returns'] = df['close'].pct_change()
        df['strategy_returns'] = df['position'] * df['returns']
        return df['strategy_returns'].cumsum().fillna(0)

    def execute_trade(self, symbol, amount, side):
        try:
            order = self.exchange.create_market_order(symbol=symbol, type='market', side=side, amount=amount)
            return order
        except Exception as e:
            print(f"Error executing trade: {e}")
            return None

    def run_strategy(self, symbol, timeframe, limit, amount):
        data = self.fetch_ohlcv(symbol, timeframe, limit)
        data = self.calculate_indicators(data)
        data = self.generate_signals(data)
        pnl = self.backtest(data)

        last_signal = data['signal'].iloc[-1]
        if last_signal == 1:
            self.execute_trade(symbol, amount, 'buy')
        elif last_signal == -1:
            self.execute_trade(symbol, amount, 'sell')

        return pnl.iloc[-1]

# Example usage
if __name__ == "__main__":
    api_key = 'your_api_key'
    api_secret = 'your_api_secret'
    trader = CryptoTrader(api_key, api_secret)

    symbol = 'BTC/USDT'
    timeframe = '1h'
    limit = 100
    amount = 0.01  # BTC amount to trade

    pnl = trader.run_strategy(symbol, timeframe, limit, amount)
    print(f"Final PnL: {pnl}")
