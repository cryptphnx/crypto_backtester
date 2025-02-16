# live_api.py
import ccxt

class LiveTrader:
    def __init__(self, exchange_name='binance', api_key='', secret=''):
        exchange_class = getattr(ccxt, exchange_name)
        self.exchange = exchange_class({
            'apiKey': api_key,
            'secret': secret,
            'enableRateLimit': True,
        })

    def fetch_balance(self):
        return self.exchange.fetch_balance()

    def create_order(self, symbol, order_type, side, amount, price=None):
        if order_type == 'market':
            return self.exchange.create_market_order(symbol, side, amount)
        elif order_type == 'limit':
            return self.exchange.create_limit_order(symbol, side, amount, price)
        else:
            raise ValueError("Unsupported order type")

if __name__ == "__main__":
    trader = LiveTrader(api_key='YOUR_API_KEY', secret='YOUR_SECRET')
    print(trader.fetch_balance())
