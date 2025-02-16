# data.py
import requests
import pandas as pd
import dateparser

def get_historical_data(symbol='BTCUSDT', interval='5m', start_str='1 month ago UTC'):
    """
    Download historical kline (candlestick) data from Binance public API (no API key required).
    
    :param symbol: Trading pair, e.g., 'BTCUSDT'
    :param interval: Candle interval (e.g., '1m', '5m', '1h', '1d')
    :param start_str: Start time in natural language (e.g., '1 month ago UTC')
    :return: DataFrame with datetime index and OHLCV columns.
    """
    base_url = "https://api.binance.com/api/v3/klines"
    # Parse the start time using dateparser
    start_dt = dateparser.parse(start_str)
    start_ts = int(start_dt.timestamp() * 1000)
    
    data = []
    limit = 1000  # Maximum records per API call
    while True:
        params = {
            'symbol': symbol,
            'interval': interval,
            'startTime': start_ts,
            'limit': limit
        }
        response = requests.get(base_url, params=params)
        klines = response.json()
        if not klines:
            break
        data.extend(klines)
        last_open_time = klines[-1][0]
        if len(klines) < limit:
            break
        start_ts = last_open_time + 1  # move to next timestamp
    
    # Create a DataFrame from the downloaded data
    df = pd.DataFrame(data, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    
    # Convert timestamps and set proper dtypes
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df.set_index('open_time', inplace=True)
    df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    return df

if __name__ == "__main__":
    df = get_historical_data()
    print(df.head())
