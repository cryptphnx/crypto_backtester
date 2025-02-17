# data.py
import requests
import pandas as pd
import dateparser

def get_historical_data(symbol='BTCUSDT', interval='5m', start_str='1 month ago UTC'):
    # Public Binance endpoint approach
    base_url = "https://api.binance.com/api/v3/klines"
    start_dt = dateparser.parse(start_str)
    start_ts = int(start_dt.timestamp() * 1000)
    
    data = []
    limit = 1000
    while True:
        params = {
            'symbol': symbol,
            'interval': interval,
            'startTime': start_ts,
            'limit': limit
        }
        resp = requests.get(base_url, params=params)
        klines = resp.json()
        if not klines:
            break
        data.extend(klines)
        last_open_time = klines[-1][0]
        if len(klines) < limit:
            break
        start_ts = last_open_time + 1
    
    df = pd.DataFrame(data, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df.set_index('open_time', inplace=True)
    df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    return df
