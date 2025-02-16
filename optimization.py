# optimization.py
import backtrader as bt
from data import get_historical_data
from strategy import PineStrategy

def run_optimization(symbol='BTCUSDT', timeframe='5m', start_str='1 month ago UTC'):
    # Define the parameter grid with the specified ranges:
    param_grid = {
        'longTermFastLen': [50 - 40, 50, 50 + 150],         # [10, 50, 200]
        'longTermSlowLen': [200 - 100, 200, 200 + 200],       # [100, 200, 400]
        'shortTermFastLen': [10 - 5, 10, 10 + 10],            # [5, 10, 20]
        'shortTermSlowLen': [20 - 5, 20, 20 + 10],            # [15, 20, 30]
        'fixedStopLossPct': [0.01 - 0.005, 0.01, 0.01 + 0.1],  # [0.005, 0.01, 0.11]
        'fixedTakeProfitPct': [0.02 - 0.005, 0.02, 0.02 + 0.1],# [0.015, 0.02, 0.12]
        'fixedTrailingPct': [0.01 - 0.005, 0.01, 0.01 + 0.1],  # [0.005, 0.01, 0.11]
    }

    cerebro = bt.Cerebro(optreturn=False)
    cerebro.optstrategy(PineStrategy, **param_grid)
    
    # Download historical data
    df = get_historical_data(symbol=symbol, interval=timeframe, start_str=start_str)
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    
    cerebro.broker.setcommission(commission=0.00055)  # 0.055% commission
    
    # Run optimization (using a single CPU for determinism; adjust maxcpus if needed)
    optimized_runs = cerebro.run(maxcpus=1)
    
    # Process optimization results: select the run with the highest final portfolio value.
    best_run = None
    best_value = -float('inf')
    for run in optimized_runs:
        strat = run[0]
        portfolio_value = strat.broker.getvalue()
        if portfolio_value > best_value:
            best_value = portfolio_value
            best_run = strat
    return best_value, best_run

if __name__ == "__main__":
    best_value, best_strategy = run_optimization()
    print(f"Best Portfolio Value: {best_value}")
