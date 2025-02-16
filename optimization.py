# optimization.py
import backtrader as bt
from data import get_historical_data
from strategy import PineStrategy

def run_optimization(symbol='BTCUSDT', timeframe='5m', start_str='1 month ago UTC'):
    # Default parameters for the strategy
    default_params = {
        'longTermFastLen': 50,
        'longTermSlowLen': 200,
        'shortTermFastLen': 10,
        'shortTermSlowLen': 20,
        'fixedStopLossPct': 0.01,
        'fixedTakeProfitPct': 0.02,
        'fixedTrailingPct': 0.01,
    }
    
    # Step sizes for optimization: these define "one step" below/above the default value.
    steps = {
        'longTermFastLen': 1,
        'longTermSlowLen': 1,
        'shortTermFastLen': 1,
        'shortTermSlowLen': 1,
        'fixedStopLossPct': 0.001,
        'fixedTakeProfitPct': 0.001,
        'fixedTrailingPct': 0.001,
    }
    
    # Build a parameter grid where each parameter takes three values: default - step, default, and default + step.
    param_grid = {}
    for key, default in default_params.items():
        step = steps[key]
        if isinstance(default, int):
            values = [default - step, default, default + step]
            # Ensure values are positive (for periods, etc.)
            values = [v if v > 0 else 1 for v in values]
        else:
            values = [default - step, default, default + step]
        param_grid[key] = values

    cerebro = bt.Cerebro(optreturn=False)
    # Set the strategy to be optimized using our generated parameter grid.
    cerebro.optstrategy(PineStrategy, **param_grid)
    
    # Download historical data.
    df = get_historical_data(symbol=symbol, interval=timeframe, start_str=start_str)
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    
    cerebro.broker.setcommission(commission=0.00055)  # 0.055%

    # Run optimization (set maxcpus=1 for determinism; you can increase if your machine allows)
    optimized_runs = cerebro.run(maxcpus=1)
    
    # Process optimization results to find the best run (by final portfolio value)
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
