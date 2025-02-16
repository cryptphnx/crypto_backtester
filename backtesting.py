# backtesting.py
import backtrader as bt
from data import get_historical_data
from strategy import PineStrategy

def run_backtest(symbol='BTCUSDT', timeframe='5m', start_str='1 month ago UTC', strategy_params={}):
    cerebro = bt.Cerebro(optreturn=False)
    cerebro.addstrategy(PineStrategy, **strategy_params)
    
    df = get_historical_data(symbol=symbol, interval=timeframe, start_str=start_str)
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    
    cerebro.broker.setcommission(commission=0.00055)  # 0.055%
    
    # Record initial portfolio value
    initial_value = cerebro.broker.getvalue()
    results = cerebro.run()
    final_value = cerebro.broker.getvalue()
    
    strat = results[0]
    trade_log = getattr(strat, 'trade_log', [])
    
    return initial_value, final_value, trade_log, cerebro

if __name__ == "__main__":
    init_val, final_val, trades, cerebro = run_backtest()
    print(f"Initial Portfolio Value: {init_val}")
    print(f"Final Portfolio Value: {final_val}")
    print("Trade Log:")
    for trade in trades:
        print(trade)
    cerebro.plot(style='candlestick')
